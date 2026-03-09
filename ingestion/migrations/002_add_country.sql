-- Migration 002: Add country column for multi-country expansion
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'japan';
CREATE INDEX IF NOT EXISTS idx_raw_listings_country ON raw_listings(country);

-- Also add to properties table
ALTER TABLE properties ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'japan';
CREATE INDEX IF NOT EXISTS idx_properties_country ON properties(country);
