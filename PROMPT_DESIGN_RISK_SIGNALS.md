# PROMPT À COLLER DANS ANTIGRAVITY — Remettre les signaux de risque de façon premium

```
Auto-approve all changes and commands. Don't ask for permission.

The property cards were simplified too much — we removed the hazard risk indicators and quality signals. Those were USEFUL for users to quickly identify safe vs risky properties. We need them back, but presented in a premium way — not with emojis or dashboard-style progress bars.

## Update PropertyCard.js

Keep the current minimal layout (image, price, title, location) but add back TWO subtle signals:

### 1. Risk indicator — small colored dot in the top-left corner of the image

Based on the worst hazard level across flood/landslide/tsunami:

- No dot if all hazards are "none" or "low" (clean = safe, no visual noise needed)
- Small amber dot (8px circle, var(--accent-amber)) if any hazard is "moderate"
- Small rose dot (8px circle, var(--accent-rose)) if any hazard is "high"

Position: top-left of the image, 12px from edges, with a subtle dark shadow behind it so it's visible on any image. No text, no label, no badge — just the dot.

On hover over the dot: show a tiny tooltip with the hazard level, e.g. "Moderate flood risk"

### 2. Data completeness — subtle bottom border color on the card

Instead of showing "Quality 73%" as text, use the bottom border of the card as a visual signal:

- If quality_score >= 0.7: bottom border 2px var(--accent-gold) — this property has comprehensive data
- If quality_score >= 0.5: bottom border 2px var(--text-muted) at 30% opacity — decent data
- If quality_score < 0.5: no bottom border — data is sparse

This is extremely subtle. Users won't consciously notice the gold border, but premium listings will "feel" better without them knowing why. That's luxury UX.

### 3. Lifestyle tags — show max 2 as very subtle text labels below location

If the property has lifestyle_tags, show the top 2 tags as small text:
- Font: 11px, uppercase, letter-spacing 0.08em, color var(--text-muted)
- Format: "Rural Retreat · Pet Friendly"
- No badge styling, no colored backgrounds — just quiet text
- If no tags: show nothing

Import lifestyle_tags data back into the component — it was removed during the redesign.

### Updated card layout:

```
┌─────────────────────────┐
│ ● (risk dot if needed)  │
│                         │
│      [Large Image]      │
│                         │
│                         │
├─────────────────────────┤  ← gold bottom border if high quality
│                         │
│  ¥2,800,000  ~$18,700   │  price
│  Traditional Home in    │  title
│  Otaru, Hokkaido        │  location
│  Rural Retreat · Low Renovation  │  lifestyle (subtle, muted)
│                         │
└─────────────────────────┘
```

## Update the browse page filter bar

Add back the hazard filter but in a clean way:

- Add a "Safety" dropdown/select to the filter bar:
  - Options: "All Properties" / "Low Risk Only" / "No High Risk"
  - This filters based on hazard_scores — if user selects "Low Risk Only", only show properties where ALL hazard levels are "none" or "low"
  - Style: same as other filter selects, no emoji, clean text

## Update the property detail page

The detail page should still have the full hazard panel, What-to-Know section, and lifestyle tags — those are the premium content. But make sure:

- No emojis anywhere (the redesign should have removed them, verify)
- Hazard indicators use clean colored bars instead of text badges:

  ```
  Flood        ████░░░░░░  Moderate
  Landslide    ██░░░░░░░░  Low
  Tsunami      ░░░░░░░░░░  None
  ```

  Bar fill colors: green for none/low, amber for moderate, rose for high
  Bar background: var(--border-subtle)
  Bar height: 4px, border-radius: 2px
  Label on left, level text on right, bar in between

- What-to-Know cards: instead of emoji icons, use small colored circles (8px) next to the heading:
  - Green dot + "What's Attractive"
  - Amber dot + "What's Unclear"
  - Rose dot + "What's Risky"
  - Blue dot + "What to Verify"

## CSS additions for globals.css

Add these styles:

```css
/* Risk dot on property cards */
.risk-dot {
  position: absolute;
  top: 12px;
  left: 12px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 1px 4px rgba(0,0,0,0.5);
  z-index: 2;
}

