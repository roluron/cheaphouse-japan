#!/usr/bin/env python3
"""
CheapHouse — Multi-Country Pipeline Dashboard
Local web dashboard for monitoring and controlling the ingestion pipeline.
Run: streamlit run dashboard.py
"""

import streamlit as st
import subprocess
import os
import sys
import re
import glob
import time
from pathlib import Path

# ── Page config ──
st.set_page_config(
    page_title="CheapHouse — Pipeline",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ──
SCRIPT_DIR = Path(__file__).parent
VENV_PYTHON = SCRIPT_DIR / "venv" / "bin" / "python"
LOG_DIR = SCRIPT_DIR / "logs"
ENV_FILE = SCRIPT_DIR / ".env"

# ── Constants ──
COUNTRY_FLAGS = {
    "japan": "🇯🇵",
    "france": "🇫🇷",
    "italy": "🇮🇹",
    "portugal": "🇵🇹",
    "sweden": "🇸🇪",
    "usa": "🇺🇸",
    "new-zealand": "🇳🇿",
}

COUNTRIES = list(COUNTRY_FLAGS.keys())

SOURCE_DETECTION = {
    # Japan
    "homes.co.jp": ("homes-co-jp", "japan"),
    "athome.co.jp": ("athome-co-jp", "japan"),
    "suumo.jp": ("suumo-jp", "japan"),
    "realestate.co.jp": ("realestate-co-jp", "japan"),
    "akiya-mart": ("akiya-mart", "japan"),
    "koryoya": ("koryoya", "japan"),
    "bukkenfan": ("bukkenfan", "japan"),
    "eikohome": ("eikohome", "japan"),
    "heritagehomes": ("heritage-homes", "japan"),
    # Europe
    "green-acres.fr": ("green-acres-fr", "france"),
    "immobilier.notaires.fr": ("notaires-fr", "france"),
    "gate-away.com": ("gate-away-it", "italy"),
    "italianhousesforsale": ("italian-houses", "italy"),
    "immobiliare.it": ("immobiliare-it", "italy"),
    "idealista.pt": ("idealista-pt", "portugal"),
    "imovirtual.com": ("imovirtual-pt", "portugal"),
    "hemnet.se": ("hemnet-se", "sweden"),
    "blocket.se": ("blocket-se", "sweden"),
    # USA
    "cheapoldhouses.com": ("cheap-old-houses-us", "usa"),
    "redfin.com": ("redfin-us", "usa"),
    "realtor.com": ("realtor-com", "usa"),
    "landwatch.com": ("landwatch-us", "usa"),
    "auction.com": ("auction-com", "usa"),
    # NZ
    "trademe.co.nz": ("trademe-nz", "new-zealand"),
    "realestate.co.nz": ("realestate-co-nz", "new-zealand"),
    "homes.co.nz": ("homes-co-nz", "new-zealand"),
    "oneroof.co.nz": ("oneroof-nz", "new-zealand"),
    "harcourts.co.nz": ("harcourts-nz", "new-zealand"),
}

NEWSLETTER_DOMAINS = [
    r"homes\.co\.jp", r"athome\.co\.jp", r"suumo\.jp", r"realestate\.co\.jp",
    r"akiya-mart\.com", r"koryoya\.com", r"bukkenfan\.jp", r"eikohome\.co\.jp",
    r"green-acres\.fr", r"immobilier\.notaires\.fr", r"gate-away\.com",
    r"italianhousesforsale\.com", r"immobiliare\.it", r"idealista\.pt",
    r"imovirtual\.com", r"hemnet\.se", r"blocket\.se",
    r"cheapoldhouses\.com", r"redfin\.com", r"realtor\.com",
    r"landwatch\.com", r"auction\.com",
    r"trademe\.co\.nz", r"realestate\.co\.nz", r"homes\.co\.nz",
    r"oneroof\.co\.nz", r"harcourts\.co\.nz",
]


# ── Load env ──
def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


load_env()


# ══════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ══════════════════════════════════════════════════════════════

def _get_conn():
    import psycopg2
    return psycopg2.connect(os.environ.get("DATABASE_URL", ""))


def _query(sql, params=None):
    """Run a query and return list of dicts."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        return [{"_error": str(e)}]


def _query_one(sql, params=None):
    rows = _query(sql, params)
    return rows[0] if rows and "_error" not in rows[0] else {}


@st.cache_data(ttl=30)
def get_global_stats():
    return _query_one("""
        SELECT
            COUNT(*) FILTER (WHERE listing_status = 'active' OR listing_status IS NULL) as active,
            COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as today,
            COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as week,
            COUNT(*) FILTER (WHERE enrichment_status = 'pending' OR enrichment_status IS NULL) as pending,
            COUNT(*) FILTER (WHERE enrichment_status = 'complete') as enriched,
            COUNT(*) FILTER (WHERE listing_status IN ('sold', 'removed')) as sold_removed
        FROM properties
    """)


@st.cache_data(ttl=30)
def get_country_stats(country):
    return _query_one("""
        SELECT
            COUNT(*) FILTER (WHERE listing_status = 'active' OR listing_status IS NULL) as active,
            COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as today,
            COUNT(*) FILTER (WHERE enrichment_status = 'pending' OR enrichment_status IS NULL) as pending,
            COUNT(*) FILTER (WHERE enrichment_status = 'complete') as enriched
        FROM properties WHERE country = %s
    """, (country,))


@st.cache_data(ttl=30)
def get_listings_by_country():
    return _query("""
        SELECT country, COUNT(*) as count FROM properties
        WHERE listing_status = 'active' OR listing_status IS NULL
        GROUP BY country ORDER BY count DESC
    """)


@st.cache_data(ttl=30)
def get_recent_runs(limit=20):
    return _query("""
        SELECT source_slug, status, listings_found, listings_new, errors,
               duration_ms, run_at
        FROM scrape_runs ORDER BY run_at DESC LIMIT %s
    """, (limit,))


@st.cache_data(ttl=30)
def get_sources_for_country(country):
    return _query("""
        SELECT primary_source_slug as source, COUNT(*) as count,
               MAX(created_at) as last_added
        FROM properties
        WHERE country = %s AND (listing_status = 'active' OR listing_status IS NULL)
        GROUP BY primary_source_slug ORDER BY count DESC
    """, (country,))


@st.cache_data(ttl=30)
def get_price_distribution(country):
    return _query("""
        SELECT price_jpy FROM properties
        WHERE country = %s AND price_jpy IS NOT NULL
          AND price_jpy > 0 AND price_jpy < 500000000
          AND (listing_status = 'active' OR listing_status IS NULL)
        LIMIT 1000
    """, (country,))


@st.cache_data(ttl=30)
def get_latest_listings(country, limit=10):
    return _query("""
        SELECT original_title, title_en, price_jpy, prefecture, city,
               primary_source_slug, enrichment_status, created_at
        FROM properties WHERE country = %s
        ORDER BY created_at DESC LIMIT %s
    """, (country, limit))


@st.cache_data(ttl=30)
def get_ai_stats():
    return _query_one("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE enrichment_status = 'complete') as enriched,
            COUNT(*) FILTER (WHERE enrichment_status = 'pending' OR enrichment_status IS NULL) as pending,
            COUNT(*) FILTER (WHERE enrichment_status = 'failed') as failed,
            COUNT(*) FILTER (WHERE title_en IS NOT NULL) as translated,
            COUNT(*) FILTER (WHERE lifestyle_tags IS NOT NULL) as tagged
        FROM properties
    """)


