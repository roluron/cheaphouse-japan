# PROMPT À COLLER DANS ANTIGRAVITY — Supabase: tout configurer, pipeline, frontend

```
I just created a Supabase project. I need you to do EVERYTHING to get CheapHouse Japan working end-to-end with real data. Don't ask me questions — just do it.

## Context

- Supabase project is created, I have access to the dashboard
- The ingestion pipeline is in /ingestion/ (Python, with scrapers + enrichment pipeline)
- The frontend is in /web/ (Next.js, currently running on mock data in app/lib/data.js)
- The database schema files are at:
  - /ingestion/schema.sql (main tables: sources, raw_listings, properties, scrape_runs)
  - /web/supabase/migration_001_users.sql (user tables, saved_properties, RLS policies)
- The seed data for sources is at /ingestion/seed_sources.sql

## Step 1 — Get my Supabase credentials

Open my Supabase dashboard. Go to:
- Settings > API → copy the Project URL and anon public key
- Settings > Database → copy the connection string (URI format, use Transaction/Pooler mode on port 6543)

I'll need to provide the database password when you build the connection string.

## Step 2 — Run the SQL migrations in Supabase

Go to the Supabase SQL Editor and execute these files in order:
1. The contents of /ingestion/schema.sql
2. The contents of /ingestion/seed_sources.sql
3. The contents of /web/supabase/migration_001_users.sql

You can copy-paste each file's contents into the SQL Editor and run them. Do them in this exact order because migration_001 references tables from schema.sql.

## Step 3 — Configure the Python ingestion pipeline

In /ingestion/:
1. Copy .env.example to .env
2. Set DATABASE_URL to the Supabase Postgres connection string (Transaction pooler, port 6543)
3. If I have an OpenAI API key, set OPENAI_API_KEY too. If not, we'll skip LLM steps later.
4. Make sure the Python venv exists and has all dependencies:
   ```bash
   cd ingestion
   python -m venv venv || true
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Step 4 — Run the scrapers and pipeline

```bash
cd ingestion
source venv/bin/activate

# Scrape from both working sources
python -m ingestion.run scrape --source old-houses-japan
python -m ingestion.run scrape --source all-akiyas

# Run the enrichment pipeline (skip LLM if no OpenAI key)
python -m ingestion.run pipeline --skip-translate

# Check what we got
python -m ingestion.run stats
```

If --skip-translate was used, properties won't have title_en or summary_en. That's OK for now — the frontend should handle nulls gracefully.

## Step 5 — Approve and publish properties

Go to the Supabase SQL Editor and run:

```sql
-- Generate slugs
UPDATE properties
SET slug = lower(
    regexp_replace(
        regexp_replace(
            coalesce(title_en, original_title, 'property-' || left(id::text, 8)),
            '[^a-zA-Z0-9\s-]', '', 'g'
        ),
        '\s+', '-', 'g'
    )
)
WHERE slug IS NULL;

-- Make slugs unique by appending short id where there are duplicates
WITH dupes AS (
    SELECT slug, array_agg(id ORDER BY quality_score DESC) as ids
    FROM properties WHERE slug IS NOT NULL
    GROUP BY slug HAVING count(*) > 1
)
UPDATE properties p
SET slug = p.slug || '-' || left(p.id::text, 6)
FROM dupes d
WHERE p.slug = d.slug AND p.id != d.ids[1];

-- Publish decent quality properties
UPDATE properties
SET admin_status = 'approved', is_published = true
WHERE quality_score > 0.4;

-- Stats
SELECT
    count(*) as total_properties,
    count(*) FILTER (WHERE is_published) as published,
    count(*) FILTER (WHERE title_en IS NOT NULL) as has_english_title,
    count(DISTINCT prefecture) as prefectures
FROM properties;
```

## Step 6 — Install Supabase in the Next.js project

```bash
cd web
npm install @supabase/supabase-js @supabase/ssr
```

## Step 7 — Create .env.local in /web/

```
NEXT_PUBLIC_SUPABASE_URL=<the project URL from step 1>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<the anon key from step 1>
```

