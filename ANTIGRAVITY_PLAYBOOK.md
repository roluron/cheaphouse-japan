# Antigravity Playbook — CheapHouse Japan

## Comment utiliser ce fichier

Copie-colle chaque prompt dans Antigravity, un par un, dans l'ordre. Chaque prompt est autonome et référence ton code existant. Ne saute pas d'étape — chaque prompt dépend des précédents.

Avant de commencer : assure-toi que ton projet Supabase est créé et que tu as tes clés (URL + anon key + service role key).

---

## PROMPT 1 — Setup Supabase + Config + Dependencies

```
I'm building a Japanese real estate platform called CheapHouse Japan. The Next.js project is in the /web folder. The design system is already in globals.css (dark theme, premium look, CSS variables).

Do the following setup steps:

1. Install dependencies:
   - @supabase/supabase-js
   - @supabase/ssr (for server-side auth with App Router)
   - @stripe/stripe-js
   - stripe (server-side)

2. Create a .env.local.example file with:
   NEXT_PUBLIC_SUPABASE_URL=
   NEXT_PUBLIC_SUPABASE_ANON_KEY=
   SUPABASE_SERVICE_ROLE_KEY=
   STRIPE_SECRET_KEY=
   STRIPE_WEBHOOK_SECRET=
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
   STRIPE_PRICE_ID=
   NEXT_PUBLIC_SITE_URL=http://localhost:3000

3. Create lib/supabase/client.js — browser Supabase client using createBrowserClient from @supabase/ssr

4. Create lib/supabase/server.js — server Supabase client using createServerClient from @supabase/ssr, reading cookies from next/headers

5. Create middleware.js at the project root — Supabase auth middleware that refreshes the session on every request. It should NOT block any routes, just refresh the token silently.

6. Update next.config.mjs to allow images from these remote domains:
   - oldhousesjapan.com
   - www.allakiyas.com
   - cheaphousesjapan.com
   - uploads-ssl.webflow.com (Webflow CDN used by Old Houses Japan)
   - images.unsplash.com (for placeholder images)

Do NOT change globals.css or layout.js — they're already set up correctly.
```

---

## PROMPT 2 — SQL Migration for User Tables

```
I need a SQL migration file to run in Supabase SQL Editor. Create it as /web/supabase/migration_001_users.sql

My existing schema already has: sources, raw_listings, properties, scrape_runs tables (see /ingestion/schema.sql for reference).

Add these NEW tables:

1. user_profiles — extends Supabase auth.users:
   - id UUID PRIMARY KEY references auth.users(id) ON DELETE CASCADE
   - display_name TEXT
   - subscription_status TEXT DEFAULT 'free' CHECK IN ('free', 'active', 'cancelled', 'past_due')
   - stripe_customer_id TEXT
   - stripe_subscription_id TEXT
   - quiz_answers JSONB DEFAULT '{}'
   - created_at, updated_at TIMESTAMPTZ

   Also create a trigger function that auto-creates a user_profile row when a new auth.users row is inserted.

2. saved_properties:
   - id UUID PK
   - user_id UUID references auth.users ON DELETE CASCADE
   - property_id UUID references properties ON DELETE CASCADE
   - notes TEXT
   - saved_at TIMESTAMPTZ
   - UNIQUE(user_id, property_id)

3. Add columns to properties table (ALTER TABLE, use IF NOT EXISTS):
   - slug TEXT UNIQUE
   - is_published BOOLEAN DEFAULT false
   - view_count INT DEFAULT 0
   - save_count INT DEFAULT 0

4. Row Level Security policies:
   - properties: public SELECT where is_published = true AND admin_status = 'approved'
   - saved_properties: users can only CRUD their own rows
   - user_profiles: users can only read/update their own row

5. Create indexes on the new columns.

Add clear comments throughout. Make it idempotent (safe to run multiple times).
```

---

## PROMPT 3 — Shared Navigation + Footer Components

