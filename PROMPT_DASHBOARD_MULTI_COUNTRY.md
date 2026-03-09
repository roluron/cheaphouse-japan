# PROMPT À COLLER DANS ANTIGRAVITY — Dashboard multi-pays + suivi IA

```
Auto-approve all changes and commands. Don't ask for permission.

## Context

We have a Streamlit dashboard at `ingestion/dashboard.py`. Right now it only handles Japan. But we're expanding to Europe (France, Italy, Portugal, Sweden), USA, and New Zealand. The dashboard needs a COMPLETE overhaul to support multi-country and show AI processing status.

## OVERHAUL `ingestion/dashboard.py`

Replace the entire dashboard with this upgraded version. Keep the same Streamlit approach, same dark theme (black + gold #C9A96E), but make it multi-country aware and add AI processing tracking.

### New Tab Structure:

```
Sidebar:
  🏠 CheapHouse
  Pipeline Control
  [System Status: Ollama, Cron]
  [Quick Actions: Run Pipeline, Scrape, Enrich, Freshness]
  [Country Filter: All / Japan / Europe / USA / NZ]

Tabs:
  📊 Overview          — Global stats + per-country breakdown
  🌍 Countries         — Detailed per-country view with source breakdown
  🤖 AI Processing     — What's been enriched, what's pending, LLM stats
  🔗 Add URL           — Multi-country URL detection
  📧 Newsletter Import — Multi-source newsletter extraction
  📄 Logs              — Pipeline logs viewer
```

### TAB 1: Overview (revamped)

```python
with tab_overview:
    # ── Country selector in sidebar ──
    # Already handled in sidebar — filters all queries

    # ── Top-level metrics (filtered by country if selected) ──
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    # Active Listings | Added Today | Added This Week | Pending Enrichment | Enriched | Sold/Removed

    # ── Country cards — one per country showing summary ──
    st.subheader("By Country")
    countries = ["japan", "france", "italy", "portugal", "sweden", "usa", "new-zealand"]

    # Display as a grid: 4 columns
    cols = st.columns(4)
    for i, country in enumerate(countries):
        with cols[i % 4]:
            # Card with:
            # Flag emoji + country name
            # Total active listings
            # Added today
            # Pending enrichment
            # Mini bar showing sources
            country_stats = get_country_stats(country)
            flag = COUNTRY_FLAGS.get(country, "🏠")
            st.metric(f"{flag} {country.replace('-', ' ').title()}", country_stats['active'])
            st.caption(f"+{country_stats['today']} today | {country_stats['pending']} pending")

    # ── Global chart: listings by country (stacked bar or donut) ──
    st.divider()
    st.subheader("Listings Distribution")
    # Plotly donut chart — one slice per country, gold color scheme

    # ── Recent activity feed ──
    st.subheader("Recent Activity")
    # Last 20 scrape runs across all countries
    # Show: timestamp | country flag | source | listings found | duration
```

### TAB 2: Countries (NEW — detailed per-country view)

```python
with tab_countries:
    # Country selector (tabs or dropdown)
    selected_country = st.selectbox("Select Country", countries)

    # ── Country header ──
    # Flag + name + total listings + last scraped

    # ── Sources breakdown ──
    st.subheader(f"Sources — {selected_country}")
    # Table: source slug | status (active/broken/disabled) | total listings | last run | avg listings/run
    # Color: green = working, red = broken, grey = disabled

    # For each source, show:
    # - Last scrape time
    # - Listings found in last run
    # - Error count (last 7 days)
    # - Success rate
    # - Button to run individual source scrape

    # ── Price distribution ──
    st.subheader("Price Distribution")
    # Histogram of listing prices for this country
    # Use plotly, gold color

    # ── Map view (if lat/lng available) ──
    # st.map() with listing locations for this country

    # ── Sample listings ──
    st.subheader("Latest Listings")
    # Show 10 most recent listings: title, price, location, source, enrichment status
    # Query:
    # SELECT title, price_jpy, location, source_slug, enrichment_status, created_at
    # FROM properties WHERE country = ? ORDER BY created_at DESC LIMIT 10
