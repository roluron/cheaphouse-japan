-- CheapHouse Japan — Seed Data: Initial Sources
-- Run after schema.sql to populate the source registry.

INSERT INTO sources (name, slug, base_url, source_type, scrape_method, refresh_hours, robots_notes, legal_notes, is_active)
VALUES
    -- Direct Japanese real estate portals (priority sources)
    (
        'LIFULL HOMES',
        'homes-co-jp',
        'https://www.homes.co.jp',
        'website',
        'http',
        24,
        'robots.txt allows /kodate/ scraping. Only /kksearch is disallowed.',
        'Public listings. Direct source URLs. Japanese language — translated via pipeline.',
        true
    ),
    (
        'at home',
        'athome-co-jp',
        'https://www.athome.co.jp',
        'website',
        'http',
        24,
        'Check robots.txt. Polite 3s delay between requests.',
        'Public listings. Direct source URLs. Good rural coverage. Japanese language.',
        true
    ),
    (
        'Real Estate Japan',
        'realestate-co-jp',
        'https://realestate.co.jp',
        'website',
        'http',
        24,
        'Check robots.txt. English-language portal.',
        'Public listings. Already in English. Targets international buyers.',
        true
    ),

    -- Fallback / aggregator sources (lower priority)
    (
        'All Akiyas',
        'all-akiyas',
        'https://allakiyas.com',
        'website',
        'http',
        48,
        'Check robots.txt before scraping',
        'Aggregator — links to original listings. Lower priority fallback.',
        false
    ),
    (
        'Suumo',
        'suumo-jp',
        'https://suumo.jp',
        'website',
        'http',
        48,
        'AGGRESSIVE anti-scraping. 5s+ delay, max 200 req/run. Residential IP only.',
        'Largest Japanese portal. Cautious scraping — 48h refresh. Run from Mac Mini.',
        true
    ),
    (
        'Eikoh Home',
        'eikohome',
        'https://www.eikohome.co.jp',
        'website',
        'http',
        168,
        'Small static site, very light load. Weekly refresh is sufficient.',
        'Nara prefecture specialist. Small curated inventory of rural houses. Static HTML.',
        true
    ),
    (
        'KORYOYA',
        'koryoya',
        'https://koryoya.com',
        'website',
        'http',
        168,
        'Small static site, ~5 listings. Weekly refresh.',
        'Pre-1950 traditional kominka specialist. English. Very curated.',
        true
    ),
    (
        'Heritage Homes Japan',
        'heritage-homes',
        'https://heritagehomesjapan.com',
        'website',
        'http',
        168,
        'WordPress site, ~20 listings. Weekly refresh.',
        'Kyoto machiya and kominka renovation specialist. English. Premium listings.',
        true
    ),
    (
        'Bukkenfan',
        'bukkenfan',
        'https://bukkenfan.jp',
        'website',
        'http',
        24,
        'JSON API at /entries.json. Polite 2s delay.',
        'Curated design-conscious property blog. For-sale listings only. Source URLs to agencies.',
        true
    ),
    (
        'Akiya Mart',
        'akiya-mart',
        'https://akiya-mart.com',
        'website',
        'http',
        24,
        'JSON API at /listings/id/{id}. 680K+ listings. Limit to 500/run.',
        'English aggregator. Source URLs point to original JP portals (suumo, athome).',
        true
    )
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    base_url = EXCLUDED.base_url,
    is_active = EXCLUDED.is_active,
    robots_notes = EXCLUDED.robots_notes,
    legal_notes = EXCLUDED.legal_notes;

-- Deactivate deprecated middleman sources
UPDATE sources SET
    is_active = false,
    legal_notes = 'Deprecated: middleman site, not original source. Replaced by direct Japanese portal scrapers.'
WHERE slug IN ('old-houses-japan', 'cheap-houses-japan', 'cheap-japan-homes');
