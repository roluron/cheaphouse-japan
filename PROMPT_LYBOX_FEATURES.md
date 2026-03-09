# PROMPT À COLLER DANS ANTIGRAVITY — Features inspirées de Lybox + Multi-devises

```
I want to add premium calculation and analysis tools to CheapHouse Japan, inspired by Lybox.fr (a French real estate investment analysis platform). These features are for paying subscribers.

## 1. Multi-currency price display

Every property currently shows price in JPY and USD. I want to support more currencies.

Create app/lib/currencies.js:

```javascript
// Exchange rates — update these periodically or fetch from API
const RATES = {
  JPY: 1,
  USD: 0.0067,    // 1 JPY = 0.0067 USD
  EUR: 0.0061,    // 1 JPY = 0.0061 EUR
  GBP: 0.0053,
  CNY: 0.048,
  VND: 168,       // 1 JPY = 168 VND
  AUD: 0.0103,
  NZD: 0.0113,
  CAD: 0.0094,
  SGD: 0.009,
  THB: 0.23,
  KRW: 9.2,
}

export function convertPrice(priceJpy, currency) {
  return Math.round(priceJpy * (RATES[currency] || 1))
}

export function formatCurrency(amount, currency) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: 0,
  }).format(amount)
}

export const SUPPORTED_CURRENCIES = Object.keys(RATES)
```

Add a currency selector dropdown in the navigation bar (or top-right of the page). Store the user's preferred currency in localStorage. Apply it everywhere prices are shown: PropertyCard, detail page, browse filters, compare view.

## 2. Total Cost Calculator (on property detail page)

Add a "True Cost Calculator" section on the property detail page, after the price section. This is a key premium feature — it shows the REAL cost of buying, not just the listing price.

Create a TotalCostCalculator client component:

Inputs (pre-filled with defaults, user can adjust):
- Purchase price: pre-filled from property price_jpy
- Agent fee: default 3% + tax (standard in Japan for properties over ¥4M, 4% for ¥2-4M, 5% for under ¥2M)
- Registration tax: default 2% of assessed value
- Acquisition tax: default 3% for residential
- Stamp duty: based on price brackets (¥1K for <¥5M, ¥5K for ¥5-10M, ¥10K for ¥10-50M)
- Legal/notary fees: default ¥200,000-500,000
- Renovation estimate: based on condition_rating from property data
  - good/fair: ¥0
  - needs_work: building_sqm × ¥30,000
  - significant_renovation: building_sqm × ¥80,000

Display:
- Each line item with amount
- Total at bottom in bold
- Show in user's selected currency
- Bar chart or simple visual breakdown showing what percentage each cost represents
- "This is an estimate. Actual costs may vary. Consult a professional."

This section is GATED — free users see a blurred version with a "Subscribe to see full cost analysis" CTA.

## 3. Renovation Cost Estimator

Add a more detailed renovation section below the Total Cost Calculator:

Based on property data (year_built, building_sqm, condition_rating):

Show estimated costs for common renovation categories:
- Structural reinforcement (if pre-1981): ¥20,000-50,000/sqm
- Roof repair/replacement: ¥500,000-2,000,000
- Kitchen renovation: ¥500,000-2,500,000
- Bathroom renovation: ¥300,000-1,500,000
- Flooring (tatami/wood): ¥5,000-15,000/sqm
- Insulation upgrade: ¥3,000-8,000/sqm
- Electrical rewiring (if pre-1990): ¥300,000-800,000
- Plumbing (if pre-1980): ¥500,000-1,500,000

Show as a checklist — user can toggle which items they think they'll need, and the total updates in real-time.

Also GATED for premium users.

## 4. Area Analysis (like Lybox's city analysis)

Create a new page: app/area/[prefecture]/page.js

For each prefecture, show an analysis dashboard:
- Number of properties available
- Average price
- Price range (min-max)
- Average building size
- Average land size
- Average year built
- Hazard risk summary (how many properties in each risk level)
- Most common lifestyle tags
- A mini-map showing where properties are clustered

Data source: aggregate from the properties table in Supabase, grouped by prefecture.

```sql
SELECT
  prefecture,
  count(*) as property_count,
  avg(price_jpy) as avg_price,
  min(price_jpy) as min_price,
  max(price_jpy) as max_price,
  avg(building_sqm) as avg_building,
  avg(land_sqm) as avg_land,
  avg(year_built) as avg_year
FROM properties
WHERE is_published = true AND admin_status = 'approved'
GROUP BY prefecture
```

Link to area pages from the browse page (clickable prefecture names) and from property detail pages.

## 5. PDF Property Report (upsell feature — build the UI now, PDF generation later)

On the property detail page, add a "Download Report" button (premium only).

For now, just create the button and a modal that says:
"Property reports are coming soon. We'll generate a comprehensive PDF including the full analysis, cost estimates, hazard data, and area context. Subscribe to be notified."

This plants the seed for a future upsell ($5-15 per report).

## 6. Currency selector in Navigation

Add a small currency dropdown in the top-right of the Nav component, next to the login/account buttons:
- Small dropdown showing current currency code (e.g., "USD")
- On click: shows list of supported currencies with their symbols
- Selection saved to localStorage
- All price displays throughout the site update immediately

## IMPORTANT

- Multi-currency and currency selector: available to ALL users (it's a hook to attract international buyers)
- Total Cost Calculator: PREMIUM only (blurred for free users)
- Renovation Estimator: PREMIUM only
- Area Analysis pages: partially free (basic stats), full analysis PREMIUM
- PDF Report: PREMIUM (coming soon placeholder)
- Keep all existing design and CSS
- All calculators should show disclaimer: "Estimates only. Consult a licensed professional."
- Use the user's selected currency everywhere, but always show JPY as the base price too
```
