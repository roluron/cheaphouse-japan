#!/usr/bin/env python3
"""
CheapHouse Japan — Pipeline Health Check
Quick status report for the entire system.

Usage:
    python status.py
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from datetime import datetime


def check_status() -> dict:
    status: dict = {"healthy": True, "issues": [], "timestamp": datetime.now().isoformat()}

    # ── 1. Ollama ────────────────────────────────────────
    try:
        import requests

        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in resp.json().get("models", [])]
        status["ollama"] = {"running": True, "models": models}
    except Exception:
        status["ollama"] = {"running": False, "models": []}
        status["issues"].append("Ollama not running")
        status["healthy"] = False

    # ── 2. Last pipeline run ─────────────────────────────
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    logs = sorted(glob.glob(os.path.join(log_dir, "pipeline_*.log")))
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

    # ── 3. Supabase connection ───────────────────────────
    try:
        from supabase import create_client

        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY", "")
        if url and key:
            sb = create_client(url, key)
            result = sb.table("properties").select("id", count="exact").execute()
            status["database"] = {
                "connected": True,
                "total_properties": result.count if hasattr(result, "count") else "unknown",
            }
        else:
            status["database"] = {"connected": False, "error": "SUPABASE_URL/KEY not set"}
            status["issues"].append("Supabase credentials not configured")
            status["healthy"] = False
    except Exception as e:
        status["database"] = {"connected": False, "error": str(e)[:200]}
        status["issues"].append("Supabase connection failed")
        status["healthy"] = False

    # ── 4. Cron ──────────────────────────────────────────
    try:
        cron_result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True
        )
        has_cron = "auto_pipeline.py" in (cron_result.stdout or "")
        status["cron"] = {"installed": has_cron}
        if not has_cron:
            status["issues"].append("Cron job not installed")
    except Exception:
        status["cron"] = {"installed": False}

    # ── 5. Adapters ──────────────────────────────────────
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from ingestion.adapters import ADAPTER_MAP

        status["adapters"] = list(ADAPTER_MAP.keys())
    except Exception as e:
        status["adapters"] = []
        status["issues"].append(f"Adapter import error: {e}")

    # ── Print ────────────────────────────────────────────
    print(json.dumps(status, indent=2, default=str))

    # Summary
    print()
    if status["healthy"]:
        print("System is HEALTHY")
    else:
        print("System has ISSUES:")
        for issue in status["issues"]:
            print(f"  - {issue}")

    return status


if __name__ == "__main__":
    check_status()
