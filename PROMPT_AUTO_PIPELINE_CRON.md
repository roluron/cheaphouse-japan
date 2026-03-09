# PROMPT À COLLER DANS ANTIGRAVITY — Pipeline 100% automatique (scrape + enrich + freshness)

```
Auto-approve all changes and commands. Don't ask for permission.

## Context

The user has:
- A Mac Mini running 24/7
- Ollama installed with local LLM (qwen2.5:14b)
- Multiple scraper adapters (homes.co.jp, athome, suumo, realestate.co.jp)
- A pipeline that normalizes, translates, dedupes, enriches with hazard/lifestyle/what-to-know
- A freshness checker that detects sold/removed listings
- Supabase as the database

Right now everything has to be run manually. We need to make it FULLY AUTOMATIC:
- Scrape new listings daily
- Run the full enrichment pipeline (with local Ollama LLM)
- Check freshness of existing listings
- Zero human intervention after initial setup

## 1. Create `ingestion/auto_pipeline.py` — the master automation script

This single script does EVERYTHING in sequence:

```python
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

import os
import sys
import time
import logging
import subprocess
import argparse
from datetime import datetime, timezone

# ---- Configuration ----
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M')}.log")

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger('auto_pipeline')

# Sources to scrape, in order. Suumo last (slowest, most careful).
SCRAPE_SOURCES = [
    {"slug": "homes-co-jp", "limit": 500},
    {"slug": "athome-co-jp", "limit": 500},
    {"slug": "realestate-co-jp", "limit": 200},
    {"slug": "suumo-jp", "limit": 150},  # Lower limit — Suumo is sensitive
]

# How many properties to enrich per run (to keep Ollama runs manageable)
ENRICH_LIMIT = 500


def check_ollama_running():
    """Verify Ollama is running before starting LLM work."""
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            log.info(f"Ollama OK. Available models: {', '.join(models)}")
            return True
    except Exception:
        pass

    log.warning("Ollama not running. Attempting to start...")
    try:
        # Try to start Ollama in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(10)  # Give it time to boot

        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            log.info("Ollama started successfully.")
            return True
    except Exception as e:
        log.error(f"Failed to start Ollama: {e}")

    log.error("Ollama is not available. LLM enrichment will be skipped.")
    return False


def run_scrape():
    """Scrape all sources."""
    log.info("=" * 60)
    log.info("PHASE 1: SCRAPING NEW LISTINGS")
    log.info("=" * 60)

    total_new = 0
    for source in SCRAPE_SOURCES:
        slug = source["slug"]
        limit = source["limit"]
        log.info(f"\n--- Scraping {slug} (limit: {limit}) ---")

        try:
            result = subprocess.run(
                ["python", "run.py", "scrape", "--source", slug, "--limit", str(limit)],
                capture_output=True, text=True, timeout=3600,  # 1 hour max per source
                cwd=os.path.dirname(__file__),
            )
            log.info(result.stdout[-2000:] if result.stdout else "(no output)")
            if result.returncode != 0:
                log.error(f"Scrape {slug} failed: {result.stderr[-1000:]}")
            else:
                # Try to extract count from output
                log.info(f"Scrape {slug} completed.")
        except subprocess.TimeoutExpired:
            log.error(f"Scrape {slug} timed out after 1 hour.")
        except Exception as e:
            log.error(f"Scrape {slug} error: {e}")

        # Pause between sources to not hammer things
        time.sleep(10)

    return total_new


