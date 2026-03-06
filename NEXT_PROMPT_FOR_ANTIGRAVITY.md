# PROMPT À COLLER DANS ANTIGRAVITY — Étape "Connecter Supabase"

## Contexte pour Antigravity

Copie tout ce qui est entre les ``` ci-dessous et colle-le dans Antigravity :

---

```
The CheapHouse Japan frontend is currently running on mock data in app/lib/data.js. I need to connect it to my Supabase database which already has real property data from my Python ingestion pipeline.

Here is what I need you to do — follow this exact order:

## 1. Install Supabase packages

npm install @supabase/supabase-js @supabase/ssr

## 2. Create .env.local

Create .env.local at the web project root with:

NEXT_PUBLIC_SUPABASE_URL=<I'll fill this in>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<I'll fill this in>
SUPABASE_SERVICE_ROLE_KEY=<I'll fill this in>

## 3. Create Supabase client utilities

Create these files:

app/lib/supabase-browser.js — Browser/client-side Supabase client:
- Use createBrowserClient from @supabase/ssr
- Export a function getSupabaseBrowser() that returns the client
- Use NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY from process.env

app/lib/supabase-server.js — Server-side Supabase client:
- Use createServerClient from @supabase/ssr
- Read/write cookies from next/headers
- Export an async function getSupabaseServer() that returns the client
- Use NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY

## 4. Update next.config.mjs

Add remotePatterns for images from these domains:
- oldhousesjapan.com
- www.oldhousesjapan.com
- uploads-ssl.webflow.com (Webflow CDN)
- www.allakiyas.com
- images.unsplash.com

## 5. Rewrite app/properties/page.js to use Supabase

Convert the browse page FROM mock data TO real Supabase data.

The database table is called `properties`. Key columns:
- id (UUID), slug (TEXT), title_en (TEXT), summary_en (TEXT)
- price_jpy (INT), price_usd (INT), price_display (TEXT)
- prefecture (TEXT), city (TEXT), region (TEXT)
- land_sqm (FLOAT), building_sqm (FLOAT), year_built (INT), rooms (TEXT)
- condition_rating (TEXT), renovation_estimate (TEXT)
- thumbnail_url (TEXT), images (JSONB — array of {url, caption, order})
- hazard_scores (JSONB — {flood: {level, confidence, source, summary}, landslide: {...}, tsunami: {...}})
- lifestyle_tags (JSONB — array of {tag, confidence, reasons, method})
- quality_score (FLOAT 0-1)
- is_published (BOOLEAN), admin_status (TEXT)
- whats_attractive (TEXT[]), whats_unclear (TEXT[]), whats_risky (TEXT[]), what_to_verify (TEXT[])
- original_url (TEXT)
- first_seen_at (TIMESTAMPTZ)

Query: SELECT FROM properties WHERE is_published = true AND admin_status = 'approved' ORDER BY quality_score DESC

Make this a SERVER component (not 'use client'). Create a separate client component for the filter UI.

Filtering approach:
- Read search params from the URL
- Build the Supabase query server-side based on params
- Prefecture filter: .eq('prefecture', value)
- Price filter: .gte('price_jpy', min).lte('price_jpy', max)
- Sort: .order('price_jpy', {ascending: true}) etc.
- For lifestyle tags: use a text search or filter after fetch (JSONB containment is tricky with Supabase JS client — it's OK to fetch all and filter client-side for MVP since we have < 500 properties)
- Paginate: .range(from, to) with 12 properties per page

Keep the existing filter UI design (filter-bar, filter-select, etc from globals.css). Keep the PropertyCard component but update it to handle real data shape (images is JSONB not a simple array, lifestyle_tags has a different shape, etc).

Handle null/missing values gracefully — many properties might not have thumbnail_url, or might have empty lifestyle_tags.

## 6. Rewrite app/properties/[slug]/page.js to use Supabase

Convert the detail page FROM mock data TO real Supabase data.

Query: SELECT FROM properties WHERE slug = params.slug AND is_published = true AND admin_status = 'approved' LIMIT 1

If not found, call notFound() from next/navigation.

Generate dynamic metadata:
- title: property.title_en + " | CheapHouse Japan"
- description: first 160 chars of summary_en
- openGraph image: thumbnail_url

Keep the exact same layout and sections that already exist. Just swap the data source from mock to Supabase.

Handle null values: if whats_attractive is null or empty, don't show that card. If hazard_scores is empty {}, show "Hazard data pending". If images is empty [], show a placeholder.

## 7. Update app/page.js homepage

Replace the mock featured properties with real ones from Supabase.

Fetch the top 3 properties by quality_score (server-side) to show in the "Featured Properties" section.

Keep everything else on the homepage exactly as-is.

## 8. Keep app/lib/data.js as fallback

Don't delete the mock data file — keep it as a reference and fallback. But the main pages should now use Supabase.

IMPORTANT RULES:
- Use the EXISTING CSS classes from globals.css — do NOT add Tailwind or new styling frameworks
- Use the EXISTING component patterns (PropertyCard, etc) — just update them for real data shape
- Server components by default, 'use client' only for interactive parts (filters, gallery, etc)
- Handle empty database gracefully — if 0 properties, show a nice empty state, not an error
- All images should use next/image with proper width/height and fallback if URL is broken
```

---

## Après ce prompt

Une fois que c'est fait et que ça tourne avec Supabase, les prochains prompts dans l'ordre sont :

### Prompt suivant : Auth (Login/Signup)
Ajouter Supabase Auth, pages login/signup, mise à jour du Nav pour afficher l'état connecté.

### Puis : Saved Properties + Compare
SaveButton sur les cards, page /saved, page /compare.

### Puis : Buyer Quiz + Matching
Quiz interactif, lib/matching.js, match scores dans le browse.

### Puis : Stripe
Pricing page, checkout, webhooks, gating features.

### Puis : Admin Dashboard
Review queue, approve/reject, source status.

### Puis : Polish + Deploy
SEO, loading states, error boundaries, Vercel deploy.
