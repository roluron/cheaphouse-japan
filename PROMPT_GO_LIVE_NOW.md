# PROMPT À COLLER DANS ANTIGRAVITY — Pousser les vrais listings en ligne MAINTENANT

```
Auto-approve all changes and commands. Don't ask for permission.

## SITUATION

We have 2125 scraped listings and 1125 enriched by Ollama in Supabase. But the website shows NOTHING — it falls back to mock data every time. The frontend requires 3 flags that the pipeline NEVER sets:

```js
.eq("is_published", true)
.eq("admin_status", "approved")
.eq("listing_status", "active")
```

The scrapers don't set `is_published` or `admin_status`. So the query returns 0 results and the frontend shows mock data. Fix this NOW.

## FIX 1: Database — Set the missing flags on ALL existing listings

Run these SQL commands via the Supabase dashboard or psycopg2:

```sql
-- Add columns if they don't exist
ALTER TABLE properties ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT true;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS admin_status TEXT DEFAULT 'approved';
ALTER TABLE properties ADD COLUMN IF NOT EXISTS listing_status TEXT DEFAULT 'active';

-- Set flags on ALL existing listings
UPDATE properties SET is_published = true WHERE is_published IS NULL OR is_published = false;
UPDATE properties SET admin_status = 'approved' WHERE admin_status IS NULL;
UPDATE properties SET listing_status = 'active' WHERE listing_status IS NULL;

-- Set defaults so all FUTURE listings are automatically published
ALTER TABLE properties ALTER COLUMN is_published SET DEFAULT true;
ALTER TABLE properties ALTER COLUMN admin_status SET DEFAULT 'approved';
ALTER TABLE properties ALTER COLUMN listing_status SET DEFAULT 'active';
```

## FIX 2: Verify the Supabase query works

After running the SQL, test the query the frontend uses:

```sql
SELECT COUNT(*) FROM properties
WHERE is_published = true
AND admin_status = 'approved'
AND listing_status = 'active';
```

This should return 2125 (or however many listings we have). If it returns 0, debug:

```sql
-- Check what values actually exist
SELECT is_published, admin_status, listing_status, COUNT(*)
FROM properties
GROUP BY is_published, admin_status, listing_status;
```

## FIX 3: Ensure the properties table has ALL columns the frontend expects

The frontend code reads these fields from each property. Make sure they ALL exist in the table:

```sql
-- Core fields (should already exist from scrapers)
ALTER TABLE properties ADD COLUMN IF NOT EXISTS slug TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS title_en TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS summary_en TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS price_jpy BIGINT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS price_usd FLOAT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS price_display TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS prefecture TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS region TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS building_sqm FLOAT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS land_sqm FLOAT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS year_built INTEGER;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS rooms TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS floors INTEGER;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS building_type TEXT DEFAULT 'detached';
ALTER TABLE properties ADD COLUMN IF NOT EXISTS structure TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS condition_rating TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS renovation_estimate TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS images JSONB DEFAULT '[]'::jsonb;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS quality_score FLOAT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS hazard_scores JSONB;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS lifestyle_tags JSONB DEFAULT '[]'::jsonb;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS whats_attractive JSONB DEFAULT '[]'::jsonb;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS whats_unclear JSONB DEFAULT '[]'::jsonb;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS whats_risky JSONB DEFAULT '[]'::jsonb;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS what_to_verify JSONB DEFAULT '[]'::jsonb;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS freshness_label TEXT DEFAULT 'new';
ALTER TABLE properties ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'japan';

-- Enrichment fields
ALTER TABLE properties ADD COLUMN IF NOT EXISTS enrichment_status TEXT DEFAULT 'pending';
ALTER TABLE properties ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMPTZ;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS what_to_know TEXT;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_properties_published ON properties(is_published, admin_status, listing_status);
CREATE INDEX IF NOT EXISTS idx_properties_country ON properties(country);
CREATE INDEX IF NOT EXISTS idx_properties_quality ON properties(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price_jpy);
```

## FIX 4: Generate slugs for all listings that don't have one

The frontend uses slugs for detail page URLs (`/properties/[slug]`). Generate them:

```sql
UPDATE properties
SET slug = LOWER(
    REGEXP_REPLACE(
        REGEXP_REPLACE(
            COALESCE(title_en, title, 'property-' || id::text),
            '[^a-zA-Z0-9\s-]', '', 'g'
        ),
        '\s+', '-', 'g'
    )
) || '-' || id
WHERE slug IS NULL;
```

## FIX 5: Fix the enrichment pipeline output format

The LLM enrichment needs to produce data in the format the frontend expects. When enriching listings, the pipeline should generate and save:

```python
# In the enrichment pipeline, after getting LLM results:

