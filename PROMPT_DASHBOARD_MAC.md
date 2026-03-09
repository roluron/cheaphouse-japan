# PROMPT À COLLER DANS ANTIGRAVITY — Dashboard local Mac Mini pour le pipeline

```
Auto-approve all changes and commands. Don't ask for permission.

## Context

We have an ingestion pipeline that scrapes Japanese real estate sites, enriches listings with Ollama LLM, and pushes to Supabase. It runs daily via cron on a Mac Mini. The user wants a LOCAL web dashboard to monitor and control everything visually — no more terminal commands.

Build a simple, clean Streamlit dashboard at `ingestion/dashboard.py`.

## Install dependencies

Add to requirements.txt and install:
```
streamlit>=1.30.0
plotly>=5.18.0
```

Run: `pip install streamlit plotly` in the venv.

## Create `ingestion/dashboard.py`

```python
#!/usr/bin/env python3
"""
CheapHouse Japan — Pipeline Dashboard
Local web dashboard for monitoring and controlling the ingestion pipeline.
Run: streamlit run dashboard.py
"""

import streamlit as st
import subprocess
import os
import sys
import json
import glob
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

# ── Page config ──
st.set_page_config(
    page_title="CheapHouse Japan — Pipeline",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ──
SCRIPT_DIR = Path(__file__).parent
VENV_PYTHON = SCRIPT_DIR / "venv" / "bin" / "python"
LOG_DIR = SCRIPT_DIR / "logs"
ENV_FILE = SCRIPT_DIR / ".env"

# ── Load env ──
def load_env():
    """Load .env file into os.environ."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                os.environ.setdefault(key.strip(), value.strip())

load_env()

# ── Database connection ──
def get_db_stats():
    """Get stats from Supabase/Postgres."""
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from ingestion.db import execute

        stats = {}

        # Total properties by status
        rows = execute("""
            SELECT
                COALESCE(listing_status, 'active') as status,
                COUNT(*) as count
            FROM properties
            GROUP BY listing_status
        """)
        stats['by_status'] = {r['status']: r['count'] for r in rows}
        stats['total_active'] = stats['by_status'].get('active', 0)
        stats['total_sold'] = stats['by_status'].get('sold', 0)
        stats['total_removed'] = stats['by_status'].get('removed', 0)

        # Total by source
        rows = execute("""
            SELECT source_slug, COUNT(*) as count
            FROM properties
            WHERE listing_status = 'active' OR listing_status IS NULL
            GROUP BY source_slug
            ORDER BY count DESC
        """)
        stats['by_source'] = {r['source_slug']: r['count'] for r in rows}

        # Raw listings pending processing
        rows = execute("""
            SELECT COUNT(*) as count FROM raw_listings
            WHERE processing_status = 'pending'
        """)
        stats['pending'] = rows[0]['count'] if rows else 0

        # Recent scrape runs
        rows = execute("""
            SELECT source_slug, status, listings_found, errors,
                   duration_ms, run_at
            FROM scrape_runs
            ORDER BY run_at DESC
            LIMIT 20
        """)
        stats['recent_runs'] = rows

        # Properties added today
        rows = execute("""
            SELECT COUNT(*) as count FROM properties
            WHERE created_at >= CURRENT_DATE
        """)
        stats['added_today'] = rows[0]['count'] if rows else 0

        # Properties added this week
        rows = execute("""
            SELECT COUNT(*) as count FROM properties
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)
        stats['added_week'] = rows[0]['count'] if rows else 0

        return stats
    except Exception as e:
        return {'error': str(e)}


def get_ollama_status():
    """Check if Ollama is running."""
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in resp.json().get("models", [])]
        return {"running": True, "models": models}
    except Exception:
        return {"running": False, "models": []}


def get_cron_status():
    """Check if cron job is installed."""
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        lines = [l for l in result.stdout.splitlines() if "auto_pipeline" in l]
        return {"installed": bool(lines), "jobs": lines}
    except Exception:
        return {"installed": False, "jobs": []}