```
Create the shared layout components for CheapHouse Japan. Use the design system already in globals.css (CSS variables, .nav, .footer, .container classes, etc). Do NOT use Tailwind — use the existing CSS classes and CSS modules for component-specific styles.

1. Create components/Navigation.js:
   - Fixed top nav bar using .nav, .nav-inner, .nav-logo, .nav-links classes from globals.css
   - Logo: "CheapHouse" with "Japan" in accent color (use .text-gradient or inline style with var(--accent-blue))
   - Links: Browse, Quiz, Pricing
   - Right side: Login/Signup buttons (if not logged in) or Account link (if logged in)
   - Use Supabase client to check auth state
   - Mobile: just show logo + hamburger icon (can be basic for now)

2. Create components/Footer.js:
   - Using .footer, .footer-grid classes from globals.css
   - Columns: About (company description), Browse (links to browse by region), Resources (How it Works, Pricing, FAQ), Legal (Terms, Privacy)
   - Bottom: copyright line

3. Update app/layout.js to include Navigation and Footer wrapping {children}
   - Add a <main> wrapper with padding-top: 80px to account for fixed nav
   - Keep existing fonts and metadata

All components should be client components where needed (auth state). Use 'use client' directive only when necessary.
```

---

## PROMPT 4 — Homepage

```
Build the homepage for CheapHouse Japan at app/page.js

This is a premium dark-themed real estate decision platform. NOT a listing site. NOT a cheap classifieds look. Think: premium SaaS landing page meets real estate intelligence tool.

Use the design system in globals.css (CSS variables, .container, .section, .btn, .btn-primary, .glass-card, .property-card, .badge-*, .animate-in classes). Use CSS modules for page-specific styles. Do NOT use Tailwind.

Sections to build:

1. HERO SECTION
   - Background: use var(--gradient-hero), add a subtle grid/dot pattern overlay
   - Headline (h1, large): "Find the right house in Japan." (line break) "Avoid the wrong one."
   - Subheadline: "The decision platform for international buyers. We aggregate listings, add hazard data, and tell you what others won't."
   - Two CTAs: "Browse Properties" (btn-primary btn-lg → /browse) and "Take the Quiz" (btn-secondary btn-lg → /quiz)
   - Stats row below CTAs: "250+ Properties" · "47 Prefectures" · "3 Risk Layers" · "8 Lifestyle Filters"

2. PROBLEM SECTION
   - Headline: "Buying a house in Japan shouldn't feel like this"
   - 4 pain point cards (glass-card):
     * "Listings scattered across dozens of sites"
     * "Critical hazard data buried in Japanese-only maps"
     * "No way to filter by lifestyle or real needs"
     * "Beautiful photos hiding serious red flags"

3. SOLUTION SECTION
   - Headline: "One platform. Complete clarity."
   - 3 feature cards:
     * "Aggregated & Normalized" — We pull from multiple sources and standardize everything
     * "Hazard Intelligence" — Flood, landslide, tsunami risk on every property
     * "Honest Insights" — What's attractive, what's unclear, what's risky, what to verify

4. PROPERTY PREVIEW SECTION
   - Headline: "See what's possible"
   - Show 3 mock property cards using the .property-card CSS classes
   - Use realistic mock data (Japanese properties, real-looking prices like ¥2,800,000 / ~$18,700)
   - Each card: image placeholder (use a gradient bg or solid color), price, title, location, 2-3 badges (lifestyle tags), hazard indicator
   - Link: "Browse all properties →"

5. LIFESTYLE SECTION
   - Headline: "Search by how you want to live"
   - Grid of lifestyle tags as clickable pills/badges:
     * Pet-Friendly, Artist Retreat, Remote Work, Low Renovation, Near Station, Rural Retreat, Family Ready, Retirement
   - Each links to /browse?lifestyle=xxx

6. CTA SECTION
   - Headline: "Stop browsing. Start deciding."
   - Subtext: "From $10/month. Cancel anytime."
   - CTA: "Get Started" → /signup

7. Use .animate-in and .animate-delay-* classes for scroll-triggered fade-in effects (use IntersectionObserver in a useEffect).

Make it beautiful. Make it feel premium and trustworthy. Not salesy.
```

