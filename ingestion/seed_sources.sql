-- CheapHouse Japan — Seed Data: Initial Sources
-- Run after schema.sql to populate the source registry.

INSERT INTO sources (name, slug, base_url, source_type, scrape_method, refresh_hours, robots_notes, legal_notes, is_active)
VALUES
    (
        'Cheap Houses Japan',
        'cheap-houses-japan',
        'https://cheaphousesjapan.com',
        'website',
        'http',
        24,
        'Check robots.txt before scraping',
        'Public listings. Attribution required. Link back to original listing.',
        true
    ),
    (
        'Akiya Mart',
        'akiya-mart',
        'https://akiya-mart.com',
        'website',
        'http',
        24,
        'Check robots.txt before scraping',
        'Public listings. Attribution required.',
        false  -- inactive until adapter is built
    ),
    (
        'Old Houses Japan',
        'old-houses-japan',
        'https://oldhousesjapan.com',
        'website',
        'http',
        48,
        'Check robots.txt before scraping',
        'Public listings. Attribution required.',
        false
    ),
    (
        'All Akiyas',
        'all-akiyas',
        'https://allakiyas.com',
        'website',
        'http',
        24,
        'Check robots.txt before scraping',
        'Public listings. Attribution required.',
        false
    ),
    (
        'Cheap Japan Homes',
        'cheap-japan-homes',
        'https://cheapjapanhomes.com',
        'website',
        'http',
        24,
        'Check robots.txt before scraping',
        'Public listings. Attribution required.',
        false
    )
ON CONFLICT (slug) DO NOTHING;