# Generate price_display
price_jpy = listing['price_jpy']
if price_jpy:
    man = price_jpy / 10000
    usd = price_jpy / 150  # approximate
    price_display = f"¥{price_jpy:,} ({man:.0f}万円, ~${usd:,.0f})"
else:
    price_display = "Price TBD"

# Generate quality_score based on data completeness + enrichment
quality_factors = []
if listing.get('title_en'): quality_factors.append(0.15)
if listing.get('price_jpy'): quality_factors.append(0.15)
if listing.get('building_sqm'): quality_factors.append(0.1)
if listing.get('land_sqm'): quality_factors.append(0.1)
if listing.get('year_built'): quality_factors.append(0.1)
if listing.get('rooms'): quality_factors.append(0.1)
if listing.get('thumbnail_url'): quality_factors.append(0.15)
if listing.get('what_to_know'): quality_factors.append(0.15)
quality_score = sum(quality_factors)

# Generate slug
import re
title = listing.get('title_en') or listing.get('title') or f"property-{listing['id']}"
slug = re.sub(r'[^a-z0-9\s-]', '', title.lower())
slug = re.sub(r'\s+', '-', slug).strip('-')
slug = f"{slug}-{listing['id']}"
```

Also, the enrichment should generate `whats_attractive`, `whats_unclear`, `whats_risky`, and `what_to_verify` arrays. Update the LLM prompt:

```python
analysis_prompt = f"""Analyze this property listing and provide a buyer assessment.

Title: {title_en}
Location: {location}
Price: ¥{price_jpy:,} if price_jpy else 'Unknown'
Country: {country}
Building: {building_sqm}m² if building_sqm else 'Unknown'
Land: {land_sqm}m² if land_sqm else 'Unknown'
Year built: {year_built or 'Unknown'}
Rooms: {rooms or 'Unknown'}
Description: {description[:500]}

Return a JSON object with these arrays (3-5 items each, short sentences):
{{
    "whats_attractive": ["point 1", "point 2", "point 3"],
    "whats_unclear": ["point 1", "point 2"],
    "whats_risky": ["point 1", "point 2"],
    "what_to_verify": ["point 1", "point 2", "point 3"],
    "summary_en": "2-3 sentence summary for listing card",
    "condition_rating": "move_in_ready|fair|needs_work|significant_renovation|unknown",
    "renovation_estimate": "none|light|moderate|heavy|unknown"
}}
"""
```

## FIX 6: Update storage.py to set publication flags on insert

In `ingestion/storage.py`, make sure `save_raw_listings()` or wherever properties are inserted also sets:

```python
is_published = True
admin_status = 'approved'
listing_status = 'active'
```

So ALL future listings are automatically live on the website.

## FIX 7: Update the frontend for multi-country

In `web/app/properties/page.js`, the page title says "Properties in Japan". Since we're going multi-country, update:

1. Replace hardcoded "Japan" with dynamic country from query params
2. Add a country filter alongside the prefecture filter
3. If country != japan, don't show prefecture filter (show region instead)

Quick fix for now — just remove the Japan-only assumption:

```js
// In page.js, change:
<h1>Properties in Japan</h1>

// To:
<h1>Browse Properties</h1>
```

And in the query, remove or relax the Japan-only constraint if there is one.

## FIX 8: Vercel env vars — make sure they're set

The frontend needs these environment variables on Vercel:
- `NEXT_PUBLIC_SUPABASE_URL` = https://ruwjtsgbqacefwndqcmb.supabase.co
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = (the anon key, NOT the service key)

Check in the Vercel dashboard → Settings → Environment Variables.

If the anon key is missing, find it:
```bash
# It's different from the service key. Check Supabase dashboard → Settings → API → anon public key
```

## FIX 9: EU/USA/NZ scrapers — quick triage

For each failed international scraper, do a quick check:

```bash
cd "/Users/test/Documents/CheapHouse Japan/ingestion"
source venv/bin/activate

# Test each one, see what error we get
for slug in gate-away-it green-acres-fr italian-houses idealista-pt cheap-old-houses-us redfin-us trademe-nz realestate-co-nz; do
    echo "=== $slug ==="
    timeout 30 python run.py scrape --source $slug --limit 2 2>&1 | tail -3
    echo ""
