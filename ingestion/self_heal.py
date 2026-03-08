#!/usr/bin/env python3
"""
CheapHouse — Self-Healing Scraper Engine
Automatically diagnoses and fixes broken scrapers using Ollama LLM.
"""

import json
import logging
import os
import re
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

log = logging.getLogger("self_heal")

SCRIPT_DIR = Path(__file__).parent
HEAL_LOG_DIR = SCRIPT_DIR / "logs" / "healing"
HEAL_LOG_DIR.mkdir(parents=True, exist_ok=True)

MAX_FIX_ATTEMPTS = 3
DISABLED_COOLDOWN_HOURS = 72  # 3 days


class ScrapeResult:
    """Result from a scrape attempt."""
    def __init__(self, slug: str, success: bool, listings_found: int = 0,
                 error: str = "", error_type: str = ""):
        self.slug = slug
        self.success = success
        self.listings_found = listings_found
        self.error = error
        self.error_type = error_type


class HealingEngine:
    """
    Self-healing engine for scrapers.
    Uses Ollama to diagnose failures and generate fixes.
    """

    def __init__(self):
        self.state_file = SCRIPT_DIR / "heal_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                pass
        return {"sources": {}, "last_run": None}

    def _save_state(self):
        self.state["last_run"] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(self.state, indent=2, default=str))

    def _get_source_state(self, slug: str) -> dict:
        if slug not in self.state["sources"]:
            self.state["sources"][slug] = {
                "fix_attempts": 0,
                "last_fix_attempt": None,
                "disabled": False,
                "disabled_at": None,
                "last_error": None,
                "fixes_applied": [],
            }
        return self.state["sources"][slug]

    # ── Detection ─────────────────────────────────────────

    def check_results(self, results: list[ScrapeResult]) -> list[ScrapeResult]:
        """Check scrape results and return sources that need healing."""
        needs_healing = []

        for r in results:
            src_state = self._get_source_state(r.slug)

            # Skip disabled sources unless cooldown expired
            if src_state["disabled"]:
                if src_state["disabled_at"]:
                    disabled_at = datetime.fromisoformat(src_state["disabled_at"])
                    if datetime.now() - disabled_at < timedelta(hours=DISABLED_COOLDOWN_HOURS):
                        log.info(f"  {r.slug}: disabled (cooldown until "
                                 f"{disabled_at + timedelta(hours=DISABLED_COOLDOWN_HOURS)})")
                        continue
                log.info(f"  {r.slug}: cooldown expired, re-enabling")
                src_state["disabled"] = False
                src_state["fix_attempts"] = 0

            if not r.success or r.listings_found == 0:
                log.warning(f"  {r.slug}: NEEDS HEALING — "
                            f"success={r.success}, listings={r.listings_found}, "
                            f"error={r.error[:100]}")
                needs_healing.append(r)
                src_state["last_error"] = r.error[:500]
            else:
                # Reset fix attempts on success
                if src_state["fix_attempts"] > 0:
                    log.info(f"  {r.slug}: recovered! Resetting fix attempts.")
                    src_state["fix_attempts"] = 0

        self._save_state()
        return needs_healing

    # ── Diagnosis ─────────────────────────────────────────

    def diagnose(self, result: ScrapeResult) -> dict:
        """Diagnose why a scraper failed."""
        slug = result.slug
        log.info(f"  Diagnosing {slug}...")

        diagnosis = {
            "slug": slug,
            "problem": "unknown",
            "details": "",
            "live_html_sample": "",
            "adapter_code": "",
            "suggestion": "",
        }

        # 1. Read adapter source code
        adapter_path = self._find_adapter_file(slug)
        if adapter_path:
            diagnosis["adapter_code"] = adapter_path.read_text()[:5000]
        else:
            diagnosis["problem"] = "adapter_not_found"
            diagnosis["details"] = f"No adapter file found for slug '{slug}'"
            return diagnosis

        # 2. Fetch live HTML from the site
        live_html = self._fetch_live_html(slug)
        if live_html is None:
            diagnosis["problem"] = "site_unreachable"
            diagnosis["details"] = "Could not fetch the site. May be down or blocking."
            return diagnosis
        diagnosis["live_html_sample"] = live_html[:3000]

        # 3. Classify the error
        error = result.error.lower()
        if "timeout" in error or "timed out" in error:
            diagnosis["problem"] = "timeout"
        elif "403" in error or "forbidden" in error or "blocked" in error:
            diagnosis["problem"] = "blocked"
        elif "404" in error or "not found" in error:
            diagnosis["problem"] = "url_changed"
        elif "no listings" in error or result.listings_found == 0:
            diagnosis["problem"] = "selectors_broken"
        elif "int()" in error or "ValueError" in error or "parse" in error:
            diagnosis["problem"] = "parsing_error"
        else:
            diagnosis["problem"] = "unknown_crash"

        # 4. LLM analysis
        diagnosis["suggestion"] = self._llm_diagnose(diagnosis)

        return diagnosis

    def _find_adapter_file(self, slug: str) -> Optional[Path]:
        """Find the Python file for an adapter by slug."""
        for adapter_dir in [
            SCRIPT_DIR / "adapters",
            SCRIPT_DIR / "adapters" / "europe",
            SCRIPT_DIR / "adapters" / "usa",
            SCRIPT_DIR / "adapters" / "nz",
        ]:
            if not adapter_dir.exists():
                continue
            for py_file in adapter_dir.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                try:
                    content = py_file.read_text()
                    if f'"{slug}"' in content or f"'{slug}'" in content:
                        return py_file
                except Exception:
                    continue
        return None

    def _fetch_live_html(self, slug: str) -> Optional[str]:
        """Fetch current HTML from the source site."""
        try:
            from ingestion.adapters import get_adapter
            adapter_cls = get_adapter(slug)
            if adapter_cls is None:
                return None
            adapter = adapter_cls() if isinstance(adapter_cls, type) else adapter_cls

            url = (getattr(adapter, 'SEARCH_URL', None)
                   or getattr(adapter, 'search_url', None)
                   or getattr(adapter, 'base_url', None)
                   or getattr(adapter, 'BASE_URL', None))
            if not url:
                return None

            headers = getattr(adapter, 'HEADERS', {})
            if isinstance(headers, property):
                headers = {}
            headers.setdefault('User-Agent',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

            resp = requests.get(url, headers=headers, timeout=30)
            return resp.text
        except Exception as e:
            log.error(f"  Could not fetch live HTML for {slug}: {e}")
            return None

    def _llm_diagnose(self, diagnosis: dict) -> str:
        """Use Ollama to analyze the problem."""
        try:
            from ingestion.llm_client import llm_chat

            system = "You are a web scraper debugger. Analyze the broken scraper and suggest a fix."
            user = f"""PROBLEM TYPE: {diagnosis['problem']}

ADAPTER CODE (first 2500 chars):
```python
{diagnosis['adapter_code'][:2500]}
```

LIVE HTML FROM SITE (first 1500 chars):
```html
{diagnosis['live_html_sample'][:1500]}
```

Analyze:
1. What changed on the website?
2. What CSS selectors or URL patterns need updating?
3. Provide the fix.

Format:
DIAGNOSIS: [one line]
FIX_TYPE: [selectors|url|headers|parser|skip]
OLD_CODE: [broken line]
NEW_CODE: [fixed line]"""

            response = llm_chat(system, user, temperature=0.1, max_tokens=2000, json_mode=False)
            return response
        except Exception as e:
            log.error(f"  LLM diagnosis failed: {e}")
            return f"LLM unavailable: {e}"

    # ── Auto-Fix ──────────────────────────────────────────

    def attempt_fix(self, diagnosis: dict) -> bool:
        """Attempt to auto-fix a broken adapter. Returns True if fixed."""
        slug = diagnosis["slug"]
        src_state = self._get_source_state(slug)

        if src_state["fix_attempts"] >= MAX_FIX_ATTEMPTS:
            log.error(f"  {slug}: max fix attempts ({MAX_FIX_ATTEMPTS}) reached. Disabling.")
            src_state["disabled"] = True
            src_state["disabled_at"] = datetime.now().isoformat()
            self._save_state()
            self._alert_disabled(slug, diagnosis)
            return False

        src_state["fix_attempts"] += 1
        src_state["last_fix_attempt"] = datetime.now().isoformat()
        self._save_state()

        problem = diagnosis["problem"]
        log.info(f"  {slug}: fix attempt #{src_state['fix_attempts']} for: {problem}")

        fix_map = {
            "selectors_broken": self._fix_selectors,
            "url_changed": self._fix_url,
            "blocked": self._fix_blocked,
            "parsing_error": self._fix_selectors,  # use LLM rewrite
            "timeout": self._fix_timeout,
            "unknown_crash": self._fix_selectors,   # use LLM rewrite
        }

        fixer = fix_map.get(problem)
        if fixer:
            return fixer(slug, diagnosis)

        if problem in ("site_unreachable", "adapter_not_found"):
            log.warning(f"  {slug}: {problem} — nothing to fix, will retry later")
            return False

        return self._fix_selectors(slug, diagnosis)

    def _fix_selectors(self, slug: str, diagnosis: dict) -> bool:
        """Fix broken CSS selectors by LLM-rewriting the adapter."""
        adapter_path = self._find_adapter_file(slug)
        if not adapter_path:
            return False

        adapter_code = adapter_path.read_text()
        live_html = diagnosis.get("live_html_sample", "")

        try:
            from ingestion.llm_client import llm_chat

            system = ("You are an expert Python web scraper developer. "
                      "Fix the broken adapter code to match the current HTML.")
            user = f"""The following scraper has broken CSS selectors. The website HTML changed.
Generate the COMPLETE updated adapter code with fixed selectors.

CURRENT ADAPTER CODE:
```python
{adapter_code[:4000]}
```

CURRENT LIVE HTML (sample):
```html
{live_html[:3000]}
```

Rules:
- Keep the same class name, slug, and overall structure
- ONLY change the CSS selectors / find() / select() calls
- Match the actual HTML structure above
- Return ONLY the complete Python file, no explanation"""

            fixed_code = llm_chat(system, user, temperature=0.1, max_tokens=8000, json_mode=False)
            fixed_code = self._extract_python(fixed_code)

            if not fixed_code:
                log.error(f"  {slug}: LLM returned no usable Python code")
                return False

            # Basic validation
            if "class " not in fixed_code and "def " not in fixed_code:
                log.error(f"  {slug}: generated code doesn't look like a valid adapter")
                return False

            # Backup + write
            backup_path = adapter_path.with_suffix('.py.bak')
            backup_path.write_text(adapter_code)
            adapter_path.write_text(fixed_code)
            log.info(f"  {slug}: wrote fixed adapter to {adapter_path}")

            # Test
            if self._test_adapter(slug):
                log.info(f"  {slug}: ✓ FIX VERIFIED — adapter works!")
                self._log_fix(slug, "selectors", adapter_code, fixed_code)
                return True
            else:
                log.warning(f"  {slug}: fix didn't work — rolling back")
                adapter_path.write_text(adapter_code)
                backup_path.unlink(missing_ok=True)
                return False

        except Exception as e:
            log.error(f"  {slug}: selector fix failed: {e}")
            return False

    def _fix_url(self, slug: str, diagnosis: dict) -> bool:
        """Fix changed URLs by discovering redirects."""
        adapter_path = self._find_adapter_file(slug)
        if not adapter_path:
            return False

        adapter_code = adapter_path.read_text()

        try:
            from ingestion.adapters import get_adapter
            adapter_cls = get_adapter(slug)
            if adapter_cls is None:
                return False
            adapter = adapter_cls() if isinstance(adapter_cls, type) else adapter_cls
            base_url = (getattr(adapter, 'base_url', '')
                        or getattr(adapter, 'BASE_URL', ''))

            resp = requests.get(base_url, allow_redirects=True, timeout=15,
                                headers={'User-Agent': 'Mozilla/5.0'})

            from ingestion.llm_client import llm_chat
            system = "Fix the search URL for this scraper."
            user = (f"Base URL: {base_url}\nFinal URL: {resp.url}\n"
                    f"Status: {resp.status_code}\n"
                    f"Code:\n```python\n{adapter_code[:2000]}\n```\n"
                    f"Return ONLY the updated URL assignment line.")

            suggestion = llm_chat(system, user, temperature=0.1,
                                  max_tokens=500, json_mode=False)
            log.info(f"  {slug}: URL fix suggestion: {suggestion[:200]}")
            return self._apply_line_fix(adapter_path, adapter_code, suggestion, slug)
        except Exception as e:
            log.error(f"  {slug}: URL fix failed: {e}")
            return False

    def _fix_blocked(self, slug: str, diagnosis: dict) -> bool:
        """Fix anti-bot blocking by updating headers/delays."""
        adapter_path = self._find_adapter_file(slug)
        if not adapter_path:
            return False

        adapter_code = adapter_path.read_text()
        modified = adapter_code

        fixes = [
            ('REQUEST_DELAY = 2', 'REQUEST_DELAY = 5'),
            ('REQUEST_DELAY = 3', 'REQUEST_DELAY = 8'),
            ('REQUEST_DELAY = (3, 5)', 'REQUEST_DELAY = (8, 15)'),
            ('REQUEST_DELAY = (5, 8)', 'REQUEST_DELAY = (10, 20)'),
        ]

        changes_made = False
        for old, new in fixes:
            if old in modified:
                modified = modified.replace(old, new, 1)
                changes_made = True

        # Also try adding/upgrading User-Agent
        if 'User-Agent' not in modified:
            # Add a headers dict if none exists
            modified = modified.replace(
                'import requests',
                'import requests\n\nDEFAULT_HEADERS = {\n'
                '    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",\n'
                '    "Accept": "text/html,application/xhtml+xml",\n'
                '    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",\n}',
                1
            )
            changes_made = True

        if changes_made:
            backup = adapter_path.with_suffix('.py.bak')
            backup.write_text(adapter_code)
            adapter_path.write_text(modified)

            if self._test_adapter(slug):
                log.info(f"  {slug}: ✓ anti-block fix worked!")
                self._log_fix(slug, "blocked", adapter_code, modified)
                return True
            else:
                adapter_path.write_text(adapter_code)
                backup.unlink(missing_ok=True)

        return False

    def _fix_timeout(self, slug: str, diagnosis: dict) -> bool:
        """Fix timeout issues — increase timeouts and reduce limits."""
        adapter_path = self._find_adapter_file(slug)
        if not adapter_path:
            return False

        adapter_code = adapter_path.read_text()
        modified = adapter_code

        modified = re.sub(
            r'timeout\s*=\s*(\d+)',
            lambda m: f'timeout={int(m.group(1)) * 2}',
            modified
        )
        modified = re.sub(
            r'MAX_PAGES\s*=\s*(\d+)',
            lambda m: f'MAX_PAGES = {max(5, int(m.group(1)) // 2)}',
            modified
        )
        modified = re.sub(
            r'REQUEST_DELAY\s*=\s*(\d+)',
            lambda m: f'REQUEST_DELAY = {int(m.group(1)) + 3}',
            modified
        )

        if modified != adapter_code:
            adapter_path.write_text(modified)
            log.info(f"  {slug}: increased timeouts/delays")
            self._log_fix(slug, "timeout", adapter_code, modified)
            return True
        return False

    # ── Helpers ────────────────────────────────────────────

    def _extract_python(self, text: str) -> Optional[str]:
        """Extract Python code from LLM response."""
        match = re.search(r'```python\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        if text.strip().startswith(('import ', 'from ', '"""', '#', '#!/')):
            return text.strip()
        return None

    def _apply_line_fix(self, adapter_path: Path, original: str,
                        suggestion: str, slug: str) -> bool:
        """Apply a single-line fix from LLM."""
        lines = suggestion.strip().split('\n')
        for line in lines:
            line = line.strip()
            if '=' in line and ('URL' in line or 'url' in line):
                for orig_line in original.split('\n'):
                    if ('URL' in orig_line and '=' in orig_line
                            and orig_line.strip().startswith(
                                ('SEARCH_URL', 'BASE_URL', 'base_url', 'search_url'))):
                        modified = original.replace(orig_line, '    ' + line)
                        adapter_path.write_text(modified)
                        if self._test_adapter(slug):
                            self._log_fix(slug, "url", original, modified)
                            return True
                        else:
                            adapter_path.write_text(original)
                            return False
        return False

    def _test_adapter(self, slug: str, limit: int = 2) -> bool:
        """Test if an adapter can successfully extract listings."""
        import subprocess
        try:
            python = str(SCRIPT_DIR / "venv" / "bin" / "python")
            run_py = str(SCRIPT_DIR / "run.py")

            result = subprocess.run(
                [python, run_py, "scrape", "--source", slug, "--limit", str(limit)],
                capture_output=True, text=True, timeout=120,
                cwd=str(SCRIPT_DIR),
                env={**os.environ, "PYTHONPATH": str(SCRIPT_DIR.parent)},
            )

            output = result.stdout + result.stderr
            if result.returncode == 0 and "0 listings" not in output.lower():
                return True
            return False
        except Exception as e:
            log.error(f"  Test failed for {slug}: {e}")
            return False

    def _log_fix(self, slug: str, fix_type: str, old_code: str, new_code: str):
        """Log a successful fix for audit."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = HEAL_LOG_DIR / f"fix_{slug}_{timestamp}.json"
        log_file.write_text(json.dumps({
            "slug": slug,
            "fix_type": fix_type,
            "timestamp": timestamp,
            "old_code_length": len(old_code),
            "new_code_length": len(new_code),
        }, indent=2))

        src_state = self._get_source_state(slug)
        src_state["fixes_applied"].append({
            "type": fix_type,
            "timestamp": timestamp,
            "success": True,
        })
        self._save_state()

    def _alert_disabled(self, slug: str, diagnosis: dict):
        """Alert when a source is disabled after max fix attempts."""
        log.error(f"")
        log.error(f"  ╔══════════════════════════════════════════╗")
        log.error(f"  ║  SOURCE DISABLED: {slug:<24}║")
        log.error(f"  ║  Problem: {diagnosis['problem']:<31}║")
        log.error(f"  ║  After {MAX_FIX_ATTEMPTS} failed fix attempts            ║")
        log.error(f"  ║  Will retry in {DISABLED_COOLDOWN_HOURS}h                       ║")
        log.error(f"  ╚══════════════════════════════════════════╝")

        alert_file = SCRIPT_DIR / "logs" / "alerts.json"
        alerts = []
        if alert_file.exists():
            try:
                alerts = json.loads(alert_file.read_text())
            except Exception:
                pass
        alerts.append({
            "type": "source_disabled",
            "slug": slug,
            "problem": diagnosis["problem"],
            "timestamp": datetime.now().isoformat(),
            "details": diagnosis.get("details", "")[:200],
        })
        alert_file.write_text(json.dumps(alerts[-50:], indent=2))


# ── Public API: called from auto_pipeline.py ──────────────

def heal_after_scrape(scrape_results: list[dict]) -> None:
    """
    Called after scrape phase. Checks results and auto-heals broken sources.
    scrape_results: list of {"slug", "success", "listings_found", "error"}
    """
    engine = HealingEngine()

    results = [
        ScrapeResult(
            slug=r["slug"],
            success=r["success"],
            listings_found=r.get("listings_found", 0),
            error=r.get("error", ""),
        )
        for r in scrape_results
    ]

    needs_healing = engine.check_results(results)

    if not needs_healing:
        log.info("  All sources healthy — no healing needed.")
        return

    log.info(f"  {len(needs_healing)} source(s) need healing...")

    for result in needs_healing:
        try:
            diagnosis = engine.diagnose(result)
            log.info(f"  {result.slug}: diagnosed as '{diagnosis['problem']}'")

            fixed = engine.attempt_fix(diagnosis)
            if fixed:
                log.info(f"  ✓ {result.slug}: AUTO-FIXED!")
            else:
                state = engine._get_source_state(result.slug)
                log.warning(f"  ✗ {result.slug}: auto-fix failed "
                            f"(attempt {state['fix_attempts']}/{MAX_FIX_ATTEMPTS})")
        except Exception as e:
            log.error(f"  {result.slug}: healing crashed: {e}")
            log.error(traceback.format_exc())
