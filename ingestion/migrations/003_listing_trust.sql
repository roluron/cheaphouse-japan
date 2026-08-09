ALTER TABLE properties ADD COLUMN IF NOT EXISTS status_checked_at TIMESTAMPTZ;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS check_error_count INT DEFAULT 0;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS status_reason TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMPTZ;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS gone_since TIMESTAMPTZ;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS freshness_label TEXT DEFAULT 'unconfirmed';

ALTER TABLE properties DROP CONSTRAINT IF EXISTS properties_listing_status_check;
ALTER TABLE properties
    ADD CONSTRAINT properties_listing_status_check
    CHECK (listing_status IN ('draft', 'active', 'uncertain', 'sold', 'removed'))
    NOT VALID;

CREATE INDEX IF NOT EXISTS idx_properties_verified_active
    ON properties(last_checked_at DESC)
    WHERE listing_status = 'active';
