# PROMPT À COLLER DANS ANTIGRAVITY — Multi-country selector + Coming Soon

```
CheapHouse is expanding beyond Japan. The platform will cover affordable and interesting homes across multiple countries. I need a country selector and a "coming soon" system so visitors can see what's next.

## 1. Country selector on homepage

Before the hero section (or integrated into the nav), add a country selector bar.

Design:
- Horizontal row of country pills/buttons
- Each pill: flag emoji + country name
- Japan is the only ACTIVE country (highlighted, clickable → goes to /browse)
- Other countries show as slightly dimmed with a "Coming Soon" label on hover
- Clicking a "coming soon" country opens a small modal (see step 3)

Countries to show:

| Country | Flag | Status | Slug |
|---------|------|--------|------|
| Japan | 🇯🇵 | Active | jp |
| France | 🇫🇷 | Coming Soon | fr |
| Vietnam | 🇻🇳 | Coming Soon | vn |
| Portugal | 🇵🇹 | Coming Soon | pt |
| Italy | 🇮🇹 | Coming Soon | it |
| Spain | 🇪🇸 | Coming Soon | es |
| Greece | 🇬🇷 | Coming Soon | gr |
| New Zealand | 🇳🇿 | Coming Soon | nz |
| Australia | 🇦🇺 | Coming Soon | au |
| USA | 🇺🇸 | Coming Soon | us |

Style:
- Active country: solid accent border, full opacity, slight glow
- Coming soon: 50% opacity, dashed border, "Coming Soon" text below or as tooltip
- On hover (coming soon): opacity goes to 80%, shows the modal trigger
- The whole row should feel premium and minimal — not a cluttered flag parade
- On mobile: horizontal scroll with the active country first

## 2. Country context in data model

Add a `country` field to the architecture. For now this is frontend-only — no DB changes needed yet.

Create app/lib/countries.js:

```javascript
export const COUNTRIES = [
  {
    code: 'jp',
    name: 'Japan',
    flag: '🇯🇵',
    status: 'active',
    currency: 'JPY',
    tagline: 'Akiya, countryside retreats, and affordable homes',
    propertyCount: null, // will be fetched from DB
  },
  {
    code: 'fr',
    name: 'France',
    flag: '🇫🇷',
    status: 'coming_soon',
    currency: 'EUR',
    tagline: 'Village houses, countryside châteaux, and Mediterranean gems',
    propertyCount: null,
  },
  {
    code: 'vn',
    name: 'Vietnam',
    flag: '🇻🇳',
    status: 'coming_soon',
    currency: 'VND',
    tagline: 'Tropical homes, beach properties, and heritage houses',
    propertyCount: null,
  },
  {
    code: 'pt',
    name: 'Portugal',
    flag: '🇵🇹',
    status: 'coming_soon',
    currency: 'EUR',
    tagline: 'Algarve coast, Lisbon apartments, and rural quintas',
    propertyCount: null,
  },
  {
    code: 'it',
    name: 'Italy',
    flag: '🇮🇹',
    status: 'coming_soon',
    currency: 'EUR',
    tagline: '€1 houses, Tuscan farmhouses, and Sicilian villas',
    propertyCount: null,
  },
  {
    code: 'es',
    name: 'Spain',
    flag: '🇪🇸',
    status: 'coming_soon',
    currency: 'EUR',
    tagline: 'Pueblo houses, coastal apartments, and rural fincas',
    propertyCount: null,
  },
  {
    code: 'gr',
    name: 'Greece',
    flag: '🇬🇷',
    status: 'coming_soon',
    currency: 'EUR',
    tagline: 'Island homes, village houses, and Aegean retreats',
    propertyCount: null,
  },
  {
    code: 'nz',
    name: 'New Zealand',
    flag: '🇳🇿',
    status: 'coming_soon',
    currency: 'NZD',
    tagline: 'Remote cottages, farm stays, and coastal properties',
    propertyCount: null,
  },
  {
    code: 'au',
    name: 'Australia',
    flag: '🇦🇺',
    status: 'coming_soon',
    currency: 'AUD',
    tagline: 'Outback homes, coastal retreats, and bush properties',
    propertyCount: null,
  },
  {
    code: 'us',
    name: 'USA',
    flag: '🇺🇸',
    status: 'coming_soon',
    currency: 'USD',
    tagline: 'Detroit bargains, rural homesteads, and fixer-uppers',
    propertyCount: null,
  },
]

export function getActiveCountries() {
  return COUNTRIES.filter(c => c.status === 'active')
}

export function getComingSoonCountries() {
  return COUNTRIES.filter(c => c.status === 'coming_soon')
}
```

## 3. "Coming Soon" modal with email capture

When a user clicks a coming-soon country, show a modal:

Content:
- Flag + Country name (large)
- Tagline (from the countries data)
- "We're expanding to [Country]. Be the first to know when we launch."
- Email input field
- "Notify Me" button
- Small text: "No spam. One email when we launch."

On submit:
- Save to a Supabase table `waitlist`:
  ```sql
  CREATE TABLE IF NOT EXISTS public.waitlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    country_code TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(email, country_code)
  );
  ```
- Show success: "You're on the list for [Country]! 🎉"
- If email already registered for that country: "You're already on the list!"

This is a REAL growth tool — we'll know which countries have the most demand before we build them.

## 4. Update homepage hero

Change the main headline to be broader (not Japan-specific):
- Before: "Find the right house in Japan. Avoid the wrong one."
- After: "Find your dream home. Anywhere in the world."
- Subheadline: "The decision platform for international buyers. Starting with Japan."
- Keep the same CTAs but the messaging is now global-first

OR keep the Japan headline but add a secondary line:
- "Find the right house in Japan. Avoid the wrong one."
- Below, smaller: "Coming soon: France, Vietnam, Portugal, Italy, and more."

Choose whichever feels better for the design. The key is: Japan is the focus NOW but the visitor should see this is going to be bigger.

## 5. Country-aware URL structure (prepare for future)

Don't implement full routing yet, but set up the pattern:
- Current: /properties, /properties/[slug]
- Future: /jp/properties, /fr/properties, /jp/properties/[slug]

For now, /properties defaults to Japan. Add a redirect so /jp/properties also works:
```javascript
// app/jp/properties/page.js
import { redirect } from 'next/navigation'
export default function Page() { redirect('/properties') }
```

This way when we add France, it'll be /fr/properties and the URL structure is clean.

## 6. Footer update

Add a "Countries" section to the footer:
- Japan (active link)
- France (Coming Soon)
- Vietnam (Coming Soon)
- Portugal (Coming Soon)
- See all →

## 7. Update the site title/branding

The site is currently "CheapHouse Japan". Since we're going multi-country, consider updating:
- Site name: "CheapHouse" (drop "Japan")
- Tagline: "Dream homes around the world"
- Or keep "CheapHouse" with the country as context: "CheapHouse — Japan" in the nav, switchable later

Update metadata in layout.js:
- title: "CheapHouse — Find Dream Homes Around the World"
- description: "The decision platform for international home buyers. Discover, compare, and decide on affordable homes worldwide. Starting with Japan."

## RULES

- Japan is the ONLY working country. Everything else is "coming soon" UI only.
- The country selector must feel premium — not like a cheap dropdown
- The waitlist/email capture is critical — it validates demand for each country
- Don't break any existing Japan functionality
- The Supabase waitlist table needs RLS: allow anonymous inserts but no reads (only admin/service role can read)
- Keep the dark premium design
- Flag emojis render natively — no need for flag image libraries
```