done
```

For each failure:
- If "No module named" → missing import, fix it
- If "connection refused" / timeout → site is blocking, increase delays
- If "0 listings" → CSS selectors wrong, inspect real HTML and fix
- If "API key required" → skip for now, mark as needs-config

Fix the EASY ones (gate-away, italian-houses, cheap-old-houses — these are simple sites). Skip the hard ones for now (hemnet, immobiliare, suumo-level anti-bot).

## FIX 10: IMAGES — Map raw_listings.image_urls to properties.thumbnail_url + images

The scrapers save images in `raw_listings.image_urls` as a plain array of URLs like:
```json
["https://img.homes.co.jp/xxx.jpg", "https://img.homes.co.jp/yyy.jpg"]
```

But the frontend expects:
- `properties.thumbnail_url` — single URL string (first image)
- `properties.images` — JSONB array of objects: `[{"url": "...", "caption": "Photo 1"}, ...]`

### Fix 10a: SQL migration to populate from existing data

```sql
-- Set thumbnail_url from first image in image_urls
UPDATE properties p
SET thumbnail_url = (
    SELECT raw.image_urls->0
    FROM raw_listings raw
    WHERE raw.source_slug = p.source_slug
    AND raw.source_listing_id = p.source_listing_id
    AND raw.image_urls IS NOT NULL
    AND jsonb_array_length(raw.image_urls) > 0
    LIMIT 1
)
WHERE p.thumbnail_url IS NULL;

-- Build images JSONB array from raw image_urls
UPDATE properties p
SET images = (
    SELECT jsonb_agg(
        jsonb_build_object(
            'url', elem,
            'caption', 'Photo ' || (idx + 1)
        )
    )
    FROM raw_listings raw,
    LATERAL jsonb_array_elements_text(raw.image_urls) WITH ORDINALITY AS t(elem, idx)
    WHERE raw.source_slug = p.source_slug
    AND raw.source_listing_id = p.source_listing_id
    AND raw.image_urls IS NOT NULL
    LIMIT 1
)
WHERE p.images IS NULL OR p.images = '[]'::jsonb;
```

NOTE: The above SQL may need adjustment depending on how image_urls is stored (TEXT[] array vs JSONB). Check the column type first:
```sql
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'raw_listings' AND column_name = 'image_urls';
```

If it's a TEXT[] (PostgreSQL array), use:
```sql
-- For TEXT[] array type:
UPDATE properties p
SET thumbnail_url = (
    SELECT raw.image_urls[1]
    FROM raw_listings raw
    WHERE raw.source_slug = p.source_slug
    AND raw.source_listing_id = p.source_listing_id
    AND raw.image_urls IS NOT NULL
    AND array_length(raw.image_urls, 1) > 0
    LIMIT 1
)
WHERE p.thumbnail_url IS NULL;
```

### Fix 10b: Fix the enrichment/processing pipeline

When listings move from `raw_listings` to `properties`, the image_urls must be transformed:

```python
# In the processing step that creates/updates properties from raw_listings:

def process_images(image_urls: list[str]) -> tuple[str, list[dict]]:
    """Convert raw image URL list to frontend format."""
    thumbnail_url = image_urls[0] if image_urls else None
    images = [
        {"url": url, "caption": f"Photo {i+1}"}
        for i, url in enumerate(image_urls[:20])  # Max 20 images
    ]
    return thumbnail_url, images

# When inserting/updating properties:
thumbnail_url, images_json = process_images(raw_listing.image_urls)
# Include in the INSERT/UPDATE:
# thumbnail_url = thumbnail_url
# images = json.dumps(images_json)
```

### Fix 10c: If properties are DIRECTLY the raw_listings table

If properties and raw_listings are the same table (or properties is populated by a simple copy), just add:

```sql
-- Quick fix: copy image_urls[0] to thumbnail_url
UPDATE properties
SET thumbnail_url = image_urls[1]  -- PostgreSQL arrays are 1-indexed
WHERE thumbnail_url IS NULL
AND image_urls IS NOT NULL
AND array_length(image_urls, 1) > 0;
```

## After ALL fixes — deploy and verify

```bash
# 1. Push backend changes
cd "/Users/test/Documents/CheapHouse Japan"
git add -A && git commit -m "fix: publish listings to frontend, fix DB flags, multi-country support" && git push

# 2. Trigger Vercel redeploy (should auto-deploy on push)
# Or force: vercel --prod (if CLI is installed)

# 3. Verify — check the live site
echo ""
echo "=== VERIFICATION ==="
echo ""

# Count published listings
python3 -c "
import sys
sys.path.insert(0, 'ingestion')
from ingestion.db import execute
rows = execute('''
    SELECT COUNT(*) as total,
           COUNT(*) FILTER (WHERE is_published = true AND admin_status = %s AND listing_status = %s) as published
    FROM properties
''', ('approved', 'active'))
r = rows[0]
print(f'Total: {r[\"total\"]}')
print(f'Published (visible on site): {r[\"published\"]}')
"

echo ""
echo "Now check your live site — the real listings should appear!"
echo "If still showing mock data, check Vercel logs for errors."
```
```
