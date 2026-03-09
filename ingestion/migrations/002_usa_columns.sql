-- USA expansion: add country and US-specific columns to raw_listings
-- Run against Supabase/Postgres database.

-- Ensure country column exists
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'japan';

-- USA adapters should set country = 'usa'
-- Add US-specific fields
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS property_tax_annual INTEGER;
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS hoa_monthly INTEGER;
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS lot_size_acres FLOAT;

-- Also add country to properties table
ALTER TABLE properties ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'japan';
