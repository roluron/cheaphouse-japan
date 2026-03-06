# PROMPT À COLLER DANS ANTIGRAVITY — Setup Supabase + Run Pipeline + Connect Frontend

```
I have set up a Supabase project. Now I need to:
1. Configure the Python ingestion pipeline to use it
2. Run the scrapers to populate the database
3. Connect the Next.js frontend to Supabase

## Part 1 — Configure the ingestion pipeline

In the /ingestion/ folder:

1. Copy .env.example to .env
2. Set DATABASE_URL to my Supabase Postgres connection string.
   Find it in Supabase dashboard: Settings > Database > Connection string > URI
   Format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

   IMPORTANT: Use the "Transaction" pooler connection string (port 6543), NOT the direct connection (port 5432). This is needed because Supabase uses connection pooling.

3. If I have an OpenAI API key, set OPENAI_API_KEY in .env too. If not, we'll skip LLM steps.

## Part 2 — Run the pipeline

Run these commands in order:

```bash
cd ingestion
source venv/bin/activate  # or create venv if it doesn't exist: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
python -m ingestion.run scrape --source old-houses-japan
python -m ingestion.run scrape --source all-akiyas
python -m ingestion.run pipeline --skip-translate  # skip LLM if no API key
```

If there are errors, fix them. Common issues:
- psycopg2 not installed: pip install psycopg2-binary
- Connection refused: check DATABASE_URL format
- Tables don't exist: run schema.sql in Supabase SQL Editor first

After the pipeline runs, approve properties for the frontend:

Connect to Supabase SQL Editor and run:
```sql
-- Generate slugs for all properties
UPDATE properties
SET slug = lower(
    regexp_replace(
        regexp_replace(
            coalesce(title_en, 'property-' || left(id::text, 8)),
            '[^a-zA-Z0-9\s-]', '', 'g'
        ),
        '\s+', '-', 'g'
    )
)
WHERE slug IS NULL;

-- Publish properties with decent quality
UPDATE properties
SET admin_status = 'approved', is_published = true
WHERE quality_score > 0.4;

-- Check how many we have
SELECT count(*) as total,
       count(*) FILTER (WHERE is_published) as published
FROM properties;
```

## Part 3 — Connect the Next.js frontend to Supabase

In the /web/ folder:

1. Install Supabase client:
```bash
npm install @supabase/supabase-js @supabase/ssr
```

2. Create .env.local with my Supabase credentials:
```
NEXT_PUBLIC_SUPABASE_URL=https://[my-project-ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[my-anon-key]
```

3. Create app/lib/supabase-browser.js:
```javascript
import { createBrowserClient } from '@supabase/ssr'

export function getSupabaseBrowser() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  )
}
```

4. Create app/lib/supabase-server.js:
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
          } catch { /* ignore in server components */ }
        },
      },
    }
  )
}
```

5. Update next.config.mjs — add Supabase storage and source site image domains to remotePatterns:
```javascript
{
  protocol: "https",
  hostname: "**.supabase.co",
},
{
  protocol: "https",
  hostname: "oldhousesjapan.com",
},
{
  protocol: "https",
  hostname: "www.allakiyas.com",
},
```

6. Rewrite app/page.js (homepage):
   - Convert to a server component
   - Fetch top 3 properties from Supabase: `supabase.from('properties').select('*').eq('is_published', true).eq('admin_status', 'approved').order('quality_score', { ascending: false }).limit(3)`
   - Replace `MOCK_PROPERTIES.slice(0, 3)` with the real data
   - Keep ALL existing layout, styling, sections exactly as they are
   - If 0 properties returned, fall back to the mock data

7. Rewrite app/properties/page.js (browse page):
   - Make the data fetching server-side
   - Keep the filter UI as a separate client component
   - Query: `supabase.from('properties').select('*').eq('is_published', true).eq('admin_status', 'approved')`
   - Apply filters from URL search params server-side
   - Keep existing PropertyCard component and styling

8. Rewrite app/properties/[slug]/page.js (detail page):
   - Query: `supabase.from('properties').select('*').eq('slug', slug).eq('is_published', true).single()`
   - If not found, return 404
   - Keep all existing sections and styling

CRITICAL: Do NOT change the design, layout, or CSS. Only change the data source from mock to Supabase. The design is already done and looks great.

After everything is wired up, run `npm run build` to verify no errors, then push to GitHub so Vercel auto-deploys.
```