---

## PROMPT 5 — Browse Properties Page (with Supabase)

```
Build the Browse Properties page at app/browse/page.js

This is a server component that fetches properties from Supabase and displays them in a filterable grid.

DATABASE CONTEXT:
The `properties` table has these key columns (from /ingestion/schema.sql):
- id (UUID), slug (TEXT), title_en, summary_en
- price_jpy (INT), price_usd (INT), price_display (TEXT)
- prefecture (TEXT), city (TEXT), region (TEXT)
- land_sqm, building_sqm, year_built, rooms
- condition_rating (TEXT: good/fair/needs_work/significant_renovation/unknown)
- thumbnail_url (TEXT), images (JSONB array of {url, caption, order})
- hazard_scores (JSONB: {flood: {level, confidence, source, summary}, landslide: {...}, tsunami: {...}})
- lifestyle_tags (JSONB array of {tag, confidence, reasons, method})
- quality_score (FLOAT 0-1)
- is_published (BOOLEAN), admin_status (TEXT)
- whats_attractive (TEXT[]), whats_unclear (TEXT[]), whats_risky (TEXT[]), what_to_verify (TEXT[])

QUERY: Only show properties WHERE is_published = true AND admin_status = 'approved'. Order by quality_score DESC.

BUILD:

1. FilterBar component (client component):
   - Prefecture dropdown (grouped by region: Hokkaido, Tohoku, Kanto, Chubu, Kansai, Chugoku, Shikoku, Kyushu)
   - Price range: min/max inputs in JPY
   - Lifestyle tags: multi-select chips (pet-friendly, artist-retreat, remote-work, low-renovation, near-station, rural-retreat, family-ready, retirement)
   - Max hazard level: dropdown (any / low only / low + moderate)
   - Sort: quality score / price low→high / price high→low / newest
   - Filters update URL search params (useSearchParams + useRouter)
   - Use .filter-bar, .filter-select, .filter-input CSS classes from globals.css

2. PropertyCard component (components/PropertyCard.js):
   - Use .property-card classes from globals.css
   - Image: use thumbnail_url or first image from images array, with Next.js Image component. Fallback to gradient placeholder.
   - Price: ¥X,XXX,XXX format (+ ~$XX,XXX in smaller text)
   - Title: title_en, clamped to 2 lines
   - Location: prefecture, city
   - Meta row: building_sqm m², land_sqm m², rooms, year_built
   - Lifestyle tags: show top 3 using .badge-* classes
   - Hazard indicator: show worst hazard level using .hazard-* classes
   - Links to /property/[slug]

3. Main page layout:
   - Header: "Browse Properties" + result count
   - FilterBar
   - PropertyGrid (.property-grid class)
   - Pagination (simple prev/next with page search param)
   - Empty state if no results

4. Server-side filtering: read searchParams, build Supabase query with .eq(), .gte(), .lte(), .contains(), .order()

For the lifestyle_tags filter: use Supabase JSONB containment — a property matches if its lifestyle_tags array contains an object where tag equals the filter value. Use .filter() or raw SQL via .rpc() if needed.

Make it performant. The page should work with 0 properties gracefully.
```

---

## PROMPT 6 — Property Detail Page