```

### TAB 3: AI Processing (NEW — the key tab you asked for!)

```python
with tab_ai:
    st.subheader("🤖 AI Processing Status")

    # ── Overall enrichment stats ──
    col1, col2, col3, col4, col5 = st.columns(5)
    # Total Enriched | Pending Translation | Pending Tags | Pending What-to-Know | Failed

    # Query:
    # SELECT
    #   COUNT(*) FILTER (WHERE enrichment_status = 'complete') as enriched,
    #   COUNT(*) FILTER (WHERE enrichment_status = 'pending') as pending,
    #   COUNT(*) FILTER (WHERE enrichment_status = 'failed') as failed,
    #   COUNT(*) FILTER (WHERE title_en IS NOT NULL) as translated,
    #   COUNT(*) FILTER (WHERE lifestyle_tags IS NOT NULL) as tagged,
    #   COUNT(*) FILTER (WHERE what_to_know IS NOT NULL) as has_wtk
    # FROM properties

    # ── Enrichment progress by country ──
    st.subheader("Enrichment by Country")
    # For each country: progress bar showing % enriched
    for country in countries:
        country_ai = get_country_ai_stats(country)
        total = country_ai['total']
        enriched = country_ai['enriched']
        pct = (enriched / total * 100) if total > 0 else 0
        st.progress(pct / 100, text=f"{COUNTRY_FLAGS[country]} {country}: {enriched}/{total} ({pct:.0f}%)")

    st.divider()

    # ── Pipeline stages breakdown ──
    st.subheader("Processing Pipeline")
    # Show each enrichment stage as a funnel:
    # Raw → Translated → Deduped → Hazard-checked → Tagged → What-to-Know → Published
    #
    # For each stage, show count of listings at that stage
    # Use plotly funnel chart

    stages_data = get_pipeline_stages()
    # stages_data = [
    #   {"stage": "Raw (scraped)", "count": 1500},
    #   {"stage": "Translated", "count": 1200},
    #   {"stage": "Deduplicated", "count": 980},
    #   {"stage": "Hazard checked", "count": 950},
    #   {"stage": "Lifestyle tagged", "count": 900},
    #   {"stage": "What-to-Know", "count": 850},
    #   {"stage": "Published", "count": 820},
    # ]
    import plotly.express as px
    fig = px.funnel(stages_data, x="count", y="stage",
                    color_discrete_sequence=["#C9A96E"])
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Recent AI processing log ──
    st.subheader("Recent AI Enrichments")
    # Show last 20 enriched listings with details:
    # timestamp | title | country | source | what was enriched (translation/tags/wtk)
    # Query:
    # SELECT title, title_en, country, source_slug, enrichment_status,
    #        lifestyle_tags, what_to_know IS NOT NULL as has_wtk,
    #        enriched_at
    # FROM properties
    # WHERE enriched_at IS NOT NULL
    # ORDER BY enriched_at DESC
    # LIMIT 20

    recent = get_recent_enrichments()
    if recent:
        for item in recent:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
            with col1:
                st.text(item['title_en'] or item['title'] or 'Untitled')
            with col2:
                st.text(COUNTRY_FLAGS.get(item['country'], '') + ' ' + (item['source_slug'] or ''))
            with col3:
                # Enrichment badges
                badges = []
                if item.get('title_en'):
                    badges.append("🌐")
                if item.get('lifestyle_tags'):
                    badges.append("🏷️")
                if item.get('has_wtk'):
                    badges.append("📝")
                st.text(' '.join(badges))
            with col4:
                st.text(str(item.get('enriched_at', ''))[:16])

    # ── Failed enrichments ──
    st.subheader("Failed Enrichments")
    # Show listings where enrichment_status = 'failed'
    # With error message and retry button
    failed = get_failed_enrichments()
    if failed:
        for item in failed:
            with st.expander(f"❌ {item['title'] or 'Untitled'} — {item['source_slug']}"):
                st.text(f"Error: {item.get('enrichment_error', 'Unknown')}")
                if st.button(f"Retry", key=f"retry_{item['id']}"):
                    # Reset to pending and re-enrich
                    pass
    else:
        st.success("No failed enrichments!")

    # ── LLM stats ──
    st.divider()
    st.subheader("Ollama LLM Stats")
    ollama = get_ollama_status()
    if ollama['running']:
        st.success(f"Ollama running — Models: {', '.join(ollama['models'])}")
        # Show enrichment speed: avg time per listing (from logs)
        # Show total tokens processed today (if tracked)
    else:
        st.error("Ollama is NOT running!")
        if st.button("Start Ollama"):
            import subprocess
            subprocess.Popen(["ollama", "serve"])
            import time
            time.sleep(3)
            st.rerun()