@st.cache_data(ttl=30)
def get_country_ai_stats(country):
    return _query_one("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE enrichment_status = 'complete') as enriched,
            COUNT(*) FILTER (WHERE enrichment_status = 'failed') as failed,
            COUNT(*) FILTER (WHERE title_en IS NOT NULL) as translated,
            COUNT(*) FILTER (WHERE lifestyle_tags IS NOT NULL) as tagged
        FROM properties WHERE country = %s
    """, (country,))


@st.cache_data(ttl=30)
def get_pipeline_stages():
    r = _query_one("""
        SELECT
            COUNT(*) as raw_total,
            COUNT(*) FILTER (WHERE title_en IS NOT NULL) as translated,
            COUNT(*) FILTER (WHERE is_duplicate = false OR is_duplicate IS NULL) as deduped,
            COUNT(*) FILTER (WHERE hazard_data IS NOT NULL) as hazard_checked,
            COUNT(*) FILTER (WHERE lifestyle_tags IS NOT NULL) as tagged,
            COUNT(*) FILTER (WHERE enrichment_status = 'complete') as published
        FROM properties
    """)
    if not r:
        return []
    return [
        {"stage": "Raw (scraped)", "count": r.get("raw_total", 0)},
        {"stage": "Translated", "count": r.get("translated", 0)},
        {"stage": "Deduplicated", "count": r.get("deduped", 0)},
        {"stage": "Hazard checked", "count": r.get("hazard_checked", 0)},
        {"stage": "Lifestyle tagged", "count": r.get("tagged", 0)},
        {"stage": "Published", "count": r.get("published", 0)},
    ]


@st.cache_data(ttl=30)
def get_recent_enrichments(limit=20):
    return _query("""
        SELECT id, original_title, title_en, country, primary_source_slug,
               enrichment_status, lifestyle_tags,
               enriched_at
        FROM properties
        WHERE enriched_at IS NOT NULL
        ORDER BY enriched_at DESC LIMIT %s
    """, (limit,))


@st.cache_data(ttl=30)
def get_failed_enrichments(limit=20):
    return _query("""
        SELECT id, original_title, primary_source_slug, country,
               enrichment_error, enrichment_status
        FROM properties
        WHERE enrichment_status = 'failed'
        ORDER BY created_at DESC LIMIT %s
    """, (limit,))


def get_ollama_status():
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in resp.json().get("models", [])]
        return {"running": True, "models": models}
    except Exception:
        return {"running": False, "models": []}


def get_cron_status():
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        lines = [l for l in result.stdout.splitlines() if "auto_pipeline" in l]
        return {"installed": bool(lines), "jobs": lines}
    except Exception:
        return {"installed": False, "jobs": []}


def get_recent_logs():
    return sorted(glob.glob(str(LOG_DIR / "pipeline_*.log")), reverse=True)[:10]


def read_log(log_path, tail=100):
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
            return "".join(lines[-tail:])
    except Exception as e:
        return f"Error: {e}"


# ── Process runner ──
if "process_output" not in st.session_state:
    st.session_state.process_output = ""
    st.session_state.process_name = ""


def run_pipeline_command(args):
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

    ollama = get_ollama_status()
    cron = get_cron_status()

    st.subheader("System Status")
    col1, col2 = st.columns(2)
    with col1:
        if ollama["running"]:
            st.success("Ollama ✓")
        else:
            st.error("Ollama ✗")
    with col2:
        if cron["installed"]:
            st.success("Cron ✓")
        else:
            st.error("Cron ✗")

    if ollama["running"]:
        st.caption(f"Models: {', '.join(ollama['models'][:3])}")

    st.divider()
    st.subheader("Quick Actions")

    if st.button("▶ Run Full Pipeline", use_container_width=True, type="primary"):
        with st.spinner("Running full pipeline..."):
            st.session_state.process_output = run_pipeline_command([])
            st.session_state.process_name = "Full Pipeline"
        st.rerun()

    if st.button("📥 Scrape Only", use_container_width=True):
        with st.spinner("Scraping..."):
            st.session_state.process_output = run_pipeline_command(["--scrape"])
            st.session_state.process_name = "Scrape"
        st.rerun()

    if st.button("🧠 Enrich Only", use_container_width=True):
        with st.spinner("Enriching with Ollama..."):
            st.session_state.process_output = run_pipeline_command(["--enrich"])
            st.session_state.process_name = "Enrich"
        st.rerun()

    if st.button("🔍 Freshness Check", use_container_width=True):
        with st.spinner("Checking freshness..."):
            st.session_state.process_output = run_pipeline_command(["--freshness"])
            st.session_state.process_name = "Freshness"
        st.rerun()

    st.divider()

    if not ollama["running"]:
        if st.button("Start Ollama", use_container_width=True):
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            st.rerun()


# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab_overview, tab_countries, tab_ai, tab_add_url, tab_newsletter, tab_logs = st.tabs(
    ["📊 Overview", "🌍 Countries", "🤖 AI Processing", "🔗 Add URL", "📧 Newsletter", "📄 Logs"]
)

# ── TAB 1: OVERVIEW ──────────────────────────────────────────
with tab_overview:
    gs = get_global_stats()
    if "_error" in gs:
        st.error(f"DB error: {gs.get('_error', gs)}")
    else:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Active Listings", gs.get("active", 0))
        c2.metric("Added Today", gs.get("today", 0))
        c3.metric("This Week", gs.get("week", 0))
        c4.metric("Pending Enrich", gs.get("pending", 0))
        c5.metric("Enriched", gs.get("enriched", 0))
        c6.metric("Sold/Removed", gs.get("sold_removed", 0))

        st.divider()
        st.subheader("By Country")
        cols = st.columns(4)
        for i, country in enumerate(COUNTRIES):
            with cols[i % 4]:
                cs = get_country_stats(country)
                flag = COUNTRY_FLAGS.get(country, "🏠")
                name = country.replace("-", " ").title()
                st.metric(f"{flag} {name}", cs.get("active", 0))
                st.caption(f"+{cs.get('today', 0)} today · {cs.get('pending', 0)} pending")

        st.divider()
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("Listings Distribution")
            by_country = get_listings_by_country()
            if by_country and "_error" not in by_country[0]:
                import plotly.express as px
                fig = px.pie(
                    by_country, names="country", values="count",
                    color_discrete_sequence=[
                        "#C9A96E", "#8B7355", "#D4AF37",
                        "#BDB76B", "#DAA520", "#B8860B", "#CD853F",
                    ],
                    hole=0.4,
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#ffffff",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No listings yet.")

        with col_right:
            st.subheader("Recent Activity")
            runs = get_recent_runs(12)
            if runs and "_error" not in runs[0]:
                for run in runs:
                    icon = "✓" if run.get("status") == "success" else "✗"
                    dur = f"{run['duration_ms'] // 1000}s" if run.get("duration_ms") else "?"
                    t = run.get("run_at", "")
                    if hasattr(t, "strftime"):
                        t = t.strftime("%m/%d %H:%M")
                    found = run.get("listings_found", 0)
                    src = run.get("source_slug", "?")
                    st.text(f"{icon} {src}: {found} ({dur}) — {t}")
            else:
                st.info("No scrape runs yet.")


# ── TAB 2: COUNTRIES ─────────────────────────────────────────
with tab_countries:
    sel_country = st.selectbox(
        "Select Country",
        COUNTRIES,
        format_func=lambda c: f"{COUNTRY_FLAGS.get(c, '')} {c.replace('-', ' ').title()}",
    )

    cs = get_country_stats(sel_country)
    flag = COUNTRY_FLAGS.get(sel_country, "")
    name = sel_country.replace("-", " ").title()
    st.header(f"{flag} {name}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active", cs.get("active", 0))
    c2.metric("Today", cs.get("today", 0))
    c3.metric("Pending", cs.get("pending", 0))
    c4.metric("Enriched", cs.get("enriched", 0))

    st.divider()
    st.subheader(f"Sources — {name}")
    sources = get_sources_for_country(sel_country)
    if sources and "_error" not in sources[0]:
        for src in sources:
            last = src.get("last_added", "")
            if hasattr(last, "strftime"):
                last = last.strftime("%m/%d %H:%M")
            st.text(f"  ● {src['source']}: {src['count']} listings (last: {last})")
    else:
        st.info("No sources found for this country yet.")

    st.divider()
    st.subheader("Price Distribution")
    prices = get_price_distribution(sel_country)
    if prices and "_error" not in prices[0]:
        import plotly.express as px
        fig = px.histogram(
            prices, x="price_jpy", nbins=30,
            color_discrete_sequence=["#C9A96E"],
            labels={"price_jpy": "Price (JPY)"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#ffffff",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No price data yet.")

    st.divider()
    st.subheader("Latest Listings")
    listings = get_latest_listings(sel_country, 10)
    if listings and "_error" not in listings[0]:
        for item in listings:
            title = item.get("title_en") or item.get("original_title") or "Untitled"
            price = f"¥{item['price_jpy']:,}" if item.get("price_jpy") else "N/A"
            loc = f"{item.get('prefecture', '') or ''} {item.get('city', '') or ''}".strip()
            src = item.get("primary_source_slug", "?")
            enr = item.get("enrichment_status", "pending")
            badge = "✅" if enr == "complete" else "⏳" if enr == "pending" else "❌"
            st.text(f"{badge} {title[:55]} — {price} — {loc} [{src}]")
    else:
        st.info("No listings yet.")


# ── TAB 3: AI PROCESSING ─────────────────────────────────────
with tab_ai:
    st.subheader("🤖 AI Processing Status")

    ai = get_ai_stats()
    if "_error" not in ai:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total", ai.get("total", 0))
        c2.metric("Enriched", ai.get("enriched", 0))
        c3.metric("Pending", ai.get("pending", 0))
        c4.metric("Translated", ai.get("translated", 0))
        c5.metric("Failed", ai.get("failed", 0))

    st.divider()
    st.subheader("Enrichment by Country")
    for country in COUNTRIES:
        ca = get_country_ai_stats(country)
        total = ca.get("total", 0)
        enriched = ca.get("enriched", 0)
        pct = (enriched / total * 100) if total > 0 else 0
        flag = COUNTRY_FLAGS.get(country, "")
        name = country.replace("-", " ").title()
        label = f"{flag} {name}: {enriched}/{total} ({pct:.0f}%)"
        st.progress(min(pct / 100, 1.0), text=label)

    st.divider()
    st.subheader("Processing Pipeline")
    stages = get_pipeline_stages()
    if stages:
        import plotly.express as px
        fig = px.funnel(
            stages, x="count", y="stage",
            color_discrete_sequence=["#C9A96E"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#ffffff",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Recent AI Enrichments")
    recent = get_recent_enrichments()
    if recent and "_error" not in recent[0]:
        for item in recent:
            c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
            with c1:
                t = item.get("title_en") or item.get("original_title") or "Untitled"
                st.text(t[:55])
            with c2:
                flag = COUNTRY_FLAGS.get(item.get("country", ""), "")
                st.text(f"{flag} {item.get('primary_source_slug', '')}")
            with c3:
                badges = []
                if item.get("title_en"):
                    badges.append("🌐")
                if item.get("lifestyle_tags"):
                    badges.append("🏷️")
                st.text(" ".join(badges) or "—")
            with c4:
                ea = item.get("enriched_at", "")
                st.text(str(ea)[:16] if ea else "—")
    else:
        st.info("No enrichments yet.")

    st.divider()
    st.subheader("Failed Enrichments")
    failed = get_failed_enrichments()
    if failed and "_error" not in failed[0]:
        for item in failed:
            title = item.get("original_title") or "Untitled"
            src = item.get("primary_source_slug", "?")
            with st.expander(f"❌ {title[:50]} — {src}"):
                st.text(f"Error: {item.get('enrichment_error', 'Unknown')}")
    else:
        st.success("No failed enrichments!")

    st.divider()
    st.subheader("Ollama LLM Stats")
    if ollama["running"]:
        st.success(f"Ollama running — Models: {', '.join(ollama['models'])}")
    else:
        st.error("Ollama is NOT running!")
        if st.button("Start Ollama Now"):
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            st.rerun()

    # ── Self-Healing Status ──
    st.divider()
    st.subheader("🔧 Self-Healing Status")

    import json as _json
    heal_state_path = SCRIPT_DIR / "heal_state.json"
    if heal_state_path.exists():
        try:
            heal_state = _json.loads(heal_state_path.read_text())
            sources = heal_state.get("sources", {})
            disabled = {s: v for s, v in sources.items() if v.get("disabled")}
            attempting = {s: v for s, v in sources.items()
                         if v.get("fix_attempts", 0) > 0 and not v.get("disabled")}

            if disabled:
                for slug, state in disabled.items():
                    st.error(f"🚫 {slug} — DISABLED "
                             f"(after {state['fix_attempts']} failed fixes)")
            if attempting:
                for slug, state in attempting.items():
                    st.warning(f"⚠️ {slug} — {state['fix_attempts']} fix attempts, "
                               f"last: {(state.get('last_fix_attempt') or 'never')[:16]}")

            # Show recent fixes
            all_fixes = []
            for slug, state in sources.items():
                for fix in state.get("fixes_applied", []):
                    fix["slug"] = slug
                    all_fixes.append(fix)
            all_fixes.sort(key=lambda f: f.get("timestamp", ""), reverse=True)
            if all_fixes:
                st.caption("Recent auto-fixes:")
                for fix in all_fixes[:5]:
                    st.text(f"  ✓ {fix['slug']} — {fix['type']} fix at {fix['timestamp']}")

            if not disabled and not attempting and not all_fixes:
                st.success("All scrapers healthy — no healing needed.")
        except Exception as e:
            st.caption(f"Could not read heal state: {e}")
    else:
        st.info("Self-healing not yet activated (runs after first scrape)")

    # Alerts
    alerts_path = SCRIPT_DIR / "logs" / "alerts.json"
    if alerts_path.exists():
        try:
            alerts = _json.loads(alerts_path.read_text())
            if alerts:
                st.subheader("🚨 Alerts")
                for alert in reversed(alerts[-10:]):
                    st.warning(f"{alert.get('timestamp', '')[:16]} — "
                               f"{alert.get('slug', '?')}: {alert.get('problem', '?')}")
        except Exception:
            pass


# ── TAB 4: ADD URL ────────────────────────────────────────────
with tab_add_url:
    st.subheader("Add a Property URL")
    st.caption("Paste any URL — we detect the country and source automatically.")

    url_input = st.text_input(
        "Property URL",
        placeholder="Paste any property URL from any supported country...",
    )

    # Auto-detect
    detected_source, detected_country = None, None
    if url_input:
        for domain, (source, country) in SOURCE_DETECTION.items():
            if domain in url_input:
                detected_source, detected_country = source, country
                break
        if detected_source:
            flag = COUNTRY_FLAGS.get(detected_country, "")
            st.info(f"Detected: {flag} {detected_country.title()} → {detected_source}")
        else:
            st.warning("Can't auto-detect. Select manually below.")

    col1, col2 = st.columns(2)
    with col1:
        all_sources = sorted(set(s for s, _ in SOURCE_DETECTION.values()))
        source_manual = st.selectbox("Source", ["auto"] + all_sources)
    with col2:
        country_manual = st.selectbox("Country", ["auto"] + COUNTRIES)

    if st.button("Scrape This URL", type="primary"):
        if url_input:
            source = detected_source if source_manual == "auto" else source_manual
            if not source:
                st.warning("Can't detect source. Select manually.")
            else:
                with st.spinner(f"Scraping with {source}..."):
                    cmd = [
                        str(VENV_PYTHON), str(SCRIPT_DIR / "run.py"),
                        "scrape-url", "--source", source, "--url", url_input,
                    ]
                    env = {**os.environ, "PYTHONPATH": str(SCRIPT_DIR.parent)}
                    try:
                        result = subprocess.run(
                            cmd, capture_output=True, text=True,
                            timeout=60, cwd=str(SCRIPT_DIR), env=env,
                        )
                        if result.returncode == 0:
                            st.success(f"Scraped from {source}!")
                            st.code(result.stdout[-500:])
                        else:
                            st.error(f"Failed: {result.stderr[-500:]}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.warning("Please enter a URL.")

    st.divider()
    st.subheader("Batch Import — Multiple URLs")
    st.caption("One URL per line.")

    batch_urls = st.text_area("URLs (one per line)", height=150)

    if st.button("Scrape All URLs"):
        urls = [u.strip() for u in batch_urls.splitlines() if u.strip()]
        if urls:
            progress = st.progress(0)
            env = {**os.environ, "PYTHONPATH": str(SCRIPT_DIR.parent)}
            for i, url in enumerate(urls):
                source = None
                for domain, (s, _) in SOURCE_DETECTION.items():
                    if domain in url:
                        source = s
                        break
                if source:
                    try:
                        cmd = [
                            str(VENV_PYTHON), str(SCRIPT_DIR / "run.py"),
                            "scrape-url", "--source", source, "--url", url,
                        ]
                        subprocess.run(cmd, capture_output=True, timeout=60,
                                       cwd=str(SCRIPT_DIR), env=env)
                    except Exception:
                        pass
                progress.progress((i + 1) / len(urls))
            st.success(f"Done! Processed {len(urls)} URLs.")
        else:
            st.warning("No URLs entered.")


# ── TAB 5: NEWSLETTER IMPORT ─────────────────────────────────
with tab_newsletter:
    st.subheader("Import from Newsletter")
    st.caption("Paste a newsletter. We'll extract property URLs and scrape them all.")

    newsletter_text = st.text_area(
        "Paste newsletter content (HTML or text)", height=300,
    )

    if st.button("Extract & Scrape URLs", type="primary"):
        if newsletter_text:
            pattern = re.compile(
                r"https?://[^\s<>\"']+"
                + r"(?:" + "|".join(NEWSLETTER_DOMAINS) + r")"
                + r"[^\s<>\"']*"
            )
            found_urls = list(set(pattern.findall(newsletter_text)))

            if found_urls:
                st.info(f"Found {len(found_urls)} property URLs:")
                for u in found_urls[:20]:
                    st.code(u)

                if st.button("Scrape Found URLs"):
                    progress = st.progress(0)
                    env = {**os.environ, "PYTHONPATH": str(SCRIPT_DIR.parent)}
                    for i, url in enumerate(found_urls):
                        source = None
                        for domain, (s, _) in SOURCE_DETECTION.items():
                            if domain in url:
                                source = s
                                break
                        if source:
                            try:
                                cmd = [
                                    str(VENV_PYTHON), str(SCRIPT_DIR / "run.py"),
                                    "scrape-url", "--source", source, "--url", url,
                                ]
                                subprocess.run(cmd, capture_output=True, timeout=60,
                                               cwd=str(SCRIPT_DIR), env=env)
                            except Exception:
                                pass
                        progress.progress((i + 1) / len(found_urls))
                    st.success(f"Scraped {len(found_urls)} listings!")
            else:
                st.warning("No property URLs found.")
        else:
            st.warning("Please paste newsletter content.")


# ── TAB 6: LOGS ──────────────────────────────────────────────
with tab_logs:
    st.subheader("Pipeline Logs")

    logs = get_recent_logs()
    if logs:
        selected_log = st.selectbox(
            "Select log file", logs,
            format_func=lambda x: Path(x).name,
        )
        tail_lines = st.slider("Lines to show", 20, 500, 100)
        if selected_log:
            st.code(read_log(selected_log, tail=tail_lines), language="log")
            if st.button("Refresh"):
                st.rerun()
    else:
        st.info("No logs yet. Run the pipeline to generate logs.")

    st.divider()
    st.subheader("Cron Schedule")
    cron = get_cron_status()
    if cron["installed"]:
        for job in cron["jobs"]:
            st.code(job)
    else:
        st.warning("No cron jobs installed.")


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
    .stApp { background-color: #0a0a0c; }
    [data-testid="stMetric"] {
        background-color: #111115;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #1a1a20;
    }
    [data-testid="stMetricValue"] { color: #C9A96E; }
    .stProgress > div > div { background-color: #C9A96E; }
    [data-baseweb="tab"] { color: #888; }
    [aria-selected="true"] { color: #C9A96E !important; border-bottom-color: #C9A96E !important; }
    code { color: #e0e0e0 !important; }
    h1, h2, h3 { color: #f0f0f0; }
</style>
""", unsafe_allow_html=True)