def run_enrich():
    """Run the full enrichment pipeline (normalize → translate → dedupe → hazard → lifestyle → quality → wtk)."""
    log.info("=" * 60)
    log.info("PHASE 2: ENRICHMENT PIPELINE (Ollama LLM)")
    log.info("=" * 60)

    ollama_ok = check_ollama_running()

    try:
        # Run the pipeline. If Ollama is not available, the pipeline
        # will use rule-based fallbacks for LLM stages.
        cmd = ["python", "run.py", "pipeline", "--limit", str(ENRICH_LIMIT)]
        if not ollama_ok:
            cmd.append("--skip-llm")
            log.warning("Running pipeline WITHOUT LLM (rule-based fallbacks only)")

        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=14400,  # 4 hours max (Ollama is slow)
            cwd=os.path.dirname(__file__),
        )
        log.info(result.stdout[-3000:] if result.stdout else "(no output)")
        if result.returncode != 0:
            log.error(f"Pipeline failed: {result.stderr[-1000:]}")
        else:
            log.info("Enrichment pipeline completed.")
    except subprocess.TimeoutExpired:
        log.error("Pipeline timed out after 4 hours.")
    except Exception as e:
        log.error(f"Pipeline error: {e}")


def run_freshness():
    """Check existing listings for sold/removed status."""
    log.info("=" * 60)
    log.info("PHASE 3: FRESHNESS CHECK")
    log.info("=" * 60)

    try:
        result = subprocess.run(
            ["python", "run.py", "check-freshness"],
            capture_output=True, text=True, timeout=3600,
            cwd=os.path.dirname(__file__),
        )
        log.info(result.stdout[-2000:] if result.stdout else "(no output)")
        if result.returncode != 0:
            log.error(f"Freshness check failed: {result.stderr[-1000:]}")
        else:
            log.info("Freshness check completed.")
    except subprocess.TimeoutExpired:
        log.error("Freshness check timed out after 1 hour.")
    except Exception as e:
        log.error(f"Freshness check error: {e}")


def cleanup_old_logs(keep_days=14):
    """Delete log files older than keep_days."""
    import glob
    cutoff = time.time() - (keep_days * 86400)
    for f in glob.glob(os.path.join(LOG_DIR, 'pipeline_*.log')):
        if os.path.getmtime(f) < cutoff:
            os.remove(f)
            log.info(f"Cleaned up old log: {f}")


def main():
    parser = argparse.ArgumentParser(description='CheapHouse Japan Auto Pipeline')
    parser.add_argument('--scrape', action='store_true', help='Run scraping only')
    parser.add_argument('--enrich', action='store_true', help='Run enrichment only')
    parser.add_argument('--freshness', action='store_true', help='Run freshness check only')
    args = parser.parse_args()

    # If no flags, run everything
    run_all = not (args.scrape or args.enrich or args.freshness)

    start = time.time()
    log.info(f"CheapHouse Japan Pipeline started at {datetime.now()}")
    log.info(f"Log file: {LOG_FILE}")

    try:
        if run_all or args.scrape:
            run_scrape()

        if run_all or args.enrich:
            run_enrich()

        if run_all or args.freshness:
            run_freshness()

        # Cleanup old logs
        cleanup_old_logs()

    except KeyboardInterrupt:
        log.warning("Pipeline interrupted by user.")
    except Exception as e:
        log.error(f"Pipeline crashed: {e}", exc_info=True)

    elapsed = time.time() - start
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    log.info(f"\nPipeline finished in {hours}h {minutes}m")
    log.info(f"Log saved to: {LOG_FILE}")


if __name__ == '__main__':
    main()
```

## 2. Create the setup script for cron — `ingestion/setup_cron.sh`

This script sets up the cron job on the Mac Mini:

```bash
#!/bin/bash
#
# CheapHouse Japan — Cron Setup
# Sets up daily automatic pipeline on Mac Mini.
# Run once: bash setup_cron.sh
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="$(which python3 || which python)"
PIPELINE_SCRIPT="$SCRIPT_DIR/auto_pipeline.py"
ENV_FILE="$SCRIPT_DIR/.env"

echo "=== CheapHouse Japan Cron Setup ==="
echo "Script dir: $SCRIPT_DIR"
echo "Python: $PYTHON_PATH"
echo ""

