# PROMPT À COLLER DANS ANTIGRAVITY — Pipeline auto-réparant (self-healing scrapers)

```
Auto-approve all changes and commands. Don't ask for permission.

## Context

We have 30+ scrapers (Japan, Europe, USA, NZ) running daily via cron. Some WILL break — sites change HTML, add anti-bot, change URLs. Right now when an adapter fails, it just logs the error and moves on. Nobody fixes it.

We need a SELF-HEALING system: when a scraper fails, the pipeline automatically diagnoses the problem and attempts to fix it — using Ollama (local LLM) to analyze errors and generate patches.

## Architecture

Create `ingestion/self_heal.py` — the self-healing engine.

### How it works:

1. **Detection**: After each scrape run, check results. If a source returns 0 listings or crashes, flag it.
2. **Diagnosis**: Fetch the site's actual HTML, compare to what the adapter expects, use Ollama to identify the mismatch.
3. **Auto-fix**: Generate a patch for the adapter (updated CSS selectors, URL patterns, headers).
4. **Validation**: Test the fix on 1-2 listings. If it works, apply it. If not, escalate.
5. **Escalation**: If auto-fix fails 3 times, disable the source and send a notification.

### Flow:

```
Scrape fails → self_heal.diagnose(slug, error) → fetch live HTML →
  Ollama analyzes difference → generates fix → test fix →
    ✓ works → apply patch + log
    ✗ fails → retry with different approach (up to 3 attempts) →
      ✗ still fails → disable source + alert
```

## Create `ingestion/self_heal.py`

```python
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

# Max auto-fix attempts before disabling a source
MAX_FIX_ATTEMPTS = 3

# How long to wait before retrying a disabled source
DISABLED_COOLDOWN_HOURS = 72  # 3 days


class ScrapeResult:
    """Result from a scrape attempt."""
    def __init__(self, slug: str, success: bool, listings_found: int = 0,
                 error: str = "", error_type: str = ""):
        self.slug = slug
        self.success = success
        self.listings_found = listings_found
        self.error = error
        self.error_type = error_type  # "crash", "zero_results", "timeout", "blocked"