```
Build the Property Detail page at app/property/[slug]/page.js

This is the most important page of the product. It must give the buyer EVERYTHING they need to decide without leaving the page.

Fetch the property from Supabase by slug (WHERE slug = params.slug AND is_published = true AND admin_status = 'approved').

If not found, return notFound().

Generate dynamic metadata (title, description, og:image) from the property data.

SECTIONS — build each as a component:

1. IMAGE GALLERY (components/PropertyGallery.js — client component)
   - Display images from the images JSONB array [{url, caption, order}]
   - Main large image + thumbnail strip below
   - Click thumbnail to change main image
   - If no images: show a styled placeholder with text "No images available"
   - Use CSS modules, dark theme consistent

2. KEY FACTS BAR
   - Horizontal row: Price (¥ + $), Building (m²), Land (m²), Rooms, Year Built, Condition
   - Each as an icon + label + value block
   - Use icons as simple SVG or unicode characters (no icon library needed for MVP)

3. SUMMARY (the AI-written English description)
   - title_en as h1
   - summary_en as formatted paragraphs
   - Below: "Source: [original site name]" with link to original_url (opens new tab)

4. WHAT TO KNOW — THE DIFFERENTIATOR (components/WhatToKnow.js)
   This is the section that makes us different from every other site.
   Four cards, each with a distinct color:
   - ✅ What's Attractive (green — var(--accent-green)) — from whats_attractive TEXT[]
   - ❓ What's Unclear (amber — var(--accent-amber)) — from whats_unclear TEXT[]
   - ⚠️ What's Risky (rose — var(--accent-rose)) — from whats_risky TEXT[]
   - 🔍 What to Verify (blue — var(--accent-blue)) — from what_to_verify TEXT[]

   Each card: colored left border, icon, title, bullet list of items
   Use glass-card style with colored accent. Make this section visually prominent.

5. HAZARD ASSESSMENT (components/HazardPanel.js)
   - From hazard_scores JSONB: {flood: {level, confidence, source, summary}, landslide: {...}, tsunami: {...}}
   - Three rows, one per hazard type
   - Each: hazard name, level badge (using .hazard-* classes), confidence indicator, summary text
   - If all unknown: show "Hazard data pending — check local authorities"

6. LIFESTYLE FIT (components/LifestyleTags.js)
   - From lifestyle_tags JSONB array [{tag, confidence, reasons, method}]
   - Display as badges with confidence bar
   - Show reasons on hover or in expanded view
   - Use .badge-* classes

7. PROPERTY DETAILS TABLE
   - Full specs: building type, structure, floors, rooms, land_sqm, building_sqm, year_built, condition_rating, renovation_estimate, nearest_station, station_distance
   - Two-column layout on desktop, single column on mobile
   - Skip any null values

8. ACTIONS SIDEBAR (sticky on desktop)
   - Save button (requires auth)
   - Add to Compare
   - Share link (copy URL)
   - "View Original Listing" → original_url

Use CSS modules per component. Keep the dark premium feel. The page should feel like a premium property report, not a classifieds listing.
```

---

## PROMPT 7 — Auth (Login + Signup)

```
Build authentication pages using Supabase Auth.

1. app/login/page.js — Login page
   - Email + password form
   - "Sign in with Google" button (Supabase OAuth)
   - Link to signup
   - On success: redirect to /browse
   - Error display for invalid credentials
   - Premium dark theme using globals.css variables

2. app/signup/page.js — Signup page
   - Email + password + display name form
   - "Sign up with Google" button
   - Link to login
   - On success: redirect to /browse (Supabase sends confirmation email automatically)
   - Password requirements hint

3. Update the Navigation component:
   - If user is logged in: show avatar/name + "Account" + "Logout"
   - If not logged in: show "Login" + "Sign Up" buttons
   - Use Supabase onAuthStateChange to reactively update

4. Create a lib/auth.js helper with:
   - getCurrentUser() — server-side, returns user or null
   - requireAuth() — server-side, redirects to /login if not authenticated
   - requireSubscription() — server-side, redirects to /pricing if user is free tier

Both pages should be simple, clean, centered forms. Use glass-card style. No unnecessary decoration.
```

---

## PROMPT 8 — Buyer Quiz + Matching

