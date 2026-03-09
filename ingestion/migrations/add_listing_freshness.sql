-- Listing freshness tracking
-- Run this in the Supabase SQL editor

ALTER TABLE properties ADD COLUMN IF NOT EXISTS listing_status TEXT DEFAULT 'active'
    CHECK (listing_status IN ('active', 'sold', 'removed'));
ALTER TABLE properties ADD COLUMN IF NOT EXISTS status_checked_at TIMESTAMPTZ;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS check_error_count INT DEFAULT 0;

-- Index for quick filtering
CREATE INDEX IF NOT EXISTS idx_properties_listing_status ON properties(listing_status);
