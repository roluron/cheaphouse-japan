#!/usr/bin/env python3
"""Full system health check."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

errors = []

def check(name, fn):
    try:
        result = fn()
        print(f"  ✓ {name}: {result}")
    except Exception as e:
        errors.append(f"{name}: {e}")
        print(f"  ✗ {name}: {e}")

print("=" * 60)
print("SYSTEM HEALTH CHECK")
print("=" * 60)

# 1. Core imports
print("\n[1] Core imports...")
check("config", lambda: (
    __import__("ingestion.config", fromlist=["LLM_PROVIDER"]),
    "OK"
)[1])
check("db", lambda: (__import__("ingestion.db", fromlist=["execute"]), "OK")[1])
check("llm_client", lambda: (__import__("ingestion.llm_client", fromlist=["llm_chat"]), "OK")[1])
check("self_heal", lambda: (__import__("ingestion.self_heal", fromlist=["HealingEngine"]), "OK")[1])
check("supabase", lambda: f"v{__import__('supabase').__version__}")
check("streamlit", lambda: f"v{__import__('streamlit').__version__}")
check("plotly", lambda: f"v{__import__('plotly').__version__}")
check("beautifulsoup4", lambda: f"v{__import__('bs4').__version__}")
check("requests", lambda: f"v{__import__('requests').__version__}")
check("psycopg2", lambda: f"v{__import__('psycopg2').__version__}")

# 2. Adapters
print("\n[2] Adapter registry...")
try:
    from ingestion.adapters import ADAPTER_MAP
    print(f"  ✓ {len(ADAPTER_MAP)} adapters registered:")
    for slug in sorted(ADAPTER_MAP.keys()):
        print(f"    • {slug}")
except Exception as e:
    errors.append(f"adapters: {e}")
    print(f"  ✗ adapters: {e}")

# 3. DB connection
print("\n[3] Database...")
try:
    from ingestion.db import execute
    rows = execute("SELECT COUNT(*) as cnt FROM properties")
    cnt = rows[0]["cnt"] if rows else 0
    print(f"  ✓ Connected — {cnt} properties")
    
    rows2 = execute("SELECT COUNT(*) as cnt FROM scrape_runs")
    cnt2 = rows2[0]["cnt"] if rows2 else 0
    print(f"  ✓ {cnt2} scrape runs")
except Exception as e:
    errors.append(f"DB: {e}")
    print(f"  ✗ DB: {e}")

# 4. Required columns
print("\n[4] DB columns...")
try:
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv("ingestion/.env")
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='properties'")
    cols = [r[0] for r in cur.fetchall()]
    for col in ["country", "enrichment_status", "enrichment_error", "enriched_at", "hazard_data",
                "is_duplicate", "title_en", "lifestyle_tags", "listing_status"]:
        if col in cols:
            print(f"  ✓ {col}")
        else:
            errors.append(f"Missing column: {col}")
            print(f"  ✗ {col} — MISSING")
    cur.close(); conn.close()
except Exception as e:
    errors.append(f"DB schema: {e}")
    print(f"  ✗ {e}")

# 5. Ollama
print("\n[5] Ollama...")
try:
    import requests
    resp = requests.get("http://localhost:11434/api/tags", timeout=3)
    models = [m["name"] for m in resp.json().get("models", [])]
    print(f"  ✓ Running — {len(models)} models: {', '.join(models[:3])}")
except Exception as e:
    errors.append(f"Ollama: {e}")
    print(f"  ✗ {e}")

# 6. Cron
print("\n[6] Cron...")
result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
cron_lines = [l for l in result.stdout.splitlines() if "auto_pipeline" in l]
if cron_lines:
    print(f"  ✓ {len(cron_lines)} cron jobs installed")
else:
    errors.append("No cron jobs")
    print("  ✗ No cron jobs")

# 7. run.py
print("\n[7] run.py...")
try:
    result = subprocess.run(
        ["ingestion/venv/bin/python", "ingestion/run.py", "--help"],
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "PYTHONPATH": os.getcwd()}
    )
    if "scrape" in result.stdout.lower() or "pipeline" in result.stdout.lower():
        print(f"  ✓ run.py works")
    else:
        errors.append(f"run.py unexpected output")
        print(f"  ? {result.stdout[:200]}")
        if result.stderr:
            print(f"  stderr: {result.stderr[:200]}")
except Exception as e:
    errors.append(f"run.py: {e}")
    print(f"  ✗ {e}")

# 8. auto_pipeline.py
print("\n[8] auto_pipeline.py...")
try:
    result = subprocess.run(
        ["ingestion/venv/bin/python", "ingestion/auto_pipeline.py", "--help"],
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "PYTHONPATH": os.getcwd()}
    )
    if result.returncode == 0:
        print(f"  ✓ auto_pipeline.py works")
    else:
        errors.append(f"auto_pipeline exit {result.returncode}")
        print(f"  ✗ exit {result.returncode}: {result.stderr[:200]}")
except Exception as e:
    errors.append(f"auto_pipeline: {e}")
    print(f"  ✗ {e}")

# 9. Mac sleep
print("\n[9] Mac sleep...")
result = subprocess.run(["pmset", "-g"], capture_output=True, text=True)
if "SleepDisabled" in result.stdout:
    for line in result.stdout.splitlines():
        if "SleepDisabled" in line:
            print(f"  ✓ {line.strip()}")
            break
else:
    errors.append("Can't check sleep")
    print("  ? Unknown")

# 10. Dashboard syntax
print("\n[10] Dashboard syntax check...")
try:
    result = subprocess.run(
        ["ingestion/venv/bin/python", "-c", "import py_compile; py_compile.compile('ingestion/dashboard.py', doraise=True)"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        print(f"  ✓ dashboard.py compiles OK")
    else:
        errors.append(f"dashboard.py syntax error")
        print(f"  ✗ {result.stderr[:300]}")
except Exception as e:
    errors.append(f"dashboard: {e}")
    print(f"  ✗ {e}")

# Summary
print("\n" + "=" * 60)
if errors:
    print(f"RESULT: {len(errors)} ISSUE(S) FOUND:")
    for e in errors:
        print(f"  ✗ {e}")
else:
    print("RESULT: ALL CHECKS PASSED ✅")
print("=" * 60)
