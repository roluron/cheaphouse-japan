-- CheapHouse Japan — Database Schema
-- Run this against your Supabase/Postgres database to set up all tables.
-- Designed for MVP: simple, no PostGIS dependency, admin-review-first workflow.

-- ══════════════════════════════════════════════════════════
-- SOURCES: registry of websites we scrape from
-- ══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    base_url        TEXT NOT NULL,
    source_type     TEXT NOT NULL DEFAULT 'website',
    listing_url_pattern TEXT,
    detail_url_pattern  TEXT,
    scrape_method   TEXT NOT NULL DEFAULT 'http',
    refresh_hours   INT NOT NULL DEFAULT 24,
    parser_status   TEXT NOT NULL DEFAULT 'active',
    robots_notes    TEXT,
    legal_notes     TEXT,
    field_mapping   JSONB,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_run_at     TIMESTAMPTZ,
    last_run_status TEXT,
    last_run_count  INT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ══════════════════════════════════════════════════════════
-- RAW LISTINGS: exactly what the scraper extracted, untouched
-- ══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS raw_listings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_slug         TEXT NOT NULL,
    source_listing_id   TEXT NOT NULL,
    source_url          TEXT NOT NULL,
    title               TEXT,
    description         TEXT,
    price_raw           TEXT,
    price_jpy           INT,
    prefecture          TEXT,
    city                TEXT,
    address_raw         TEXT,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    land_sqm            DOUBLE PRECISION,
    building_sqm        DOUBLE PRECISION,
    year_built          INT,
    building_type       TEXT,
    structure           TEXT,
    rooms               TEXT,
    floors              INT,
    condition_notes     TEXT,
    nearest_station     TEXT,
    station_distance    TEXT,
    image_urls          TEXT[],
    raw_data            JSONB,
    fetched_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    processing_status   TEXT DEFAULT 'pending',
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now(),
    UNIQUE(source_slug, source_listing_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_listings_status ON raw_listings(processing_status);
CREATE INDEX IF NOT EXISTS idx_raw_listings_source ON raw_listings(source_slug);

-- ══════════════════════════════════════════════════════════
-- PROPERTIES: normalized, enriched, publishable listings
-- ══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS properties (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source attribution
    primary_source_slug TEXT,
    source_listing_ids  JSONB,
    original_url        TEXT NOT NULL,
    canonical_url       TEXT,

    -- Titles and descriptions
    original_title      TEXT,
    title_en            TEXT,
    original_description TEXT,
    summary_en          TEXT,

    -- Price
    price_jpy           INT,
    price_usd           INT,
    price_display       TEXT,

    -- Location
    prefecture          TEXT,
    city                TEXT,
    address_text        TEXT,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    region              TEXT,

    -- Property details
    land_sqm            DOUBLE PRECISION,
    building_sqm        DOUBLE PRECISION,
    year_built          INT,
    building_type       TEXT,
    structure           TEXT,
    floors              INT,
    rooms               TEXT,

    -- Condition
    condition_rating    TEXT,
    condition_notes     TEXT,
    renovation_notes    TEXT,
    renovation_estimate TEXT,

    -- Access
    nearest_station     TEXT,
    station_distance    TEXT,
    transport_notes     TEXT,

    -- Images (JSON array of {url, caption, order})
    images              JSONB DEFAULT '[]'::jsonb,
    thumbnail_url       TEXT,

    -- Hazard data (JSON object, see architecture doc Section G)
    hazard_scores       JSONB DEFAULT '{}'::jsonb,

    -- Lifestyle tags (JSON array of {tag, confidence, reasons, method})
    lifestyle_tags      JSONB DEFAULT '[]'::jsonb,

    -- What to know (honesty section)
    whats_attractive    TEXT[],
    whats_unclear       TEXT[],
    whats_risky         TEXT[],
    what_to_verify      TEXT[],

    -- Match prep
    match_attributes    JSONB DEFAULT '{}'::jsonb,

    -- Quality and status
    quality_score       DOUBLE PRECISION DEFAULT 0,
    listing_status      TEXT DEFAULT 'draft',
    admin_status        TEXT DEFAULT 'pending_review',
    admin_notes         TEXT,

    -- Freshness
    first_seen_at       TIMESTAMPTZ DEFAULT now(),
    last_seen_at        TIMESTAMPTZ DEFAULT now(),
    last_checked_at     TIMESTAMPTZ DEFAULT now(),
    gone_since          TIMESTAMPTZ,
    freshness_label     TEXT DEFAULT 'new',

    -- Deduplication
    dedupe_fingerprint  TEXT,
    merged_from         UUID[],

    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_properties_prefecture ON properties(prefecture);
CREATE INDEX IF NOT EXISTS idx_properties_status ON properties(listing_status);
CREATE INDEX IF NOT EXISTS idx_properties_admin ON properties(admin_status);
CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price_jpy);
CREATE INDEX IF NOT EXISTS idx_properties_freshness ON properties(freshness_label);
CREATE INDEX IF NOT EXISTS idx_properties_dedupe ON properties(dedupe_fingerprint);

-- ══════════════════════════════════════════════════════════
-- SCRAPE RUNS: log of each scraper execution
-- ══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS scrape_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_slug     TEXT NOT NULL,
    status          TEXT NOT NULL,
    listings_found  INT DEFAULT 0,
    listings_new    INT DEFAULT 0,
    errors          INT DEFAULT 0,
    duration_ms     INT DEFAULT 0,
    error_log       TEXT,
    run_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scrape_runs_source ON scrape_runs(source_slug);

-- ══════════════════════════════════════════════════════════
-- ADMIN REVIEW QUEUE (view for convenience)
-- ══════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW admin_review_queue AS
SELECT
    id,
    title_en,
    original_title,
    prefecture,
    city,
    price_jpy,
    price_display,
    quality_score,
    hazard_scores,
    lifestyle_tags,
    admin_status,
    listing_status,
    freshness_label,
    original_url,
    created_at
FROM properties
WHERE admin_status = 'pending_review'
ORDER BY quality_score DESC, created_at DESC;