# Check prerequisites
if [ ! -f "$PIPELINE_SCRIPT" ]; then
    echo "ERROR: auto_pipeline.py not found at $PIPELINE_SCRIPT"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "WARNING: No .env file found. Make sure environment variables are set."
    echo "Required: SUPABASE_URL, SUPABASE_SERVICE_KEY"
    echo "Optional: LLM_PROVIDER, OLLAMA_MODEL"
fi

# Build the cron command
# Runs daily at 3 AM (when internet/Mac is least busy)
# Sources the .env file for environment variables
# Logs to pipeline log directory
CRON_CMD="0 3 * * * cd $SCRIPT_DIR && source $ENV_FILE 2>/dev/null; $PYTHON_PATH $PIPELINE_SCRIPT >> $SCRIPT_DIR/logs/cron.log 2>&1"

# Also run freshness check at 2 PM (midday Japan time = good time to catch sold listings)
CRON_FRESHNESS="0 14 * * * cd $SCRIPT_DIR && source $ENV_FILE 2>/dev/null; $PYTHON_PATH $PIPELINE_SCRIPT --freshness >> $SCRIPT_DIR/logs/cron.log 2>&1"

# Check if cron job already exists
EXISTING=$(crontab -l 2>/dev/null | grep "auto_pipeline.py" || true)
if [ -n "$EXISTING" ]; then
    echo "Cron job already exists:"
    echo "$EXISTING"
    echo ""
    read -p "Replace with new schedule? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing cron job."
        exit 0
    fi
    # Remove old entries
    crontab -l 2>/dev/null | grep -v "auto_pipeline.py" | crontab -
fi

# Add new cron jobs
(crontab -l 2>/dev/null; echo "# CheapHouse Japan — Daily pipeline (3 AM)"; echo "$CRON_CMD"; echo "# CheapHouse Japan — Freshness check (2 PM)"; echo "$CRON_FRESHNESS") | crontab -

echo ""
echo "Cron jobs installed:"
echo "  - Full pipeline: Daily at 3:00 AM"
echo "  - Freshness check: Daily at 2:00 PM"
echo ""
echo "To verify: crontab -l"
echo "To remove: crontab -l | grep -v auto_pipeline | crontab -"
echo ""
echo "Make sure:"
echo "  1. Ollama is set to auto-start (stays running)"
echo "  2. .env has SUPABASE_URL and SUPABASE_SERVICE_KEY"
echo "  3. Mac Mini doesn't sleep (System Settings → Energy → Prevent automatic sleeping)"
echo ""
echo "Done!"
```

## 3. Make sure Ollama auto-starts on Mac boot

Create a LaunchAgent so Ollama starts automatically when the Mac Mini boots:

Create file: `ingestion/setup_ollama_autostart.sh`

```bash
#!/bin/bash
#
# Set up Ollama to auto-start on Mac boot via LaunchAgent.
# Run once: bash setup_ollama_autostart.sh
#

PLIST_PATH="$HOME/Library/LaunchAgents/com.cheaphouse.ollama.plist"

cat > "$PLIST_PATH" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cheaphouse.ollama</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ollama.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ollama.stderr.log</string>
</dict>
</plist>
EOF

# Load it now
launchctl load "$PLIST_PATH"

echo "Ollama auto-start configured."
echo "  - Starts on boot"
echo "  - Restarts if it crashes (KeepAlive)"
echo "  - Logs at /tmp/ollama.stdout.log"
echo ""
echo "Verify: launchctl list | grep ollama"
echo "Remove: launchctl unload $PLIST_PATH && rm $PLIST_PATH"
```

## 4. Create `.env.example` with all required variables

```bash
# === CheapHouse Japan Pipeline Configuration ===

# Supabase (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIs...

# LLM Provider (default: ollama = free local)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b

# OpenAI (only if LLM_PROVIDER=openai)
# OPENAI_API_KEY=sk-...

