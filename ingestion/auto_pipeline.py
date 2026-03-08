#!/usr/bin/env python3
"""
CheapHouse Japan — Automated Pipeline
Runs the full scrape → enrich → freshness cycle.
Designed to run daily via cron on Mac Mini.

Usage:
    python auto_pipeline.py              # Full run (scrape + enrich + freshness)
    python auto_pipeline.py --scrape     # Scrape only
    python auto_pipeline.py --enrich     # Enrich only
    python auto_pipeline.py --freshness  # Freshness check only
"""

from __future__ import annotations

import argparse
import glob
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

# ── Paths ────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M')}.log"
)

# ── Logging (file + console) ────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("auto_pipeline")

# ── Configuration ────────────────────────────────────────
# Sources in priority order. Suumo last (slowest, most careful).
SCRAPE_SOURCES = [
    # Curated / character properties (small, run first)
    {"slug": "koryoya", "limit": 50},          # Pre-1950 kominka, ~5 listings
    {"slug": "heritage-homes", "limit": 50},   # Kyoto machiya/kominka, ~20 listings
    {"slug": "bukkenfan", "limit": 200},       # Design-curated, JSON API
    {"slug": "eikohome", "limit": 50},         # Nara specialist, ~8 listings
    # Major portals
    {"slug": "homes-co-jp", "limit": 500},
    {"slug": "athome-co-jp", "limit": 500},
    {"slug": "akiya-mart", "limit": 500},      # English aggregator (source URLs)
    {"slug": "realestate-co-jp", "limit": 200},
    {"slug": "suumo-jp", "limit": 150},        # Lower — Suumo is sensitive
    # ── New Zealand Sources ────────────────────────────────────
    {"slug": "trademe-nz", "limit": 300},       # API — best source
    {"slug": "realestate-co-nz", "limit": 200}, # Medium
    {"slug": "homes-co-nz", "limit": 200},      # Medium — valuations
    {"slug": "oneroof-nz", "limit": 150},       # Medium
    {"slug": "harcourts-nz", "limit": 150},     # Easy — agency
    # ── European Sources ──────────────────────────────────────
    # Easy sources first, hard sources last
    {"slug": "green-acres-fr", "limit": 300},     # France — easy
    {"slug": "notaires-fr", "limit": 200},        # France — medium
    {"slug": "gate-away-it", "limit": 300},       # Italy — easy
    {"slug": "italian-houses", "limit": 200},     # Italy — easy
    {"slug": "1euro-houses", "limit": 50},        # Italy — 1€ program
    {"slug": "idealista-pt", "limit": 200},       # Portugal — API
    {"slug": "imovirtual-pt", "limit": 200},      # Portugal — medium
    {"slug": "blocket-se", "limit": 200},         # Sweden — medium
    {"slug": "hemnet-se", "limit": 150},          # Sweden — hard (last)
    {"slug": "immobiliare-it", "limit": 100},     # Italy — hard (very last)
    # ── USA Sources ────────────────────────────────────────
    {"slug": "cheap-old-houses-us", "limit": 200},  # Curated — easy
    {"slug": "redfin-us", "limit": 500},             # CSV download — easy
    {"slug": "realtor-com", "limit": 300},            # Medium
    {"slug": "landwatch-us", "limit": 300},           # Medium — rural
    {"slug": "auction-com", "limit": 200},            # Medium — foreclosures
]

ENRICH_LIMIT = int(os.environ.get("ENRICH_LIMIT", 500))

# Find the right Python binary (venv or system)
PYTHON = (
    os.path.join(SCRIPT_DIR, "venv", "bin", "python")
    if os.path.exists(os.path.join(SCRIPT_DIR, "venv", "bin", "python"))
    else sys.executable
)
RUN_PY = os.path.join(SCRIPT_DIR, "run.py")


def _run_cmd(cmd: list[str], timeout: int = 3600, label: str = "") -> bool:
    """Run a subprocess, log output, return True on success."""
    log.info(f"  Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=SCRIPT_DIR,
            env={**os.environ, "PYTHONPATH": os.path.dirname(SCRIPT_DIR)},
        )
        if result.stdout:
            for line in result.stdout.strip().split("\n")[-30:]:
                log.info(f"  | {line}")
        if result.returncode != 0:
            log.error(f"  {label} failed (exit {result.returncode})")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[-10:]:
                    log.error(f"  | {line}")
            return False
        log.info(f"  {label} completed successfully.")
        return True
    except subprocess.TimeoutExpired:
        log.error(f"  {label} timed out after {timeout}s.")
        return False
    except Exception as e:
        log.error(f"  {label} error: {e}")
        return False