```

### TAB 4: Add URL (updated for multi-country)

```python
with tab_add_url:
    st.subheader("Add a Property URL")
    st.caption("Found a cool listing? Paste the URL — we detect the country and source automatically.")

    url_input = st.text_input("Property URL", placeholder="Paste any property URL from any supported country...")

    # Auto-detect source AND country from URL
    SOURCE_DETECTION = {
        # Japan
        "homes.co.jp": ("homes-co-jp", "japan"),
        "athome.co.jp": ("athome-co-jp", "japan"),
        "suumo.jp": ("suumo-jp", "japan"),
        "realestate.co.jp": ("realestate-co-jp", "japan"),
        "akiya-mart": ("akiya-mart", "japan"),
        "koryoya": ("koryoya", "japan"),
        "bukkenfan": ("bukkenfan", "japan"),
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

    # When URL is entered, show detected source + country
    if url_input:
        detected = None
        for domain, (source, country) in SOURCE_DETECTION.items():
            if domain in url_input:
                detected = (source, country)
                break
        if detected:
            flag = COUNTRY_FLAGS.get(detected[1], '')
            st.info(f"Detected: {flag} {detected[1].title()} → {detected[0]}")
        else:
            st.warning("Can't auto-detect. Select manually below.")

    # Manual override
    col1, col2 = st.columns(2)
    with col1:
        source_manual = st.selectbox("Source", ["auto"] + list(set(
            s for s, c in SOURCE_DETECTION.values()
        )))
    with col2:
        country_manual = st.selectbox("Country", ["auto", "japan", "france", "italy",
                                                     "portugal", "sweden", "usa", "new-zealand"])

    if st.button("Scrape This URL", type="primary"):
        # ... existing scrape logic but with country-aware detection
        pass
```

### TAB 5: Newsletter Import (updated)

Same as before but add URL patterns for all countries:

```python
# Extended URL patterns for newsletter extraction
NEWSLETTER_DOMAINS = [
    # Japan
    r'homes\.co\.jp', r'athome\.co\.jp', r'suumo\.jp', r'realestate\.co\.jp',
    r'akiya-mart\.com', r'koryoya\.com', r'bukkenfan\.jp',
    # Europe
    r'green-acres\.fr', r'immobilier\.notaires\.fr', r'gate-away\.com',
    r'italianhousesforsale\.com', r'immobiliare\.it', r'idealista\.pt',
    r'imovirtual\.com', r'hemnet\.se', r'blocket\.se',
    # USA
    r'cheapoldhouses\.com', r'redfin\.com', r'realtor\.com',
    r'landwatch\.com', r'auction\.com',
    # NZ
    r'trademe\.co\.nz', r'realestate\.co\.nz', r'homes\.co\.nz',
    r'oneroof\.co\.nz', r'harcourts\.co\.nz',
]
```

### Helper functions to add:

```python
# Country flags
COUNTRY_FLAGS = {
    "japan": "🇯🇵",
    "france": "🇫🇷",
    "italy": "🇮🇹",
    "portugal": "🇵🇹",
    "sweden": "🇸🇪",
    "usa": "🇺🇸",
    "new-zealand": "🇳🇿",
}

def get_country_stats(country: str) -> dict:
    """Get stats for a specific country."""
    from ingestion.db import execute

    rows = execute("""
        SELECT
            COUNT(*) FILTER (WHERE listing_status = 'active' OR listing_status IS NULL) as active,
            COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as today,
            COUNT(*) FILTER (WHERE enrichment_status = 'pending' OR enrichment_status IS NULL) as pending,
            COUNT(*) FILTER (WHERE enrichment_status = 'complete') as enriched
        FROM properties
        WHERE country = %s
    """, (country,))

    if rows:
        return dict(rows[0])
    return {'active': 0, 'today': 0, 'pending': 0, 'enriched': 0}


def get_country_ai_stats(country: str) -> dict:
    """Get AI enrichment stats for a country."""
    from ingestion.db import execute

    rows = execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE enrichment_status = 'complete') as enriched,
            COUNT(*) FILTER (WHERE enrichment_status = 'failed') as failed,
            COUNT(*) FILTER (WHERE title_en IS NOT NULL) as translated,
            COUNT(*) FILTER (WHERE lifestyle_tags IS NOT NULL) as tagged,
            COUNT(*) FILTER (WHERE what_to_know IS NOT NULL) as has_wtk
        FROM properties
        WHERE country = %s
    """, (country,))

    if rows:
        return dict(rows[0])
    return {'total': 0, 'enriched': 0, 'failed': 0, 'translated': 0, 'tagged': 0, 'has_wtk': 0}


def get_pipeline_stages() -> list:
    """Get counts at each pipeline stage."""
    from ingestion.db import execute

    rows = execute("""
        SELECT
            COUNT(*) as raw_total,
            COUNT(*) FILTER (WHERE title_en IS NOT NULL) as translated,
            COUNT(*) FILTER (WHERE is_duplicate = false OR is_duplicate IS NULL) as deduped,
            COUNT(*) FILTER (WHERE hazard_data IS NOT NULL) as hazard_checked,
            COUNT(*) FILTER (WHERE lifestyle_tags IS NOT NULL) as tagged,
            COUNT(*) FILTER (WHERE what_to_know IS NOT NULL) as has_wtk,
            COUNT(*) FILTER (WHERE enrichment_status = 'complete') as published
        FROM properties
    """)

    if not rows:
        return []

    r = rows[0]
    return [
        {"stage": "Raw (scraped)", "count": r['raw_total']},
        {"stage": "Translated", "count": r['translated']},
        {"stage": "Deduplicated", "count": r['deduped']},
        {"stage": "Hazard checked", "count": r['hazard_checked']},
        {"stage": "Lifestyle tagged", "count": r['tagged']},
        {"stage": "What-to-Know", "count": r['has_wtk']},
        {"stage": "Published", "count": r['published']},
    ]


def get_recent_enrichments(limit=20) -> list:
    """Get recently enriched listings."""
    from ingestion.db import execute

    return execute("""
        SELECT id, title, title_en, country, source_slug,
               enrichment_status, lifestyle_tags,
               what_to_know IS NOT NULL as has_wtk,
               enriched_at
        FROM properties
        WHERE enriched_at IS NOT NULL
        ORDER BY enriched_at DESC
        LIMIT %s
    """, (limit,))


def get_failed_enrichments(limit=20) -> list:
    """Get listings where enrichment failed."""
    from ingestion.db import execute

    return execute("""
        SELECT id, title, source_slug, country,
               enrichment_error, enrichment_status
        FROM properties
        WHERE enrichment_status = 'failed'
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))
```

### Database: Make sure these columns exist

Run these SQL migrations before deploying the dashboard:

```sql
-- Country support
ALTER TABLE properties ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'japan';
CREATE INDEX IF NOT EXISTS idx_properties_country ON properties(country);