# Pipeline limits (optional, auto_pipeline.py has defaults)
# SCRAPE_LIMIT=500
# ENRICH_LIMIT=500
```

## 5. Add a simple status/health check endpoint

Create `ingestion/status.py` — a tiny script to check if everything is healthy:

```python
#!/usr/bin/env python3
"""Quick health check for the CheapHouse pipeline."""

import os
import json
import glob
from datetime import datetime, timedelta


def check_status():
    status = {"healthy": True, "issues": []}

    # 1. Check Ollama
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in resp.json().get("models", [])]
        status["ollama"] = {"running": True, "models": models}
    except Exception:
        status["ollama"] = {"running": False}
        status["issues"].append("Ollama not running")
        status["healthy"] = False

    # 2. Check last pipeline run
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    logs = sorted(glob.glob(os.path.join(log_dir, 'pipeline_*.log')))
    if logs:
        last_log = logs[-1]
        last_run = datetime.fromtimestamp(os.path.getmtime(last_log))
        hours_ago = (datetime.now() - last_run).total_seconds() / 3600
        status["last_run"] = {
            "log": os.path.basename(last_log),
            "time": last_run.isoformat(),
            "hours_ago": round(hours_ago, 1),
        }
        if hours_ago > 36:
            status["issues"].append(f"No pipeline run in {round(hours_ago)}h")
            status["healthy"] = False
    else:
        status["last_run"] = None
        status["issues"].append("No pipeline runs found")

    # 3. Check Supabase connection
    try:
        from supabase import create_client
        sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])
        result = sb.table('properties').select('id', count='exact').eq('listing_status', 'active').execute()
        status["database"] = {
            "connected": True,
            "active_listings": result.count,
        }
    except Exception as e:
        status["database"] = {"connected": False, "error": str(e)}
        status["issues"].append("Supabase connection failed")
        status["healthy"] = False

    # 4. Check cron
    import subprocess
    cron_result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    has_cron = "auto_pipeline.py" in (cron_result.stdout or "")
    status["cron"] = {"installed": has_cron}
    if not has_cron:
        status["issues"].append("Cron job not installed")

    # Print
    print(json.dumps(status, indent=2))
    return status


if __name__ == '__main__':
    check_status()
```

## 6. Prevent Mac Mini from sleeping

Add this reminder to the setup script output, and also create a quick setup command:

```bash
# In setup_cron.sh, add at the end:
echo ""
echo "IMPORTANT: Disable Mac sleep for the pipeline to run 24/7:"
echo "  sudo pmset -a disablesleep 1"
echo "  (or: System Settings → Energy → Prevent automatic sleeping)"
```

## Summary: What happens after setup

Every day, automatically, with ZERO human intervention:

**3:00 AM — Full pipeline:**
1. Scrape homes.co.jp (500 listings max)
2. Scrape athome.co.jp (500 listings max)
3. Scrape realestate.co.jp (200 listings max)
4. Scrape suumo.jp (150 listings max, careful)
5. Normalize all new raw listings
6. Translate Japanese → English (Ollama, FREE)
7. Deduplicate against existing DB
8. Enrich with hazard data
9. Generate lifestyle tags (Ollama, FREE)
10. Quality scoring
11. Generate What-to-Know reports (Ollama, FREE)
12. Everything saves to Supabase → live on website

**2:00 PM — Freshness check:**
1. Check all active listing URLs
2. Mark sold/removed listings
3. They disappear from the site automatically

**Cost: $0/day. Runs forever on Mac Mini.**

## RULES

- auto_pipeline.py must handle ALL errors gracefully — never crash, never leave things in a broken state
- If Ollama is not running, try to start it. If it can't start, skip LLM stages (use rule-based fallbacks)
- Every run creates a timestamped log in ingestion/logs/
- Old logs auto-cleanup after 14 days
- Suumo gets lower limits and longer delays than other sources
- The cron schedule is 3 AM for scraping (low traffic) and 2 PM for freshness (Japan business hours = more likely to catch updated pages)
- Mac Mini must not sleep — remind user to disable sleep
- Build must pass, push to GitHub
```