# ── Phase 1: Check Ollama ────────────────────────────────

def check_ollama() -> bool:
    """Verify Ollama is running. Try to start it if not."""
    try:
        import requests

        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            log.info(f"  Ollama running. Models: {', '.join(models)}")
            return True
    except Exception:
        pass

    log.warning("  Ollama not running. Attempting to start...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(10)

        import requests

        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            log.info("  Ollama started successfully.")
            return True
    except Exception as e:
        log.error(f"  Failed to start Ollama: {e}")

    log.error("  Ollama unavailable. LLM stages will be skipped.")
    return False


# ── Phase 2: Scrape ──────────────────────────────────────

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
            "SELECT error_log FROM scrape_runs "
            "WHERE source_slug = %s AND status != 'success' "
            "ORDER BY run_at DESC LIMIT 1",
            (slug,)
        )
        return rows[0]["error_log"] if rows and rows[0].get("error_log") else ""
    except Exception:
        return ""


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

        listings_found = _get_last_scrape_count(slug)
        scrape_results.append({
            "slug": slug,
            "success": success,
            "listings_found": listings_found,
            "error": _get_last_scrape_error(slug) if not success else "",
        })

        # Pause between sources
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


# ── Phase 3: Enrich ──────────────────────────────────────

def run_enrich() -> None:
    log.info("=" * 60)
    log.info("PHASE 2: ENRICHMENT PIPELINE (Ollama LLM)")
    log.info("=" * 60)

    ollama_ok = check_ollama()

    cmd = [PYTHON, RUN_PY, "pipeline", "--limit", str(ENRICH_LIMIT)]
    if not ollama_ok:
        cmd.append("--skip-llm")
        log.warning("  Running pipeline WITHOUT LLM (rule-based fallbacks only)")

    _run_cmd(
        cmd,
        timeout=14400,  # 4 hours max — Ollama can be slow
        label="Enrichment pipeline",
    )


# ── Phase 4: Freshness ──────────────────────────────────

def run_freshness() -> None:
    log.info("=" * 60)
    log.info("PHASE 3: FRESHNESS CHECK")
    log.info("=" * 60)

    _run_cmd(
        [PYTHON, RUN_PY, "check-freshness"],
        timeout=3600,
        label="Freshness check",
    )


# ── Cleanup ──────────────────────────────────────────────

def cleanup_old_logs(keep_days: int = 14) -> None:
    """Delete log files older than keep_days."""
    cutoff = time.time() - (keep_days * 86400)
    for f in glob.glob(os.path.join(LOG_DIR, "pipeline_*.log")):
        if os.path.getmtime(f) < cutoff:
            os.remove(f)
            log.info(f"  Cleaned up old log: {os.path.basename(f)}")


# ── Main ─────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="CheapHouse Japan Auto Pipeline")
    parser.add_argument("--scrape", action="store_true", help="Run scraping only")
    parser.add_argument("--enrich", action="store_true", help="Run enrichment only")
    parser.add_argument("--freshness", action="store_true", help="Run freshness check only")
    args = parser.parse_args()

    run_all = not (args.scrape or args.enrich or args.freshness)

    start = time.time()
    log.info(f"CheapHouse Japan Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info(f"Python: {PYTHON}")
    log.info(f"Log: {LOG_FILE}")
    log.info("")

    try:
        if run_all or args.scrape:
            run_scrape()

        if run_all or args.enrich:
            run_enrich()

        if run_all or args.freshness:
            run_freshness()

        cleanup_old_logs()

    except KeyboardInterrupt:
        log.warning("Pipeline interrupted by user (Ctrl+C).")
    except Exception as e:
        log.error(f"Pipeline crashed: {e}", exc_info=True)

    elapsed = time.time() - start
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    log.info(f"\nPipeline finished in {hours}h {minutes}m")
    log.info(f"Log saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