def get_recent_logs():
    """Get recent log files."""
    logs = sorted(glob.glob(str(LOG_DIR / "pipeline_*.log")), reverse=True)
    return logs[:10]


def read_log(log_path, tail=100):
    """Read last N lines of a log file."""
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-tail:])
    except Exception as e:
        return f"Error reading log: {e}"


# ── Process runner (background) ──
if 'running_process' not in st.session_state:
    st.session_state.running_process = None
    st.session_state.process_output = ""
    st.session_state.process_name = ""


def run_pipeline_command(cmd_name, args):
    """Run a pipeline command in background."""
    cmd = [str(VENV_PYTHON), str(SCRIPT_DIR / "auto_pipeline.py")] + args
    env = {**os.environ, "PYTHONPATH": str(SCRIPT_DIR.parent)}

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=7200,
            cwd=str(SCRIPT_DIR), env=env,
        )
        return result.stdout + "\n" + result.stderr
    except subprocess.TimeoutExpired:
        return "Process timed out after 2 hours."
    except Exception as e:
        return f"Error: {e}"


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🏠 CheapHouse")
    st.caption("Pipeline Control")

    st.divider()

    # System status
    ollama = get_ollama_status()
    cron = get_cron_status()

    st.subheader("System Status")
    col1, col2 = st.columns(2)
    with col1:
        if ollama['running']:
            st.success("Ollama ✓")
        else:
            st.error("Ollama ✗")
    with col2:
        if cron['installed']:
            st.success("Cron ✓")
        else:
            st.error("Cron ✗")

    if ollama['running']:
        st.caption(f"Models: {', '.join(ollama['models'][:3])}")

    st.divider()

    # Quick actions
    st.subheader("Quick Actions")

    if st.button("▶ Run Full Pipeline", use_container_width=True, type="primary"):
        with st.spinner("Running full pipeline..."):
            output = run_pipeline_command("full", [])
            st.session_state.process_output = output
            st.session_state.process_name = "Full Pipeline"

    if st.button("📥 Scrape Only", use_container_width=True):
        with st.spinner("Scraping..."):
            output = run_pipeline_command("scrape", ["--scrape"])
            st.session_state.process_output = output
            st.session_state.process_name = "Scrape"

    if st.button("🧠 Enrich Only", use_container_width=True):
        with st.spinner("Enriching with Ollama..."):
            output = run_pipeline_command("enrich", ["--enrich"])
            st.session_state.process_output = output
            st.session_state.process_name = "Enrich"

    if st.button("🔍 Freshness Check", use_container_width=True):
        with st.spinner("Checking listing freshness..."):
            output = run_pipeline_command("freshness", ["--freshness"])
            st.session_state.process_output = output
            st.session_state.process_name = "Freshness"

    st.divider()

    # Ollama controls
    if not ollama['running']:
        if st.button("Start Ollama", use_container_width=True):
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            st.rerun()


# ══════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════

# Tab navigation
tab_overview, tab_add_url, tab_newsletter, tab_logs = st.tabs([
    "📊 Overview", "🔗 Add URL", "📧 Newsletter Import", "📄 Logs"
])

