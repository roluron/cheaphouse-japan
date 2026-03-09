#!/usr/bin/env python3
"""Generate CheapHouse Japan Walkthrough PDF"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Brand colors
GOLD = HexColor("#C9A96E")
DARK_BG = HexColor("#0a0a0c")
DARK_CARD = HexColor("#111115")
MUTED = HexColor("#8e8e93")
TEXT = HexColor("#2a2a2a")
LIGHT_BG = HexColor("#fafafa")
GREEN = HexColor("#34C759")
AMBER = HexColor("#FF9F0A")
RED = HexColor("#FF453A")
BLUE = HexColor("#5B9BD5")

# Page setup
WIDTH, HEIGHT = A4
MARGIN = 2 * cm

def build_pdf():
    output_path = "/sessions/magical-trusting-fermi/mnt/CheapHouse Japan/CheapHouse_Japan_Walkthrough.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=28, leading=34, textColor=DARK_BG,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=13, leading=18, textColor=MUTED,
        spaceAfter=24,
    )

    heading_style = ParagraphStyle(
        'H1', parent=styles['Heading1'],
        fontSize=18, leading=24, textColor=DARK_BG,
        spaceBefore=20, spaceAfter=10,
        borderColor=GOLD, borderWidth=0,
    )

    heading2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=14, leading=18, textColor=HexColor("#333333"),
        spaceBefore=14, spaceAfter=6,
    )

    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10.5, leading=16, textColor=TEXT,
        spaceAfter=8,
    )

    code_style = ParagraphStyle(
        'Code', parent=styles['Code'],
        fontSize=9, leading=13, textColor=HexColor("#1a1a1a"),
        backColor=HexColor("#f0f0f0"),
        borderColor=HexColor("#ddd"), borderWidth=0.5,
        borderPadding=8, leftIndent=12,
        spaceAfter=10,
    )

    bullet_style = ParagraphStyle(
        'Bullet', parent=body_style,
        leftIndent=20, bulletIndent=8,
        spaceBefore=2, spaceAfter=2,
    )

    gold_label = ParagraphStyle(
        'GoldLabel', parent=styles['Normal'],
        fontSize=9, leading=12, textColor=GOLD,
        spaceBefore=2, spaceAfter=2,
        fontName='Helvetica-Bold',
    )

    note_style = ParagraphStyle(
        'Note', parent=body_style,
        fontSize=9.5, leading=14, textColor=HexColor("#555"),
        backColor=HexColor("#f8f6f0"),
        borderColor=GOLD, borderWidth=1,
        borderPadding=10, leftIndent=0,
        spaceBefore=8, spaceAfter=12,
    )

    story = []

    # ══════════════════════════════════════════════
    # PAGE 1: COVER
    # ══════════════════════════════════════════════
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("CheapHouse Japan", title_style))
    story.append(Paragraph("Setup & Operations Walkthrough", subtitle_style))
    story.append(HRFlowable(width="40%", thickness=2, color=GOLD, spaceAfter=20))
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph("What this document covers:", heading2_style))
    items = [
        "Architecture overview (what runs where)",
        "How the automatic pipeline works",
        "Dashboard usage (monitor, add URLs, import newsletters)",
        "Prompt order for Antigravity",
        "Troubleshooting common issues",
        "European expansion sites for future scraping",
    ]
    for item in items:
        story.append(Paragraph(f"\u2022  {item}", bullet_style))

    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("March 2026", ParagraphStyle('DateStyle', parent=body_style, textColor=MUTED, fontSize=10)))
    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # PAGE 2: ARCHITECTURE
    # ══════════════════════════════════════════════
    story.append(Paragraph("1. Architecture", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))

    story.append(Paragraph(
        "CheapHouse Japan runs on three layers. Your Mac Mini is the engine, "
        "Supabase is the database, and Vercel serves the website.",
        body_style
    ))

    # Architecture table
    arch_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Where</b>", body_style), Paragraph("<b>What it does</b>", body_style)],
        [Paragraph("Scrapers", body_style), Paragraph("Mac Mini", body_style), Paragraph("Crawl 10 Japanese property sites daily", body_style)],
        [Paragraph("Ollama LLM", body_style), Paragraph("Mac Mini", body_style), Paragraph("Translate, tag, generate What-to-Know (free)", body_style)],
        [Paragraph("Freshness checker", body_style), Paragraph("Mac Mini", body_style), Paragraph("Detect sold/removed listings daily", body_style)],
        [Paragraph("Cron scheduler", body_style), Paragraph("Mac Mini", body_style), Paragraph("3 AM: full pipeline / 2 PM: freshness check", body_style)],
        [Paragraph("Dashboard", body_style), Paragraph("Mac Mini", body_style), Paragraph("http://localhost:8501 (Streamlit)", body_style)],
        [Paragraph("Database", body_style), Paragraph("Supabase", body_style), Paragraph("PostgreSQL + Auth + API", body_style)],
        [Paragraph("Website", body_style), Paragraph("Vercel", body_style), Paragraph("Next.js 16, reads from Supabase", body_style)],
    ]

    arch_table = Table(arch_data, colWidths=[3*cm, 3*cm, 9*cm])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f8f8f8")]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph(
        "The key insight: once set up, <b>everything is automatic</b>. The Mac Mini scrapes, "
        "enriches, and pushes to Supabase. Vercel picks it up instantly. You do nothing.",
        note_style
    ))

    # ══════════════════════════════════════════════
    # PIPELINE FLOW
    # ══════════════════════════════════════════════
    story.append(Paragraph("2. Daily Pipeline Flow", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))

    story.append(Paragraph("Every day at 3 AM, your Mac Mini runs this sequence automatically:", body_style))

    steps = [
        ("SCRAPE", "Crawl 10 sites (homes.co.jp, athome, suumo, akiya-mart, koryoya, heritage-homes, eikohome, bukkenfan, realestate.co.jp, all-akiyas). ~1,500 listings per run."),
        ("NORMALIZE", "Clean data, standardize formats, parse Japanese prices/dates/areas."),
        ("TRANSLATE", "Japanese to English via Ollama qwen2.5:14b (local, free). ~5 sec/listing."),
        ("DEDUPLICATE", "Fingerprint matching to avoid duplicate properties across sources."),
        ("HAZARD ENRICH", "Add flood/landslide/tsunami risk scores per prefecture."),
        ("LIFESTYLE TAG", "Rule-based + LLM tags: rural-retreat, pet-friendly, near-station, etc."),
        ("QUALITY SCORE", "13-check data completeness score (0 to 1)."),
        ("WHAT-TO-KNOW", "LLM generates honest reports: attractive, unclear, risky, verify."),
    ]

    for i, (label, desc) in enumerate(steps, 1):
        story.append(Paragraph(f"<b>{i}. {label}</b>", gold_label))
        story.append(Paragraph(desc, bullet_style))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("At 2 PM, a separate freshness check runs:", body_style))
    story.append(Paragraph(f"\u2022  Visits every listing's source URL", bullet_style))
    story.append(Paragraph(f"\u2022  Detects 404s, \"sold\" patterns in Japanese/English", bullet_style))
    story.append(Paragraph(f"\u2022  Marks sold/removed listings (they disappear from the site)", bullet_style))

    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # SOURCES
    # ══════════════════════════════════════════════
    story.append(Paragraph("3. Active Scraper Sources", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))

    sources_data = [
        [Paragraph("<b>Source</b>", body_style), Paragraph("<b>Type</b>", body_style), Paragraph("<b>Status</b>", body_style), Paragraph("<b>Notes</b>", body_style)],
        ["koryoya", "Curated", "Working", "Pre-1950 kominka specialist"],
        ["heritage-homes", "Curated", "Working", "Kyoto machiya + kominka"],
        ["bukkenfan", "Curated", "Bug fix needed", "Price parsing crash on Japanese format"],
        ["eikohome", "Curated", "Working", "Nara specialist, rural houses"],
        ["homes-co-jp", "Major portal", "Working", "LIFULL HOME'S, nationwide"],
        ["athome-co-jp", "Major portal", "Working", "Good rural coverage"],
        ["suumo-jp", "Major portal", "Careful", "Largest portal, anti-scraping (5s delay)"],
        ["realestate-co-jp", "English portal", "Fix needed", "CSS selectors need update"],
        ["akiya-mart", "Aggregator", "Working", "680K+ listings, links to source"],
        ["all-akiyas", "Aggregator", "Fallback", "No individual listing URLs"],
    ]

    for i in range(1, len(sources_data)):
        sources_data[i] = [Paragraph(str(c), body_style) for c in sources_data[i]]

    src_table = Table(sources_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 7*cm])
    src_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f8f8f8")]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(src_table)

    # ══════════════════════════════════════════════
    # PROMPT ORDER
    # ══════════════════════════════════════════════
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("4. Antigravity Prompt Order", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))

    story.append(Paragraph("Copy-paste these prompts into Antigravity in this exact order:", body_style))

    prompts = [
        ("PROMPT_FIX_SCRAPER_BUGS.md", "Fix bukkenfan price parsing + realestate.co.jp selectors", "Priority"),
        ("PROMPT_DESIGN_RISK_SIGNALS.md", "Risk dots on cards + freshness checker + safety filter", "Priority"),
        ("PROMPT_DASHBOARD_MAC.md", "Streamlit dashboard + single URL scrape + newsletter import", "Priority"),
        ("PROMPT_OLLAMA_LOCAL_LLM.md", "Already applied - switch pipeline to Ollama", "Done"),
        ("PROMPT_REAL_JAPANESE_SCRAPERS.md", "Already applied - direct Japanese site scrapers", "Done"),
        ("PROMPT_SCRAPERS_ATHOME_SUUMO.md", "Already applied - athome + suumo adapters", "Done"),
        ("PROMPT_AUTO_PIPELINE_CRON.md", "Already applied - cron automation", "Done"),
        ("PROMPT_LYBOX_FEATURES.md", "Cost calculator, renovation estimator, area analysis", "Next"),
        ("PROMPT_MULTI_COUNTRY.md", "Country selector + Coming Soon + waitlist", "Next"),
        ("Auth + Quiz + Stripe", "Login, matching quiz, subscription paywall", "Later"),
    ]

    prompt_data = [[Paragraph("<b>Prompt</b>", body_style), Paragraph("<b>What it does</b>", body_style), Paragraph("<b>Status</b>", body_style)]]
    for name, desc, status in prompts:
        color = "#34C759" if status == "Done" else "#FF9F0A" if status == "Priority" else "#5B9BD5"
        prompt_data.append([
            Paragraph(f"<font size=8>{name}</font>", body_style),
            Paragraph(f"<font size=8>{desc}</font>", body_style),
            Paragraph(f'<font size=8 color="{color}"><b>{status}</b></font>', body_style),
        ])

    p_table = Table(prompt_data, colWidths=[5.5*cm, 7*cm, 2.5*cm])
    p_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f8f8f8")]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(p_table)

    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════
    story.append(Paragraph("5. Dashboard Usage", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))

    story.append(Paragraph("After running PROMPT_DASHBOARD_MAC.md in Antigravity, your dashboard lives at:", body_style))
    story.append(Paragraph("<b>http://localhost:8501</b>", ParagraphStyle('URL', parent=body_style, fontSize=14, textColor=GOLD)))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("<b>Overview tab</b> - Real-time stats: active listings, added today/this week, sold count, pending enrichment. Bar chart by source. Recent scrape run history.", body_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("<b>Add URL tab</b> - Found a cool listing? Paste the URL. Auto-detects source (homes.co.jp, athome, suumo...). Batch mode: paste multiple URLs, one per line.", body_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("<b>Newsletter Import tab</b> - Paste a CheapHouse Japan newsletter (HTML or text). It extracts all property URLs and scrapes them automatically.", body_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("<b>Logs tab</b> - View pipeline logs. See cron schedule. Debug issues.", body_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("<b>Sidebar</b> - One-click buttons: Run Full Pipeline, Scrape Only, Enrich Only, Freshness Check. Ollama + Cron status indicators.", body_style))

    # ══════════════════════════════════════════════
    # TROUBLESHOOTING
    # ══════════════════════════════════════════════
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("6. Troubleshooting", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))

    issues = [
        ("Pipeline didn't run last night", "Check: <b>crontab -l</b> (cron installed?), Mac Mini awake? (<b>sudo pmset -a disablesleep 1</b>), check logs in ingestion/logs/"),
        ("Ollama not responding", "Run: <b>ollama serve</b> or <b>bash setup_ollama_autostart.sh</b>. Verify: <b>curl http://localhost:11434/api/tags</b>"),
        ("Suumo blocked (403)", "Normal. It stops gracefully and retries next run. Never force it. Max 150 listings/run."),
        ("Listings still showing as 'analysis pending'", "The enrich pipeline hasn't run yet. Run: <b>python auto_pipeline.py --enrich</b>"),
        ("New listings not on website", "Check Supabase has the data. Check Vercel is connected. Force redeploy on Vercel if needed."),
        ("Dashboard won't start", "Run: <b>pip install streamlit plotly</b> in the venv, then <b>streamlit run dashboard.py</b>"),
        ("'command not found: python'", "Always activate venv first: <b>source venv/bin/activate</b>"),
    ]

    for problem, solution in issues:
        story.append(Paragraph(f"<b>{problem}</b>", heading2_style))
        story.append(Paragraph(solution, body_style))

    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # ESSENTIAL COMMANDS
    # ══════════════════════════════════════════════
    story.append(Paragraph("7. Essential Commands", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))

    story.append(Paragraph("All commands from the ingestion directory:", body_style))
    story.append(Paragraph('<font face="Courier" size=8>cd "/Users/test/Documents/CheapHouse Japan/ingestion" &amp;&amp; source venv/bin/activate</font>', code_style))

    commands = [
        ("Run full pipeline (scrape + enrich + freshness)", "python auto_pipeline.py"),
        ("Scrape only", "python auto_pipeline.py --scrape"),
        ("Enrich only (translate + tags + what-to-know)", "python auto_pipeline.py --enrich"),
        ("Freshness check only", "python auto_pipeline.py --freshness"),
        ("Scrape one source", "python run.py scrape --source homes-co-jp --limit 100"),
        ("Test an adapter", "python run.py test-adapter suumo-jp --limit 3"),
        ("Check system health", "python status.py"),
        ("Check cron", "crontab -l"),
        ("View last log", "cat logs/pipeline_*.log | tail -50"),
        ("Start dashboard", "streamlit run dashboard.py"),
    ]

    cmd_data = [[Paragraph("<b>Action</b>", body_style), Paragraph("<b>Command</b>", body_style)]]
    for action, cmd in commands:
        cmd_data.append([
            Paragraph(f"<font size=8.5>{action}</font>", body_style),
            Paragraph(f'<font face="Courier" size=8>{cmd}</font>', body_style),
        ])

    cmd_table = Table(cmd_data, colWidths=[7*cm, 8*cm])
    cmd_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f8f8f8")]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(cmd_table)

    # ══════════════════════════════════════════════
    # EUROPEAN EXPANSION
    # ══════════════════════════════════════════════
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("8. European Expansion - Target Sites", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))

    story.append(Paragraph(
        "For the multi-country vision, these are the top sites to scrape per country. "
        "Curated sites first (smaller, easier), major portals second (volume).",
        body_style
    ))

    story.append(Paragraph("Curated / Affordable Specialists", heading2_style))

    curated_eu = [
        [Paragraph("<b>Site</b>", body_style), Paragraph("<b>Country</b>", body_style), Paragraph("<b>Why</b>", body_style), Paragraph("<b>Difficulty</b>", body_style)],
        ["cheappropertyitaly.com", "Italy", "Budget rural houses, renovation projects", "Easy"],
        ["italianhousesforsale.net", "Italy", "Village houses, low-cost listings", "Easy"],
        ["bargainhomesabroad.com", "EU-wide", "Curated affordable fixer-uppers across EU", "Easy"],
        ["historicalhomesofeurope.com", "EU-wide", "Unique/historic affordable homes", "Easy"],
        ["frenchpropertynews.com", "France", "Budget-friendly renovation properties", "Medium"],
        ["anewlifeininfrance.com", "France", "Rural, cheap properties", "Medium"],
    ]
    for i in range(1, len(curated_eu)):
        curated_eu[i] = [Paragraph(f"<font size=8>{c}</font>", body_style) for c in curated_eu[i]]

    eu_table1 = Table(curated_eu, colWidths=[4.5*cm, 2.5*cm, 5.5*cm, 2.5*cm])
    eu_table1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f8f8f8")]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(eu_table1)

    story.append(Paragraph("Major Portals (High Volume)", heading2_style))

    major_eu = [
        [Paragraph("<b>Site</b>", body_style), Paragraph("<b>Country</b>", body_style), Paragraph("<b>Why</b>", body_style), Paragraph("<b>Difficulty</b>", body_style)],
        ["idealista.com", "ES / IT / PT", "Best for cheap/repossessed in Southern Europe", "Hard"],
        ["immobiliare.it", "Italy", "Italy's #1 portal, filter by low price", "Hard"],
        ["leboncoin.fr", "France", "Direct-from-owner, very cheap rural listings", "Hard"],
        ["seloger.com", "France", "Major French portal", "Hard"],
        ["funda.nl", "Netherlands", "Largest Dutch site, bargains in rural areas", "Medium"],
        ["immobilienscout24.de", "Germany", "Germany's main portal", "Hard"],
        ["finn.no", "Norway", "Norway's main real estate site", "Medium"],
    ]
    for i in range(1, len(major_eu)):
        major_eu[i] = [Paragraph(f"<font size=8>{c}</font>", body_style) for c in major_eu[i]]

    eu_table2 = Table(major_eu, colWidths=[4.5*cm, 2.5*cm, 5.5*cm, 2.5*cm])
    eu_table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f8f8f8")]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(eu_table2)

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>Recommended approach:</b> Start with the curated sites (easy scraping, English content, "
        "small volume). Then tackle the major portals one country at a time. Each portal needs its "
        "own adapter with country-specific price/date parsing, like we did for Japanese sites. "
        "You can run a second Antigravity window in parallel to build European scrapers while the "
        "Japanese pipeline is already running.",
        note_style
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════
    # COSTS + FINAL
    # ══════════════════════════════════════════════
    story.append(Paragraph("9. Running Costs", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=12))

    costs_data = [
        [Paragraph("<b>Item</b>", body_style), Paragraph("<b>Cost</b>", body_style), Paragraph("<b>Notes</b>", body_style)],
        ["Scraping", "$0", "Runs on your Mac Mini"],
        ["LLM enrichment (Ollama)", "$0", "Local model, no API calls"],
        ["Supabase (free tier)", "$0", "Up to 500MB DB, 50K auth users"],
        ["Vercel (hobby)", "$0", "Free for personal projects"],
        ["Domain (optional)", "~$12/year", "Custom domain for the site"],
        ["Supabase Pro (if needed)", "$25/month", "Only if you exceed free tier limits"],
    ]
    for i in range(1, len(costs_data)):
        costs_data[i] = [Paragraph(f"<font size=9>{c}</font>", body_style) for c in costs_data[i]]

    costs_table = Table(costs_data, colWidths=[4.5*cm, 3*cm, 7.5*cm])
    costs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#f8f8f8")]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#ddd")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(costs_table)

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "<b>Total MVP cost: $0/month.</b> When you add Stripe subscriptions at $10/month per user, "
        "your first paying customer covers all costs with room to spare.",
        note_style
    ))

    story.append(Spacer(1, 1.5 * cm))
    story.append(HRFlowable(width="60%", thickness=2, color=GOLD, spaceAfter=16))
    story.append(Paragraph(
        "CheapHouse Japan - Built with Claude + Antigravity",
        ParagraphStyle('Footer', parent=body_style, alignment=TA_CENTER, textColor=MUTED, fontSize=9)
    ))

    # Build
    doc.build(story)
    print(f"PDF created: {output_path}")


if __name__ == "__main__":
    build_pdf()