## Step 8 — Create Supabase client utilities

Create app/lib/supabase-browser.js:
```javascript
import { createBrowserClient } from '@supabase/ssr'

export function getSupabaseBrowser() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  )
}
```

Create app/lib/supabase-server.js:
```javascript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function getSupabaseServer() {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {}
        },
      },
    }
  )
}
```

## Step 9 — Update next.config.mjs

Add more image domains to the existing remotePatterns (keep what's already there, just add these if missing):
```javascript
{ protocol: "https", hostname: "oldhousesjapan.com" },
{ protocol: "https", hostname: "www.oldhousesjapan.com" },
{ protocol: "https", hostname: "uploads-ssl.webflow.com" },
{ protocol: "https", hostname: "www.allakiyas.com" },
{ protocol: "https", hostname: "**.supabase.co" },
```

## Step 10 — Rewrite the frontend to use Supabase data

### app/page.js (homepage)
- Keep ALL existing design, layout, sections, CSS exactly as they are
- Only change: fetch 3 featured properties from Supabase instead of MOCK_PROPERTIES
- Query: `supabase.from('properties').select('*').eq('is_published', true).eq('admin_status', 'approved').order('quality_score', { ascending: false }).limit(3)`
- If query returns 0 results, fall back to the existing mock data so the homepage never looks empty

### app/properties/page.js (browse)
- Split into: server component for data fetching + client component for filter UI
- Query: `supabase.from('properties').select('*').eq('is_published', true).eq('admin_status', 'approved')`
- Apply filters from URL searchParams server-side:
  - Prefecture: `.eq('prefecture', value)`
  - Price min/max: `.gte('price_jpy', min).lte('price_jpy', max)`
  - Sort: `.order('price_jpy', { ascending: true })` etc.
  - Lifestyle tags: fetch all then filter client-side (JSONB containment is complex, and we have <500 properties)
- Pagination: `.range(from, to)` with 12 per page
- Keep existing PropertyCard component — just adapt it if the data shape differs slightly
- Handle nulls: if thumbnail_url is null, show gradient placeholder. If lifestyle_tags is null/empty, don't show tags section.

### app/properties/[slug]/page.js (property detail)
- Query: `supabase.from('properties').select('*').eq('slug', slug).eq('is_published', true).single()`
- If not found: `notFound()`
- Add dynamic metadata: title from title_en, description from summary_en
- Keep ALL existing sections and styling
- Handle nulls gracefully: if whats_attractive is null, hide that card. If hazard_scores is empty, show "Hazard data pending". If images is empty, show placeholder.

### PropertyCard component
- Make sure it works with real data shape:
  - images is JSONB (array of {url, caption, order}), not a simple string array
  - lifestyle_tags is JSONB (array of {tag, confidence, reasons, method})
  - hazard_scores is JSONB ({flood: {level, ...}, landslide: {level, ...}, tsunami: {level, ...}})
  - Some fields may be null
- Use title_en if available, fall back to original_title
- Use thumbnail_url for image, fall back to first image in images array, fall back to gradient

## Step 11 — Build and verify

```bash
cd web
npm run build
```

Fix any errors. Then:
```bash
npm run dev
```

Open http://localhost:3000 and verify:
- Homepage shows real featured properties (or mock fallback)
- /properties shows the grid with real data from Supabase
- Clicking a property card goes to the detail page with real data
- Filters work
- No console errors

## Step 12 — Push to GitHub and deploy

```bash
cd web
git add -A
git commit -m "Connect Supabase: real property data from ingestion pipeline"
git push origin main
```

Then add the Supabase env vars to Vercel:
```bash
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel --prod
```

Or do it via the Vercel dashboard: Settings > Environment Variables.

## RULES

- Do NOT change the design, CSS, or visual layout. The styling is done.
- Do NOT remove app/lib/data.js — keep it as fallback.
- Handle empty/null data gracefully everywhere. Never crash on missing data.
- Use server components by default. Only use 'use client' for interactive parts (filters, gallery clicks, etc.)
- If something fails, fix it and keep going. Don't stop and ask me.
```