# ── TAB 1: Overview ──
with tab_overview:
    stats = get_db_stats()

    if 'error' in stats:
        st.error(f"Database error: {stats['error']}")
    else:
        # Big numbers
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Active Listings", stats.get('total_active', 0))
        with col2:
            st.metric("Added Today", stats.get('added_today', 0))
        with col3:
            st.metric("Added This Week", stats.get('added_week', 0))
        with col4:
            st.metric("Sold", stats.get('total_sold', 0))
        with col5:
            st.metric("Pending Enrichment", stats.get('pending', 0))

        st.divider()

        # By source chart
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("Listings by Source")
            if stats.get('by_source'):
                import plotly.express as px
                source_data = [
                    {"source": k, "count": v}
                    for k, v in stats['by_source'].items()
                ]
                fig = px.bar(
                    source_data, x="source", y="count",
                    color_discrete_sequence=["#C9A96E"],
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#ffffff",
                    xaxis_title="",
                    yaxis_title="Listings",
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("Recent Scrape Runs")
            if stats.get('recent_runs'):
                for run in stats['recent_runs'][:8]:
                    status_icon = "✓" if run['status'] == 'success' else "✗"
                    duration = f"{run['duration_ms']//1000}s" if run.get('duration_ms') else "?"
                    run_time = run['run_at']
                    if hasattr(run_time, 'strftime'):
                        run_time = run_time.strftime('%m/%d %H:%M')
                    st.text(f"{status_icon} {run['source_slug']}: {run['listings_found']} ({duration}) — {run_time}")
            else:
                st.info("No scrape runs yet.")


# ── TAB 2: Add URL ──
with tab_add_url:
    st.subheader("Add a Property URL")
    st.caption("Found a cool listing online? Paste the URL and we'll scrape it directly into the pipeline.")

    url_input = st.text_input(
        "Property URL",
        placeholder="https://www.homes.co.jp/kodate/b-12345678/ or any Japanese real estate URL",
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        source_hint = st.selectbox("Source (auto-detect)", [
            "auto",
            "homes-co-jp",
            "athome-co-jp",
            "suumo-jp",
            "realestate-co-jp",
            "akiya-mart",
            "koryoya",
            "heritage-homes",
            "bukkenfan",
            "eikohome",
            "other",
        ])

    if st.button("Scrape This URL", type="primary"):
        if url_input:
            with st.spinner(f"Scraping {url_input}..."):
                # Detect source from URL
                source = source_hint
                if source == "auto":
                    if "homes.co.jp" in url_input:
                        source = "homes-co-jp"
                    elif "athome.co.jp" in url_input:
                        source = "athome-co-jp"
                    elif "suumo.jp" in url_input:
                        source = "suumo-jp"
                    elif "realestate.co.jp" in url_input:
                        source = "realestate-co-jp"
                    elif "akiya-mart" in url_input:
                        source = "akiya-mart"
                    elif "koryoya" in url_input:
                        source = "koryoya"
                    else:
                        source = "other"

                if source == "other":
                    st.warning("Can't auto-detect the source. Please select manually.")
                else:
                    # Run single URL scrape
                    cmd = [
                        str(VENV_PYTHON), str(SCRIPT_DIR / "run.py"),
                        "scrape-url", "--source", source, "--url", url_input,
                    ]
                    try:
                        result = subprocess.run(
                            cmd, capture_output=True, text=True, timeout=60,
                            cwd=str(SCRIPT_DIR),
                        )
                        if result.returncode == 0:
                            st.success(f"Scraped successfully from {source}!")
                            st.code(result.stdout[-500:])
                        else:
                            st.error(f"Scrape failed: {result.stderr[-500:]}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.warning("Please enter a URL.")

    st.divider()

    # Batch URL input
    st.subheader("Batch Import — Multiple URLs")
    st.caption("One URL per line. All will be scraped and added to the pipeline.")

    batch_urls = st.text_area(
        "URLs (one per line)",
        height=150,
        placeholder="https://www.homes.co.jp/kodate/b-12345678/\nhttps://suumo.jp/jj/bukken/shosai/...\nhttps://www.athome.co.jp/kodate/...",
    )

    if st.button("Scrape All URLs"):
        urls = [u.strip() for u in batch_urls.splitlines() if u.strip()]
        if urls:
            progress = st.progress(0)
            for i, url in enumerate(urls):
                st.text(f"Scraping {i+1}/{len(urls)}: {url[:80]}...")
                # Auto-detect and scrape each
                source = "other"
                if "homes.co.jp" in url:
                    source = "homes-co-jp"
                elif "athome.co.jp" in url:
                    source = "athome-co-jp"
                elif "suumo.jp" in url:
                    source = "suumo-jp"
                elif "realestate.co.jp" in url:
                    source = "realestate-co-jp"

                if source != "other":
                    try:
                        cmd = [
                            str(VENV_PYTHON), str(SCRIPT_DIR / "run.py"),
                            "scrape-url", "--source", source, "--url", url,
                        ]
                        subprocess.run(cmd, capture_output=True, timeout=60, cwd=str(SCRIPT_DIR))
                    except Exception:
                        pass

                progress.progress((i + 1) / len(urls))
            st.success(f"Done! Scraped {len(urls)} URLs.")
        else:
            st.warning("No URLs entered.")


# ── TAB 3: Newsletter Import ──
with tab_newsletter:
    st.subheader("Import from Newsletter")
    st.caption(
        "Paste the content of a CheapHouse Japan or similar newsletter. "
        "We'll extract property URLs and scrape them all."
    )

    newsletter_text = st.text_area(
        "Paste newsletter content (HTML or text)",
        height=300,
        placeholder="Paste the full email content here...",
    )

    if st.button("Extract & Scrape URLs from Newsletter", type="primary"):
        if newsletter_text:
            import re
            # Extract all URLs from the newsletter
            url_pattern = re.compile(
                r'https?://[^\s<>"\']+(?:homes\.co\.jp|athome\.co\.jp|suumo\.jp|'
                r'realestate\.co\.jp|akiya-mart\.com|cheapjapanhomes\.com|'
                r'oldhousesjapan\.com|koryoya\.com|bukkenfan\.jp)[^\s<>"\']*'
            )
            found_urls = list(set(url_pattern.findall(newsletter_text)))

            # Also try to find generic property-looking URLs
            generic_pattern = re.compile(r'https?://[^\s<>"\']+/(?:property|bukken|kodate|listing)[^\s<>"\']*')
            found_urls += list(set(generic_pattern.findall(newsletter_text)))

            found_urls = list(set(found_urls))  # Dedupe

            if found_urls:
                st.info(f"Found {len(found_urls)} property URLs:")
                for url in found_urls:
                    st.code(url)

                if st.button("Scrape All Found URLs"):
                    progress = st.progress(0)
                    for i, url in enumerate(found_urls):
                        # Auto-detect source and scrape
                        source = "other"
                        for domain, slug in [
                            ("homes.co.jp", "homes-co-jp"),
                            ("athome.co.jp", "athome-co-jp"),
                            ("suumo.jp", "suumo-jp"),
                            ("realestate.co.jp", "realestate-co-jp"),
                        ]:
                            if domain in url:
                                source = slug
                                break

                        if source != "other":
                            try:
                                cmd = [
                                    str(VENV_PYTHON), str(SCRIPT_DIR / "run.py"),
                                    "scrape-url", "--source", source, "--url", url,
                                ]
                                subprocess.run(cmd, capture_output=True, timeout=60, cwd=str(SCRIPT_DIR))
                            except Exception:
                                pass

                        progress.progress((i + 1) / len(found_urls))
                    st.success(f"Scraped {len(found_urls)} listings from newsletter!")
            else:
                st.warning("No property URLs found in the newsletter text.")
        else:
            st.warning("Please paste newsletter content.")


# ── TAB 4: Logs ──
with tab_logs:
    st.subheader("Pipeline Logs")

    logs = get_recent_logs()
    if logs:
        selected_log = st.selectbox(
            "Select log file",
            logs,
            format_func=lambda x: Path(x).name,
        )

        tail_lines = st.slider("Lines to show", 20, 500, 100)

        if selected_log:
            log_content = read_log(selected_log, tail=tail_lines)
            st.code(log_content, language="log")

            if st.button("Refresh"):
                st.rerun()
    else:
        st.info("No logs yet. Run the pipeline to generate logs.")

    # Show cron schedule
    st.divider()
    st.subheader("Cron Schedule")
    cron = get_cron_status()
    if cron['installed']:
        for job in cron['jobs']:
            st.code(job)
    else:
        st.warning("No cron jobs installed. Run setup_cron.sh.")


# ── Process output ──
if st.session_state.process_output:
    st.divider()
    st.subheader(f"Output: {st.session_state.process_name}")
    st.code(st.session_state.process_output[-3000:], language="log")
    if st.button("Clear Output"):
        st.session_state.process_output = ""
        st.session_state.process_name = ""
        st.rerun()


# ── Custom dark theme ──
st.markdown("""
<style>
    .stApp {
        background-color: #0a0a0c;
    }
    .stMetric {
        background-color: #111115;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #1a1a20;
    }
    .stMetricValue {
        color: #C9A96E;
    }
    code {
        color: #e0e0e0 !important;
    }
</style>
""", unsafe_allow_html=True)
```

## Also add a `scrape-url` CLI command to `ingestion/run.py`

The dashboard's "Add URL" feature needs a CLI command to scrape a single URL:

```python
@cli.command("scrape-url")
@click.option("--source", required=True, help="Source adapter slug")
@click.option("--url", required=True, help="URL to scrape")
def scrape_single_url(source, url):
    """Scrape a single URL using the specified adapter."""
    from ingestion.adapters import get_adapter
    from ingestion.storage import save_raw_listings

    adapter = get_adapter(source)
    click.echo(f"Scraping {url} with {source} adapter...")

    listing = adapter.extract_listing(url)
    if listing:
        inserted, updated = save_raw_listings([listing])
        click.echo(f"✓ Saved: {listing.title or 'Untitled'} ({inserted} new, {updated} updated)")
    else:
        click.echo(f"✗ Failed to extract listing from {url}")
```

## Create a launch script: `ingestion/start_dashboard.sh`

```bash
#!/bin/bash
# Launch the CheapHouse pipeline dashboard
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run dashboard.py --server.port 8501 --server.address localhost --browser.gatherUsageStats false
```

Make it executable: `chmod +x start_dashboard.sh`

## OPTIONAL: Auto-start dashboard on Mac boot

Create `ingestion/setup_dashboard_autostart.sh`:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_PATH="$HOME/Library/LaunchAgents/com.cheaphouse.dashboard.plist"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cheaphouse.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/venv/bin/streamlit</string>
        <string>run</string>
        <string>$SCRIPT_DIR/dashboard.py</string>
        <string>--server.port</string>
        <string>8501</string>
        <string>--server.address</string>
        <string>localhost</string>
        <string>--browser.gatherUsageStats</string>
        <string>false</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/cheaphouse-dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/cheaphouse-dashboard.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$SCRIPT_DIR/venv/bin</string>
    </dict>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH"

echo "Dashboard auto-start configured!"
echo "  URL: http://localhost:8501"
echo "  Starts on boot, restarts on crash"
echo ""
echo "Verify: open http://localhost:8501"
echo "Remove: launchctl unload $PLIST_PATH && rm $PLIST_PATH"
```

## Test

After building:
```bash
cd ingestion
source venv/bin/activate
pip install streamlit plotly
streamlit run dashboard.py
```

Opens at http://localhost:8501

## RULES

- Dashboard must work with existing DB schema — read-only queries for stats, use existing CLI for actions
- Dark theme matching the CheapHouse brand (black + gold)
- scrape-url command must follow existing adapter pattern — detect source, call extract_listing, save
- Newsletter import should extract URLs from pasted HTML/text and batch-scrape them
- Dashboard does NOT need authentication — it only runs on localhost
- Keep it simple — Streamlit, no React/Vue/custom frontend
- Build must pass, push to GitHub
```