```
Build the Buyer Quiz at app/quiz/page.js — this is a client component ('use client').

The quiz helps users define their preferences and generates a match score for every property.

QUESTIONS (7 steps, one question per screen, smooth transitions):

1. Budget — "What's your budget range?"
   Options as clickable cards: Under ¥1M (~$6,700) / ¥1-3M (~$6,700-$20,000) / ¥3-5M / ¥5-10M / ¥10-20M / Over ¥20M

2. Purpose — "What will this home be for?"
   Options: Primary residence / Second home / Vacation retreat / Creative studio/workshop / Investment / I'm not sure yet

3. Renovation — "How much work are you willing to do?"
   Options: Move-in ready only / Minor cosmetic work OK / Moderate renovation OK / Major renovation is fine

4. Animals — "Do you have or plan to have pets?"
   Options: Yes, dogs / Yes, cats / Yes, other animals / No pets

5. Transport — "How important is public transport access?"
   Options: Must be near a train station / Occasional access is fine / I'll have a car / Full remoteness is OK

6. Risk Tolerance — "How do you feel about natural hazard zones?"
   Options: I want minimal risk / Some risk is OK if the deal is good / Doesn't concern me much

7. Environment — "What setting appeals to you most?"
   Options: In or near a city / Suburban / Countryside / Mountain area / Coastal / Forest

QUIZ UX:
- Progress bar at top
- One question per view with animated transitions
- Selected option highlighted with accent border
- Back/Next navigation
- On completion: save answers to user_profiles.quiz_answers via Supabase (if logged in) or localStorage (if not)
- Redirect to /browse after completion — browse page will show match scores

MATCHING LOGIC — create lib/matching.js:

Function: computeMatchScore(quizAnswers, property) → { score: 0-1, breakdown: {...} }

Breakdown dimensions:
- budget_fit (weight 3): 1.0 if price is in chosen bracket, 0.7 if ±1 bracket, 0.3 if ±2, 0 beyond
- lifestyle_match (weight 2): count of property's lifestyle_tags that align with quiz answers / total expected tags
- risk_tolerance (weight 2): compare max hazard level to user tolerance
- condition_fit (weight 2): compare condition_rating to renovation answer
- transport_fit (weight 1): compare near-station tag to transport answer
- environment_fit (weight 1): compare property region/prefecture to environment answer

The score must be EXPLAINABLE — each sub-score should have a human-readable reason string.

Make the quiz feel premium and engaging. Animated transitions between questions. Dark theme.
```

---

## PROMPT 9 — Saved Properties + Compare

```
Build the Saved Properties and Compare features.

1. app/saved/page.js — Saved Properties (requires auth)
   - Fetch from saved_properties table joined with properties
   - Display as property cards (reuse PropertyCard component)
   - Each card has: remove from saved, add to compare, notes (editable inline)
   - Empty state: "No saved properties yet. Browse properties to start saving."
   - Link to /browse

2. Save Button Component (components/SaveButton.js — client component):
   - Heart icon, toggles saved/unsaved state
   - If not logged in: show tooltip "Sign in to save properties" + redirect to login
   - If logged in: INSERT/DELETE from saved_properties via Supabase client
   - Optimistic UI update
   - Use this component on PropertyCard and Property Detail page

3. app/compare/page.js — Compare View (requires auth + subscription)
   - Read property IDs from URL search params (?ids=uuid1,uuid2,uuid3)
   - Max 3 properties at once
   - Side-by-side comparison table:
     Rows: Photo, Price, Location, Building sqm, Land sqm, Year Built, Condition, Rooms, Hazard (flood/landslide/tsunami), Lifestyle Tags, Match Score, What's Risky
   - Highlight best/worst values in each row (green for best, rose for worst)
   - Use glass-card for each column
   - Mobile: horizontal scroll
   - "Add to Compare" button on PropertyCard and detail page that adds the ID to a local compare list (max 3)

4. Create a useCompare hook (hooks/useCompare.js):
   - Stores compare list in localStorage
   - addToCompare(propertyId), removeFromCompare(propertyId), clearCompare()
   - isInCompare(propertyId)
   - compareIds (array, max 3)
   - Show a floating "Compare (N)" button at bottom of screen when 2+ items selected

Keep it functional and clean. Dark theme.
```