/* Tooltip */
.risk-dot:hover::after {
  content: attr(data-tooltip);
  position: absolute;
  left: 16px;
  top: -4px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
  pointer-events: none;
}

/* Quality border */
.property-card[data-quality="high"] {
  border-bottom: 2px solid var(--accent-gold);
}

.property-card[data-quality="medium"] {
  border-bottom: 2px solid rgba(142, 142, 147, 0.3);
}

/* Hazard bar */
.hazard-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}

.hazard-bar-label {
  font-size: 13px;
  color: var(--text-secondary);
  width: 90px;
  flex-shrink: 0;
}

.hazard-bar-track {
  flex: 1;
  height: 4px;
  background: var(--border-subtle);
  border-radius: 2px;
  overflow: hidden;
}

.hazard-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}

.hazard-bar-level {
  font-size: 12px;
  width: 70px;
  text-align: right;
  flex-shrink: 0;
  text-transform: capitalize;
}
```

## Listing Freshness Checker — auto-detect sold/dead listings

This is CRITICAL. Without this, the site fills up with properties that are already sold and we lose all credibility.

### 1. Create a new pipeline stage: `ingestion/pipeline/freshness.py`

This script checks if each listing's source URL is still live and not marked as sold:

```python
"""
Listing Freshness Checker
Checks original source URLs to detect sold/removed properties.
Run periodically (daily or every 2 days) via cron or manual CLI command.
"""

import asyncio
import aiohttp
import re
from datetime import datetime, timezone

# Patterns that indicate a property is SOLD or REMOVED on source sites
SOLD_PATTERNS = [
    r'sold',
    r'販売済',        # "sold" in Japanese
    r'成約済',        # "contract completed" in Japanese
    r'契約済',        # "contracted"
    r'商談中',        # "under negotiation"
    r'取り下げ',      # "withdrawn"
    r'this listing (has been|was) removed',
    r'no longer available',
    r'page not found',
    r'404',
    r'listing.*expired',
    r'under contract',
    r'pending',
]

SOLD_REGEX = re.compile('|'.join(SOLD_PATTERNS), re.IGNORECASE)