class HealingEngine:
    """
    Self-healing engine for scrapers.
    Uses Ollama to diagnose failures and generate fixes.
    """

    def __init__(self):
        self.state_file = SCRIPT_DIR / "heal_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load healing state (fix attempts, disabled sources, etc.)."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                pass
        return {"sources": {}, "last_run": None}

    def _save_state(self):
        """Persist healing state."""
        self.state["last_run"] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def _get_source_state(self, slug: str) -> dict:
        """Get or create state for a source."""
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
        """
        Check scrape results and return list of sources that need healing.
        """
        needs_healing = []

        for r in results:
            src_state = self._get_source_state(r.slug)

            # Skip disabled sources (unless cooldown expired)
            if src_state["disabled"]:
                disabled_at = datetime.fromisoformat(src_state["disabled_at"])
                if datetime.now() - disabled_at < timedelta(hours=DISABLED_COOLDOWN_HOURS):
                    log.info(f"  {r.slug}: disabled (cooldown until "
                             f"{disabled_at + timedelta(hours=DISABLED_COOLDOWN_HOURS)})")
                    continue
                else:
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
        """
        Diagnose why a scraper failed.
        Returns diagnosis dict with problem type and details.
        """
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

        # 1. Read the adapter source code
        adapter_path = self._find_adapter_file(slug)
        if adapter_path:
            diagnosis["adapter_code"] = adapter_path.read_text()[:5000]
        else:
            diagnosis["problem"] = "adapter_not_found"
            return diagnosis

        # 2. Fetch the actual live HTML from the site
        live_html = self._fetch_live_html(slug)
        if live_html is None:
            diagnosis["problem"] = "site_unreachable"
            diagnosis["details"] = "Could not fetch the site at all. May be down or blocking us."
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

        # 4. Use Ollama to get a detailed analysis
        diagnosis["suggestion"] = self._llm_diagnose(diagnosis)

        return diagnosis

    def _find_adapter_file(self, slug: str) -> Optional[Path]:
        """Find the Python file for an adapter by slug."""
        # Search in all adapter directories
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
                    if f'slug = "{slug}"' in content or f"slug = '{slug}'" in content:
                        return py_file
                except Exception:
                    continue
        return None

    def _fetch_live_html(self, slug: str) -> Optional[str]:
        """Fetch current HTML from the source site."""
        # Map slugs to their search URLs
        from ingestion.adapters import get_adapter
        try:
            adapter = get_adapter(slug)
            # Try to get the base_url or search URL
            url = getattr(adapter, 'SEARCH_URL', None) or getattr(adapter, 'base_url', None)
            if not url:
                return None

            headers = getattr(adapter, 'HEADERS', {})
            headers.setdefault('User-Agent',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            resp = requests.get(url, headers=headers, timeout=30)
            return resp.text
        except Exception as e:
            log.error(f"  Could not fetch live HTML for {slug}: {e}")
            return None

    def _llm_diagnose(self, diagnosis: dict) -> str:
        """Use Ollama to analyze the problem and suggest a fix."""
        from ingestion.llm_client import llm_chat

        prompt = f"""You are debugging a web scraper that stopped working.

PROBLEM TYPE: {diagnosis['problem']}
ADAPTER CODE (first 3000 chars):
```python
{diagnosis['adapter_code'][:3000]}
```

LIVE HTML FROM SITE (first 2000 chars):
```html
{diagnosis['live_html_sample'][:2000]}
```

Analyze:
1. What changed on the website that broke the scraper?
2. What specific CSS selectors or URL patterns need updating?
3. Provide the exact fix as a Python code snippet.

Be specific. Show the exact lines to change. Format as:
DIAGNOSIS: [one line explanation]
FIX_TYPE: [selectors|url|headers|parser|skip]
OLD_CODE: [the broken line(s)]
NEW_CODE: [the fixed line(s)]
"""

        try:
            response = llm_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            return response
        except Exception as e:
            log.error(f"  LLM diagnosis failed: {e}")
            return f"LLM unavailable: {e}"

    # ── Auto-Fix ──────────────────────────────────────────

    def attempt_fix(self, diagnosis: dict) -> bool:
        """
        Attempt to auto-fix a broken adapter based on diagnosis.
        Returns True if fix was applied and verified.
        """
        slug = diagnosis["slug"]
        src_state = self._get_source_state(slug)

        # Check attempt limit
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
        log.info(f"  {slug}: attempting fix #{src_state['fix_attempts']} "
                 f"for problem: {problem}")

        # Route to appropriate fix strategy
        if problem == "selectors_broken":
            return self._fix_selectors(slug, diagnosis)
        elif problem == "url_changed":
            return self._fix_url(slug, diagnosis)
        elif problem == "blocked":
            return self._fix_blocked(slug, diagnosis)
        elif problem == "parsing_error":
            return self._fix_parser(slug, diagnosis)
        elif problem == "timeout":
            return self._fix_timeout(slug, diagnosis)
        elif problem == "site_unreachable":
            log.warning(f"  {slug}: site unreachable — nothing to fix, will retry later")
            return False
        else:
            return self._fix_with_llm(slug, diagnosis)

    def _fix_selectors(self, slug: str, diagnosis: dict) -> bool:
        """Fix broken CSS selectors by analyzing live HTML."""
        from ingestion.llm_client import llm_chat

        adapter_path = self._find_adapter_file(slug)
        if not adapter_path:
            return False

        adapter_code = adapter_path.read_text()
        live_html = diagnosis.get("live_html_sample", "")

        prompt = f"""The following Python scraper adapter has broken CSS selectors.
The website's HTML has changed. Generate the COMPLETE updated adapter code with fixed selectors.

CURRENT ADAPTER CODE:
```python
{adapter_code}
```

CURRENT LIVE HTML (sample):
```html
{live_html[:4000]}
```

Rules:
- Keep the same class name, slug, and overall structure
- ONLY change the CSS selectors / BeautifulSoup find() / select() calls
- Match the actual HTML structure shown above
- Return ONLY the complete Python file content, nothing else
- Do NOT add explanatory text before or after the code
"""

        try:
            fixed_code = llm_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=8000,
            )

            # Clean up LLM response — extract Python code
            fixed_code = self._extract_python(fixed_code)
            if not fixed_code:
                log.error(f"  {slug}: LLM returned no usable Python code")
                return False

            # Validate: must have the class definition and slug
            if f'slug = "{slug}"' not in fixed_code and f"slug = '{slug}'" not in fixed_code:
                log.error(f"  {slug}: generated code doesn't contain correct slug")
                return False

            # Backup original
            backup_path = adapter_path.with_suffix('.py.bak')
            backup_path.write_text(adapter_code)

            # Write fix
            adapter_path.write_text(fixed_code)
            log.info(f"  {slug}: wrote fixed adapter to {adapter_path}")

            # Test the fix
            if self._test_adapter(slug):
                log.info(f"  {slug}: FIX VERIFIED — adapter works now!")
                self._log_fix(slug, "selectors", adapter_code, fixed_code)
                return True
            else:
                # Rollback
                log.warning(f"  {slug}: fix didn't work — rolling back")
                adapter_path.write_text(adapter_code)
                backup_path.unlink(missing_ok=True)
                return False

        except Exception as e:
            log.error(f"  {slug}: selector fix failed: {e}")
            return False

    def _fix_url(self, slug: str, diagnosis: dict) -> bool:
        """Fix changed URLs by discovering new URL patterns."""
        from ingestion.llm_client import llm_chat

        adapter_path = self._find_adapter_file(slug)
        if not adapter_path:
            return False

        adapter_code = adapter_path.read_text()

        # Try to discover the new URL by checking common redirects
        from ingestion.adapters import get_adapter
        try:
            adapter = get_adapter(slug)
            base_url = getattr(adapter, 'base_url', '')

            # Fetch base URL and check for redirects
            resp = requests.get(base_url, allow_redirects=True, timeout=15,
                                headers={'User-Agent': 'Mozilla/5.0'})
            final_url = resp.url
            status = resp.status_code

            prompt = f"""The scraper's search URL is returning 404/changed.
Base URL: {base_url}
Final URL after redirect: {final_url}
Status: {status}
HTML title: {BeautifulSoup(resp.text[:1000], 'html.parser').title}

Current adapter code:
```python
{adapter_code[:3000]}
```

What is the new correct search URL? Return ONLY the updated SEARCH_URL line.
"""
            suggestion = llm_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )

            log.info(f"  {slug}: URL fix suggestion: {suggestion[:200]}")
            # Apply if it looks like a valid URL line
            # This is a simpler fix — just update the URL constant
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

        # Common fixes for blocking:
        fixes = [
            # Add/update User-Agent
            ('HEADERS = {', 'HEADERS = {\n'
             '        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",\n'
             '        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",\n'
             '        "Accept-Language": "en-US,en;q=0.9",\n'
             '        "Accept-Encoding": "gzip, deflate, br",\n'
             '        "Connection": "keep-alive",\n'),
            # Increase delay
            ('REQUEST_DELAY = 2', 'REQUEST_DELAY = 5'),
            ('REQUEST_DELAY = 3', 'REQUEST_DELAY = 8'),
            ('REQUEST_DELAY = (3, 5)', 'REQUEST_DELAY = (8, 15)'),
            ('REQUEST_DELAY = (5, 8)', 'REQUEST_DELAY = (10, 20)'),
        ]

        modified = adapter_code
        changes_made = False
        for old, new in fixes:
            if old in modified:
                modified = modified.replace(old, new, 1)
                changes_made = True

        if changes_made:
            backup = adapter_path.with_suffix('.py.bak')
            backup.write_text(adapter_code)
            adapter_path.write_text(modified)

            if self._test_adapter(slug):
                log.info(f"  {slug}: anti-block fix worked!")
                self._log_fix(slug, "blocked", adapter_code, modified)
                return True
            else:
                adapter_path.write_text(adapter_code)
                backup.unlink(missing_ok=True)

        return False

    def _fix_parser(self, slug: str, diagnosis: dict) -> bool:
        """Fix parsing errors (int(), price parsing, etc.)."""
        # This is similar to the bukkenfan fix — ensure proper parsers are used
        return self._fix_with_llm(slug, diagnosis)

    def _fix_timeout(self, slug: str, diagnosis: dict) -> bool:
        """Fix timeout issues — increase timeouts and reduce limits."""
        adapter_path = self._find_adapter_file(slug)
        if not adapter_path:
            return False

        adapter_code = adapter_path.read_text()
        modified = adapter_code

        # Increase timeouts
        modified = re.sub(r'timeout\s*=\s*(\d+)', lambda m: f'timeout={int(m.group(1)) * 2}', modified)
        # Reduce max pages
        modified = re.sub(r'MAX_PAGES\s*=\s*(\d+)', lambda m: f'MAX_PAGES = {max(5, int(m.group(1)) // 2)}', modified)
        # Increase delays
        modified = re.sub(r'REQUEST_DELAY\s*=\s*(\d+)', lambda m: f'REQUEST_DELAY = {int(m.group(1)) + 3}', modified)

        if modified != adapter_code:
            adapter_path.write_text(modified)
            log.info(f"  {slug}: increased timeouts/delays")
            self._log_fix(slug, "timeout", adapter_code, modified)
            return True

        return False

    def _fix_with_llm(self, slug: str, diagnosis: dict) -> bool:
        """Generic LLM-based fix — let Ollama figure it out."""
        return self._fix_selectors(slug, diagnosis)  # Same approach, LLM rewrites adapter

    # ── Helpers ────────────────────────────────────────────

    def _extract_python(self, text: str) -> Optional[str]:
        """Extract Python code from LLM response."""
        # Try markdown code blocks first
        match = re.search(r'```python\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # If it starts with import or from, it's probably raw code
        if text.strip().startswith(('import ', 'from ', '"""', '#')):
            return text.strip()
        return None

    def _apply_line_fix(self, adapter_path: Path, original: str,
                        suggestion: str, slug: str) -> bool:
        """Apply a single-line fix suggestion from LLM."""
        # Extract the line to change from the suggestion
        lines = suggestion.strip().split('\n')
        for line in lines:
            line = line.strip()
            if '=' in line and ('URL' in line or 'url' in line):
                # Find and replace the matching line in original
                for orig_line in original.split('\n'):
                    if 'URL' in orig_line and '=' in orig_line and orig_line.strip().startswith(('SEARCH_URL', 'BASE_URL', 'base_url')):
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

            # Check if listings were found
            output = result.stdout + result.stderr
            # Look for success patterns
            if "listings extracted" in output and "0 listings" not in output.lower():
                return True
            if result.returncode == 0 and "Error" not in output and "error" not in output.lower():
                return True

            return False
        except Exception as e:
            log.error(f"  Test failed for {slug}: {e}")
            return False

    def _log_fix(self, slug: str, fix_type: str, old_code: str, new_code: str):
        """Log a successful fix for audit trail."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = HEAL_LOG_DIR / f"fix_{slug}_{timestamp}.json"
        log_file.write_text(json.dumps({
            "slug": slug,
            "fix_type": fix_type,
            "timestamp": timestamp,
            "old_code_hash": hash(old_code),
            "new_code_length": len(new_code),
            "diff_lines": len(set(new_code.split('\n')) - set(old_code.split('\n'))),
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
        log.error(f"")

        # Also write to a special alert file the dashboard can read
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
        # Keep last 50 alerts
        alert_file.write_text(json.dumps(alerts[-50:], indent=2))


# ── Integration: call from auto_pipeline.py ──────────────

def heal_after_scrape(scrape_results: list[dict]) -> None:
    """
    Called after scrape phase. Checks results and auto-heals broken sources.

    scrape_results: list of {"slug": str, "success": bool, "listings_found": int, "error": str}
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
                log.warning(f"  ✗ {result.slug}: auto-fix failed "
                            f"(attempt {engine._get_source_state(result.slug)['fix_attempts']}"
                            f"/{MAX_FIX_ATTEMPTS})")
        except Exception as e:
            log.error(f"  {result.slug}: healing crashed: {e}")
            log.error(traceback.format_exc())
```

## Integrate into auto_pipeline.py

In `auto_pipeline.py`, modify the `run_scrape()` function to collect results and feed them to the healer:

```python
def run_scrape() -> None:
    log.info("=" * 60)
    log.info("PHASE 1: SCRAPING NEW LISTINGS")
    log.info("=" * 60)

    scrape_results = []

    for source in SCRAPE_SOURCES:
        slug = source["slug"]
        limit = source["limit"]
        log.info(f"\n--- {slug} (limit {limit}) ---")

        success = _run_cmd(
            [PYTHON, RUN_PY, "scrape", "--source", slug],
            timeout=3600,
            label=f"Scrape {slug}",
        )

        # Parse listings count from log output (or from DB)
        listings_found = _get_last_scrape_count(slug)

        scrape_results.append({
            "slug": slug,
            "success": success,
            "listings_found": listings_found,
            "error": _get_last_scrape_error(slug),
        })

        time.sleep(10)

    # ── SELF-HEALING ──
    log.info("")
    log.info("=" * 60)
    log.info("PHASE 1.5: SELF-HEALING CHECK")
    log.info("=" * 60)

    try:
        from ingestion.self_heal import heal_after_scrape
        heal_after_scrape(scrape_results)
    except Exception as e:
        log.error(f"Self-healing crashed (non-fatal): {e}")

    log.info("")


def _get_last_scrape_count(slug: str) -> int:
    """Get listing count from the last scrape run in DB."""
    try:
        from ingestion.db import execute
        rows = execute(
            "SELECT listings_found FROM scrape_runs "
            "WHERE source_slug = %s ORDER BY run_at DESC LIMIT 1",
            (slug,)
        )
        return rows[0]["listings_found"] if rows else 0
    except Exception:
        return 0


def _get_last_scrape_error(slug: str) -> str:
    """Get error from the last scrape run."""
    try:
        from ingestion.db import execute
        rows = execute(
            "SELECT error_message FROM scrape_runs "
            "WHERE source_slug = %s AND status = 'error' "
            "ORDER BY run_at DESC LIMIT 1",
            (slug,)
        )
        return rows[0]["error_message"] if rows else ""
    except Exception:
        return ""
```

## Dashboard: Add Healing tab

Add to the dashboard `ingestion/dashboard.py` a new section in the AI Processing tab or a separate "🔧 Healing" tab:

```python
# In the AI Processing tab or a new tab:
st.subheader("🔧 Self-Healing Status")

# Read heal_state.json
heal_state_path = SCRIPT_DIR / "heal_state.json"
if heal_state_path.exists():
    heal_state = json.loads(heal_state_path.read_text())

    for slug, state in heal_state.get("sources", {}).items():
        if state.get("disabled"):
            st.error(f"🚫 {slug} — DISABLED (after {state['fix_attempts']} failed fixes)")
        elif state.get("fix_attempts", 0) > 0:
            st.warning(f"⚠️ {slug} — {state['fix_attempts']} fix attempts, last: {state.get('last_fix_attempt', 'never')}")
        # Show fixes applied
        for fix in state.get("fixes_applied", [])[-3:]:
            st.caption(f"  Fixed ({fix['type']}) at {fix['timestamp']}")

# Read alerts
alerts_path = SCRIPT_DIR / "logs" / "alerts.json"
if alerts_path.exists():
    alerts = json.loads(alerts_path.read_text())
    if alerts:
        st.subheader("Recent Alerts")
        for alert in reversed(alerts[-10:]):
            st.warning(f"🚨 {alert['timestamp'][:16]} — {alert['slug']}: {alert['problem']}")
```

## Test

```bash
cd "/Users/test/Documents/CheapHouse Japan/ingestion"
source venv/bin/activate

# Test the healing engine imports correctly
python -c "from ingestion.self_heal import HealingEngine; print('Self-heal module OK')"

# Test with a known-broken adapter
python -c "
from ingestion.self_heal import HealingEngine, ScrapeResult
engine = HealingEngine()
results = engine.check_results([
    ScrapeResult('realestate-co-jp', success=True, listings_found=0),
])
print(f'Needs healing: {len(results)} sources')
if results:
    diag = engine.diagnose(results[0])
    print(f'Diagnosis: {diag[\"problem\"]}')
"
```

Push to GitHub.
```