---

## PROMPT 10 — Stripe Subscription + Pricing Page

```
Build the payment system with Stripe.

1. app/pricing/page.js — Pricing page
   - Two tiers displayed side by side:

   FREE:
   - Browse up to 10 properties per day
   - Basic filters (price, prefecture)
   - Limited property details
   - CTA: "Start Free"

   PRO — $10/month:
   - Unlimited property access
   - All filters (lifestyle, hazard, condition)
   - Full "What to Know" reports
   - Save & Compare properties
   - Personalized match scores
   - CTA: "Subscribe Now"

   - Use glass-card style, highlight Pro tier with accent border
   - FAQ section below: billing, cancellation, etc.

2. app/api/stripe/checkout/route.js — POST endpoint
   - Creates a Stripe Checkout Session in 'subscription' mode
   - Uses STRIPE_PRICE_ID from env
   - success_url: /account?success=true
   - cancel_url: /pricing
   - Passes Supabase user ID as client_reference_id
   - Requires authentication

3. app/api/stripe/webhook/route.js — POST endpoint
   - Verifies Stripe webhook signature
   - Handles events:
     * checkout.session.completed → set subscription_status = 'active', save stripe_customer_id and stripe_subscription_id
     * customer.subscription.updated → update status
     * customer.subscription.deleted → set status = 'cancelled'
   - Updates user_profiles table via Supabase service role client

4. app/api/stripe/portal/route.js — POST endpoint
   - Creates a Stripe Customer Portal session for managing subscription
   - Redirects to Stripe portal

5. app/account/page.js — Account page (requires auth)
   - Display: name, email, subscription status
   - If subscribed: "Manage Subscription" button (→ Stripe portal)
   - If free: "Upgrade to Pro" button (→ Stripe checkout)
   - Quiz answers summary + "Retake Quiz" link

6. Create a lib/subscription.js helper:
   - isSubscribed(userId) — checks user_profiles.subscription_status === 'active'
   - Used in middleware/server components to gate features

7. GATING LOGIC — update existing pages:
   - Browse: free users see max 10 results, with a CTA to subscribe for more
   - Property detail: free users don't see the "What to Know" section — show blurred placeholder + CTA
   - Saved/Compare: redirect free users to pricing page
   - Quiz: available to all (it's a conversion funnel)
```

---

## PROMPT 11 — Admin Dashboard

```
Build a basic admin dashboard for reviewing and managing properties.

1. app/admin/layout.js — Admin layout
   - Check if user email is in an ADMIN_EMAILS array (hardcoded for now, e.g., ['roluron@gmail.com'])
   - If not admin: redirect to /
   - Simple sidebar nav: Dashboard, Review Queue, Sources

2. app/admin/page.js — Dashboard
   - Stats cards: Total properties, Pending review, Approved, Published, Total users, Active subscribers
   - Query properties and user_profiles tables with Supabase service role
   - Recent scrape runs from scrape_runs table

3. app/admin/review/page.js — Review Queue
   - Table of properties WHERE admin_status = 'pending_review', ordered by quality_score DESC
   - Columns: thumbnail, title_en, prefecture, price, quality_score, source, created_at
   - Click row to expand: show full detail + images + hazard + what-to-know
   - Actions per property:
     * Approve (set admin_status = 'approved', is_published = true)
     * Reject (set admin_status = 'rejected')
     * Edit title_en / summary_en inline
     * Re-run enrichment (flag for pipeline to re-process — set a column)
   - Bulk actions: approve all with quality_score > 0.7
   - Pagination

4. app/admin/sources/page.js — Source Status
   - Table of sources: name, last_run_at, last_run_status, last_run_count, is_active
   - Recent scrape_runs per source
   - Toggle is_active

Keep admin pages FUNCTIONAL, not beautiful. Dark theme matches the rest but less polish is fine. Use basic table layouts. No fancy animations needed.
```

