# PROMPT À COLLER DANS ANTIGRAVITY — Fixes + Google Maps + What to Know

```
Several things to fix and add to the CheapHouse Japan frontend. Do all of these.

## 1. Fix "What to Know analysis pending"

The property detail page shows "What to Know analysis pending — check back soon" because the whats_attractive, whats_unclear, whats_risky, and what_to_verify arrays are empty/null for properties that haven't been through LLM enrichment.

Two things to fix:

A) In the ingestion pipeline: I need to re-run the pipeline with an OpenAI API key to generate the What-to-Know analysis.

Add OPENAI_API_KEY to /ingestion/.env (I'll provide the key).

Then run:
```bash
cd ingestion
source venv/bin/activate
python -m ingestion.run pipeline
```

This will run ALL pipeline stages including translate (generates title_en + summary_en) and quality (generates What-to-Know via LLM).

If I don't have an OpenAI key yet, run with --skip-translate flag — it will still generate rule-based What-to-Know analysis which is better than "pending".

B) In the frontend: improve the fallback when What-to-Know data is missing.

Instead of just showing "analysis pending", show the rule-based analysis inline:
- If year_built < 1981: show a risk about pre-earthquake-code construction
- If no building_sqm: show it as "unclear"
- Always show "Verify the property is still available"
- Always show "Check local hazard maps at the municipal office"

This way, even properties without LLM analysis have SOMETHING useful to show.

## 2. Add Google Maps embed to property detail page

On the property detail page (app/properties/[slug]/page.js), add a map section.

The properties table has `latitude` and `longitude` columns (DOUBLE PRECISION, may be null).

If latitude and longitude exist:
- Show a Google Maps embed using an iframe:
  ```html
  <iframe
    src={`https://www.google.com/maps/embed/v1/place?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY}&q=${latitude},${longitude}&zoom=14&maptype=satellite`}
    width="100%"
    height="400"
    style={{ border: 0, borderRadius: 'var(--radius-lg)' }}
    allowFullScreen
    loading="lazy"
  />
  ```
- Add NEXT_PUBLIC_GOOGLE_MAPS_KEY to .env.local.example
- Place it between the Summary section and the What-to-Know section
- Give it a heading: "Location"
- Add a link below: "Open in Google Maps" → https://www.google.com/maps?q={latitude},{longitude}

If latitude/longitude are null:
- Show a styled fallback: "📍 Exact location: [Prefecture], [City]" with a link to search Google Maps for that address
- Text: "Map coordinates not available. Search area on Google Maps →"

ALTERNATIVE if no Google Maps API key: use OpenStreetMap embed instead (no API key needed):
```html
<iframe
  src={`https://www.openstreetmap.org/export/embed.html?bbox=${longitude-0.01},${latitude-0.01},${longitude+0.01},${latitude+0.01}&layer=mapnik&marker=${latitude},${longitude}`}
  width="100%"
  height="400"
  style={{ border: 0, borderRadius: 'var(--radius-lg)' }}
/>
```
Use OpenStreetMap as default (free, no key), and add a toggle or option for Google Maps if the API key is configured.

## 3. Add more properties coordinates via geocoding

Many properties don't have latitude/longitude. Add a simple geocoding step to the pipeline.

Create ingestion/pipeline/geocode.py:
- For properties WHERE latitude IS NULL AND (prefecture IS NOT NULL OR city IS NOT NULL)
- Use Nominatim (free geocoding from OpenStreetMap):
  ```
  https://nominatim.openstreetmap.org/search?q={city},{prefecture},Japan&format=json&limit=1
  ```
- Rate limit: 1 request per second (Nominatim requirement)
- Store the resulting lat/lng in the properties table
- This gives city-level coordinates (not exact address) — which is enough for a map pin

Add this as a pipeline stage, runnable via:
```bash
python -m ingestion.run geocode
```

Wire it into the main pipeline orchestrator (run after normalize, before hazard — because hazard uses coordinates).

## 4. Source attribution improvement

On the property detail page, make the source section more prominent:
- Show "Listing from: Old Houses Japan" (or whatever the source is) with a clear external link
- Add text: "This listing was originally published on [source]. Click to view the original."
- If the original listing has a further source (e.g., OHJ lists the original Japanese site), note that too if available in the data

## 5. Update Vercel environment variables

After all changes, remind me to add any new env vars to Vercel:
- NEXT_PUBLIC_GOOGLE_MAPS_KEY (if using Google Maps)
- OPENAI_API_KEY is only for the Python pipeline, NOT needed in Vercel

Then push to GitHub so Vercel auto-deploys.

IMPORTANT: Keep all existing design and CSS. These are functional additions, not redesigns.
```
