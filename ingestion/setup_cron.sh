#!/bin/bash
#
# CheapHouse Japan — Cron Setup
# Sets up daily automatic pipeline on Mac Mini.
# Run once: bash setup_cron.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
SYSTEM_PYTHON="$(which python3 2>/dev/null || which python 2>/dev/null)"
PYTHON_PATH="${VENV_PYTHON:-$SYSTEM_PYTHON}"
PIPELINE_SCRIPT="$SCRIPT_DIR/auto_pipeline.py"
ENV_FILE="$SCRIPT_DIR/.env"

echo "=== CheapHouse Japan — Cron Setup ==="
echo ""
echo "  Script dir:  $SCRIPT_DIR"
echo "  Python:      $PYTHON_PATH"
echo "  Pipeline:    $PIPELINE_SCRIPT"
echo ""

# Check prerequisites
if [ ! -f "$PIPELINE_SCRIPT" ]; then
    echo "ERROR: auto_pipeline.py not found."
    exit 1
fi

if [ ! -f "$PYTHON_PATH" ]; then
    echo "ERROR: Python not found at $PYTHON_PATH"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "WARNING: No .env file found at $ENV_FILE"
    echo "  Required: SUPABASE_URL, SUPABASE_SERVICE_KEY"
    echo ""
fi

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Build cron commands
# Full pipeline at 3 AM (low traffic, good for scraping)
CRON_FULL="0 3 * * * cd $SCRIPT_DIR && source $SCRIPT_DIR/.env 2>/dev/null; $PYTHON_PATH $PIPELINE_SCRIPT >> $SCRIPT_DIR/logs/cron.log 2>&1"

# Freshness check at 2 PM (Japan business hours — more likely to catch sold listings)
CRON_FRESH="0 14 * * * cd $SCRIPT_DIR && source $SCRIPT_DIR/.env 2>/dev/null; $PYTHON_PATH $PIPELINE_SCRIPT --freshness >> $SCRIPT_DIR/logs/cron.log 2>&1"

# Check for existing cron job
EXISTING=$(crontab -l 2>/dev/null | grep "auto_pipeline.py" || true)
if [ -n "$EXISTING" ]; then
    echo "Existing cron jobs found:"
    echo "$EXISTING"
    echo ""
    echo "Replacing existing schedule automatically."
    # Remove old entries
    crontab -l 2>/dev/null | grep -v "auto_pipeline.py" | grep -v "CheapHouse" | crontab -
fi

# Install cron jobs
(
    crontab -l 2>/dev/null
    echo ""
    echo "# CheapHouse Japan — Full pipeline (daily 3 AM)"
    echo "$CRON_FULL"
    echo "# CheapHouse Japan — Freshness check (daily 2 PM)"
    echo "$CRON_FRESH"
) | crontab -

echo ""
echo "Cron jobs installed:"
echo "  Full pipeline:    Daily at 3:00 AM"
echo "  Freshness check:  Daily at 2:00 PM"
echo ""
echo "Verify:  crontab -l"
echo "Remove:  crontab -l | grep -v auto_pipeline | grep -v 'CheapHouse' | crontab -"
echo ""
echo "=== Checklist ==="
echo "  1. Ollama running?   ollama serve (or run setup_ollama_autostart.sh)"
echo "  2. .env configured?  SUPABASE_URL + SUPABASE_SERVICE_KEY"
echo "  3. Mac not sleeping? sudo pmset -a disablesleep 1"
echo ""
echo "Done!"