---

## PROMPT 12 — SEO + Polish + Deploy Prep

```
Final polish pass for CheapHouse Japan before deployment.

1. SEO:
   - Add generateMetadata() to browse page (dynamic title based on filters)
   - Add generateMetadata() to property detail (property title, description, og:image from thumbnail)
   - Create app/sitemap.js that generates a sitemap from all published properties
   - Create app/robots.js with standard rules
   - Add structured data (JSON-LD) to property pages: Product schema with price, location

2. Performance:
   - Add loading.js skeleton files for browse and property pages
   - Add error.js boundary for browse and property pages
   - Ensure all images use Next.js Image with proper sizes/priority
   - Add appropriate cache headers (revalidate: 3600 for browse, 1800 for detail)

3. Empty/Error states:
   - Browse with no results: "No properties match your filters. Try broadening your search."
   - Property not found: nice 404 with link to browse
   - Auth required: redirect with return URL param

4. Create a not-found.js at app level — styled 404 page

5. Responsive check:
   - Ensure all pages work on mobile (375px width)
   - Nav collapses to hamburger on mobile
   - Property grid goes single column
   - Compare view scrolls horizontally

6. Update package.json scripts to include:
   - "build": "next build"
   - Verify build succeeds with no errors

7. Create a .env.local.example with all required variables documented

Make sure everything is production-ready. No console.logs, no TODO comments, no broken links.
```

---

## ORDRE D'EXÉCUTION RÉSUMÉ

| # | Prompt | Temps estimé | Dépendances |
|---|--------|-------------|-------------|
| 1 | Setup Supabase + deps | 15 min | Rien |
| 2 | SQL migration | 10 min | Projet Supabase créé |
| 3 | Nav + Footer | 20 min | Prompt 1 |
| 4 | Homepage | 30 min | Prompt 3 |
| 5 | Browse Properties | 45 min | Prompts 1-3 + data en base |
| 6 | Property Detail | 45 min | Prompt 5 |
| 7 | Auth | 20 min | Prompt 1 |
| 8 | Quiz + Matching | 30 min | Prompt 7 |
| 9 | Saved + Compare | 30 min | Prompts 7-8 |
| 10 | Stripe + Pricing | 30 min | Prompt 7 |
| 11 | Admin Dashboard | 30 min | Prompts 1-2 |
| 12 | SEO + Polish | 20 min | Tout |

**Total : ~5-6 heures de prompts Antigravity** pour un MVP complet.

---

## NOTES IMPORTANTES

### Avant de commencer
1. Crée ton projet Supabase sur supabase.com
2. Run le schema.sql existant (dans /ingestion/schema.sql) dans le SQL Editor Supabase
3. Run la migration_001_users.sql (prompt 2) juste après
4. Run le pipeline d'ingestion pour avoir de la data : `python run.py scrape --source old-houses-japan && python run.py pipeline`
5. Approve quelques propriétés manuellement dans Supabase (UPDATE properties SET admin_status = 'approved', is_published = true WHERE quality_score > 0.6)

### Si Antigravity galère
- Rappelle-lui de regarder globals.css pour le design system
- Rappelle-lui le schema.sql pour la structure des données
- Si un composant ne matche pas le style : "Use the CSS classes from globals.css, not custom styles. The design system is already defined."

### Stack confirmé
- Next.js 16 (App Router, JS pas TS)
- CSS Modules + globals.css (PAS Tailwind — le design system est custom)
- Supabase (Postgres + Auth + RLS)
- Stripe (Checkout + Webhooks)
- Vercel (deploy)