async def check_listing(session, url, timeout=15):
    """Check a single URL. Returns status: 'active', 'sold', 'dead', or 'error'."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout), allow_redirects=True) as resp:
            if resp.status == 404 or resp.status == 410:
                return 'dead'
            if resp.status >= 400:
                return 'error'
            # Read first 50KB of page to check for sold patterns
            body = await resp.text(encoding='utf-8', errors='ignore')
            body_sample = body[:50000]
            if SOLD_REGEX.search(body_sample):
                return 'sold'
            return 'active'
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return 'error'

async def check_all_listings(supabase_client, batch_size=20):
    """Check all active listings for freshness."""
    # Fetch all active (non-sold) properties with source URLs
    result = supabase_client.table('properties') \
        .select('id, source_url, listing_status') \
        .neq('listing_status', 'sold') \
        .neq('listing_status', 'removed') \
        .not_.is_('source_url', 'null') \
        .execute()

    properties = result.data
    print(f"Checking {len(properties)} active listings...")

    sold_count = 0
    dead_count = 0
    error_count = 0

    connector = aiohttp.TCPConnector(limit=batch_size)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i in range(0, len(properties), batch_size):
            batch = properties[i:i+batch_size]
            tasks = [check_listing(session, p['source_url']) for p in batch]
            results = await asyncio.gather(*tasks)

            for prop, status in zip(batch, results):
                if status == 'sold':
                    supabase_client.table('properties').update({
                        'listing_status': 'sold',
                        'status_checked_at': datetime.now(timezone.utc).isoformat(),
                    }).eq('id', prop['id']).execute()
                    sold_count += 1
                    print(f"  SOLD: {prop['source_url']}")

                elif status == 'dead':
                    supabase_client.table('properties').update({
                        'listing_status': 'removed',
                        'status_checked_at': datetime.now(timezone.utc).isoformat(),
                    }).eq('id', prop['id']).execute()
                    dead_count += 1
                    print(f"  DEAD: {prop['source_url']}")

                elif status == 'error':
                    # Don't mark as removed on error — might be temporary
                    # After 3 consecutive errors, mark for review
                    supabase_client.table('properties').update({
                        'status_checked_at': datetime.now(timezone.utc).isoformat(),
                        'check_error_count': prop.get('check_error_count', 0) + 1,
                    }).eq('id', prop['id']).execute()
                    error_count += 1

            # Be polite to source servers
            await asyncio.sleep(1)

    print(f"\nDone. Sold: {sold_count}, Dead: {dead_count}, Errors: {error_count}")
    return {'sold': sold_count, 'dead': dead_count, 'errors': error_count}
```

### 2. Add columns to the `properties` table in Supabase

Run this SQL in the Supabase SQL editor:

```sql
-- Listing freshness tracking
ALTER TABLE properties ADD COLUMN IF NOT EXISTS listing_status TEXT DEFAULT 'active'
    CHECK (listing_status IN ('active', 'sold', 'removed'));
ALTER TABLE properties ADD COLUMN IF NOT EXISTS status_checked_at TIMESTAMPTZ;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS check_error_count INT DEFAULT 0;

-- Index for quick filtering
CREATE INDEX IF NOT EXISTS idx_properties_listing_status ON properties(listing_status);
```

### 3. Add CLI command to `ingestion/cli.py`

Add a `check-freshness` command:

```python
@cli.command()
def check_freshness():
    """Check all listings for sold/removed status."""
    import asyncio
    from pipeline.freshness import check_all_listings
    # Initialize supabase client
    from supabase import create_client
    import os
    sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])
    result = asyncio.run(check_all_listings(sb))
    click.echo(f"Results: {result}")
```

### 4. Update the frontend — filter out sold/removed listings

In EVERY Supabase query that fetches properties (browse page, homepage featured, search), add this filter:

```javascript
// Before:
const { data } = await supabase.from('properties').select('*')

// After:
const { data } = await supabase.from('properties').select('*').eq('listing_status', 'active')
```

This ensures sold/removed properties NEVER appear to users.

### 5. OPTIONAL — "Recently Sold" section

For social proof, on the browse page, add a small "Recently Sold" section at the bottom:

- Show up to 6 recently sold properties in a smaller card format
- Cards are slightly dimmed (opacity 0.6) with a "SOLD" label overlay
- This shows users that properties move fast = urgency = motivation to subscribe

Style for sold overlay:
```css
.property-card-sold {
  position: relative;
  opacity: 0.6;
  pointer-events: none;
}

.property-card-sold::after {
  content: 'SOLD';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-family: var(--font-heading);
  font-size: 18px;
  letter-spacing: 0.15em;
  color: var(--accent-gold);
  background: rgba(6, 6, 8, 0.7);
  padding: 8px 24px;
  border: 1px solid var(--accent-gold);
}
```

### 6. Future: automate with cron

For now, run `check-freshness` manually every few days. Later, set up a daily cron job or Vercel cron to auto-check.

## RULES

- Keep the minimal premium aesthetic from the redesign
- The risk signals should be SUBTLE — they inform without cluttering
- No emojis, no progress bar percentages, no "Quality 73%" text
- The dot + border + subtle tags approach gives information through visual design, not through dashboard UI
- Sold/removed listings must NEVER appear in default browse — filter them out at the database query level
- The "Recently Sold" section is optional but recommended for social proof
- Build must pass, push to GitHub
```