-- Enrichment tracking
ALTER TABLE properties ADD COLUMN IF NOT EXISTS enrichment_status TEXT DEFAULT 'pending';
-- Values: 'pending', 'in_progress', 'complete', 'failed'
ALTER TABLE properties ADD COLUMN IF NOT EXISTS enrichment_error TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMPTZ;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS title_en TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS lifestyle_tags JSONB;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS what_to_know TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS hazard_data JSONB;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT false;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS listing_status TEXT DEFAULT 'active';

CREATE INDEX IF NOT EXISTS idx_properties_enrichment ON properties(enrichment_status);
CREATE INDEX IF NOT EXISTS idx_properties_country_status ON properties(country, listing_status);
```

### Same dark theme — keep the CheapHouse brand:

```python
st.markdown("""
<style>
    .stApp { background-color: #0a0a0c; }
    .stMetric { background-color: #111115; padding: 16px; border-radius: 8px; border: 1px solid #1a1a20; }
    .stMetricValue { color: #C9A96E; }
    .stProgress .st-bo { background-color: #C9A96E; }
    .stTabs [data-baseweb="tab"] { color: #888; }
    .stTabs [aria-selected="true"] { color: #C9A96E; border-bottom-color: #C9A96E; }
    code { color: #e0e0e0 !important; }
    h1, h2, h3 { color: #f0f0f0; }
</style>
""", unsafe_allow_html=True)
```

## After building

```bash
cd "/Users/test/Documents/CheapHouse Japan/ingestion"
source venv/bin/activate
pip install streamlit plotly
streamlit run dashboard.py
```

Verify:
1. Overview tab shows country cards (mostly 0 for new countries — that's fine)
2. Countries tab lets you drill into each country
3. AI Processing tab shows enrichment funnel
4. Add URL detects URLs from all supported countries
5. Dark theme with gold accents

Push to GitHub.
```
