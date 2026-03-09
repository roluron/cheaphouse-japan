# PROMPT: USA Scrapers — Cheap Houses in America

> Paste this prompt in a **separate Antigravity window** (same project folder). It builds adapters for US property sites using the same BaseAdapter pattern.

---

## Context

We have a working ingestion pipeline for Japan in `ingestion/adapters/`. Each adapter extends `BaseAdapter` and implements `get_listing_urls()` + `extract_listing(url)`. We're now expanding to the **USA** — focusing on **cheap/affordable houses** for international buyers.

The USA has a unique market: houses under $50K exist in many states (Detroit, Cleveland, Pittsburgh, rural South, Midwest). The target audience is the same — people looking for affordable real estate adventures.

---

## 1. Directory Structure

```
ingestion/
  adapters/
    usa/
      __init__.py              # USA adapter registry
      zillow_us.py             # Zillow (hard — API deprecated, scraping difficult)
      realtor_com.py           # Realtor.com (medium)
      redfin_us.py             # Redfin (has CSV download!)
      cheap_old_houses.py      # CheapOldHouses.com (curated — perfect fit)
      landwatch_us.py          # LandWatch.com (rural + land + houses)
      auction_com.py           # Auction.com (foreclosures)
```

---

## 2. USA BaseAdapter

Create `ingestion/adapters/usa/base_usa.py`:

```python
"""
USA adapter base class.
Extends BaseAdapter with USD price handling and US address parsing.
"""

from ingestion.base_adapter import BaseAdapter

class USABaseAdapter(BaseAdapter):
    """Base for all USA adapters."""

    country: str = "usa"
    currency: str = "USD"
    default_language: str = "en"

    PRICE_THRESHOLD = 100_000  # $100K max for "cheap" houses

    # Target states with cheap housing:
    # Midwest: Ohio, Michigan, Indiana, Kansas, Missouri
    # South: Mississippi, Alabama, Arkansas, West Virginia
    # Rust Belt: Pennsylvania, upstate New York
    TARGET_STATES = [
        "OH", "MI", "IN", "KS", "MO",
        "MS", "AL", "AR", "WV",
        "PA", "NY",
    ]
```

---

## 3. Utility Functions

Create `ingestion/utils_usa.py`:

```python
"""
USA price and address utilities.
"""

import re
from typing import Optional

def parse_price_usd(text: str) -> Optional[int]:
    """
    Parse USD price formats:
    - "$85,000"
    - "$85K"
    - "85000"
    - "$1.2M" (filter out — too expensive)
    """
    if not text:
        return None

    text = text.strip().upper()

    # Handle K shorthand: "$85K" → 85000
    k_match = re.search(r'\$?([\d,.]+)\s*K', text)
    if k_match:
        return int(float(k_match.group(1).replace(',', '')) * 1000)

    # Handle M shorthand: "$1.2M" → 1200000
    m_match = re.search(r'\$?([\d,.]+)\s*M', text)
    if m_match:
        val = int(float(m_match.group(1).replace(',', '')) * 1_000_000)
        return val if val <= 200_000 else None  # Skip expensive ones

    # Standard: "$85,000" or "85000"
    cleaned = re.sub(r'[^\d]', '', text)
    if not cleaned:
        return None
    price = int(cleaned)
    return price if price <= 500_000 else None  # Sanity cap

def parse_area_sqft(text: str) -> Optional[float]:
    """Parse area in sq ft: '1,200 sqft', '1200 sq ft'."""
    if not text:
        return None
    match = re.search(r'([\d,]+)\s*(?:sqft|sq\.?\s*ft|sf)', text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', ''))
    return None

def sqft_to_sqm(sqft: float) -> float:
    """Convert square feet to square meters."""
    return round(sqft * 0.0929, 1)

def usd_to_jpy(usd: int) -> int:
    """Rough USD→JPY for cross-country comparison."""
    return int(usd * 150)  # ~150 JPY/USD as of 2026

def parse_us_address(address: str) -> dict:
    """
    Parse US address into components.
    '123 Main St, Cleveland, OH 44101' →
    {'street': '123 Main St', 'city': 'Cleveland', 'state': 'OH', 'zip': '44101'}
    """
    parts = [p.strip() for p in address.split(',')]
    result = {'street': '', 'city': '', 'state': '', 'zip': ''}

    if len(parts) >= 1:
        result['street'] = parts[0]
    if len(parts) >= 2:
        result['city'] = parts[1]
    if len(parts) >= 3:
        # "OH 44101" or "OH"
        state_zip = parts[2].strip().split()
        result['state'] = state_zip[0] if state_zip else ''
        result['zip'] = state_zip[1] if len(state_zip) > 1 else ''

    return result
```

---

## 4. Adapters

### 4a. CheapOldHouses.com (PRIORITY — perfect fit!)

```python
# ingestion/adapters/usa/cheap_old_houses.py
"""
CheapOldHouses.com — curated historic/cheap houses across America.
This is THE perfect source: focuses specifically on cheap houses with character.
Easy to scrape, curated content, great photos.
"""

class CheapOldHousesAdapter(USABaseAdapter):
    slug = "cheap-old-houses-us"
    base_url = "https://cheapoldhouses.com"

    # Scraping strategy:
    # 1. Browse main listing feed (blog-style layout)
    # 2. Each post = one house with price, location, photos, description
    # 3. Simple HTML, minimal JS
    # 4. Pagination: standard page numbers or infinite scroll
    # 5. Delay: 2s between requests
    # 6. Extract: title, price, city/state, sqft, year built, photos, description

    # This site is curated (human-selected listings) so quality is high.
    # All listings are under $150K, most under $100K.
    # Many are historic/Victorian/craftsman — great for the "adventure buyer".

    REQUEST_DELAY = 2
```

### 4b. Redfin (Has CSV download!)

```python
# ingestion/adapters/usa/redfin_us.py
"""
Redfin — major US real estate portal.
BEST APPROACH: Redfin offers CSV data download from search results!
No scraping needed — just download the CSV.
Target: houses under $100K in target states.
"""

class RedfinUSAdapter(USABaseAdapter):
    slug = "redfin-us"
    base_url = "https://www.redfin.com"

    # Redfin CSV strategy:
    # 1. Build search URL per target state:
    #    redfin.com/state/Ohio/filter/max-price=100k,property-type=house
    # 2. Append /csv to the search URL → direct CSV download
    #    OR use the "Download All" button URL pattern
    # 3. Parse CSV (pandas): columns include price, address, beds, baths,
    #    sqft, year_built, url, latitude, longitude
    # 4. One CSV per state per day
    # 5. No rate limiting concerns since it's a single download per state

    # CSV columns (typical):
    # SALE TYPE, SOLD DATE, PROPERTY TYPE, ADDRESS, CITY, STATE OR PROVINCE,
    # ZIP OR POSTAL CODE, PRICE, BEDS, BATHS, LOCATION, SQUARE FEET,
    # LOT SIZE, YEAR BUILT, DAYS ON MARKET, $/SQUARE FEET, HOA/MONTH,
    # STATUS, URL, LATITUDE, LONGITUDE

    # This is the cleanest data source — structured CSV, no scraping needed.
    CSV_URL_TEMPLATE = (
        "https://www.redfin.com/stingray/api/gis-csv"
        "?al=1&market=false&max_price=100000"
        "&num_homes=350&ord=redfin-recommended-asc"
        "&page_number=1&property_type=house"
        "&region_id={region_id}&region_type=2&status=9"
        "&uipt=1&v=8"
    )

    # Region IDs for target states (look up from Redfin):
    STATE_REGION_IDS = {
        "OH": 35,   # Ohio
        "MI": 23,   # Michigan
        "IN": 14,   # Indiana
        "PA": 39,   # Pennsylvania
        "WV": 49,   # West Virginia
        "MS": 25,   # Mississippi
        "AL": 1,    # Alabama
        "AR": 4,    # Arkansas
        "KS": 16,   # Kansas
        "MO": 26,   # Missouri
    }

    REQUEST_DELAY = 5  # Be polite even with CSV downloads
```

### 4c. Realtor.com

```python
# ingestion/adapters/usa/realtor_com.py
"""
Realtor.com — official site of the National Association of Realtors.
Medium scraping difficulty. Good coverage of cheap rural properties.
"""

class RealtorComAdapter(USABaseAdapter):
    slug = "realtor-com"
    base_url = "https://www.realtor.com"

    # Search URL pattern:
    # realtor.com/realestateandhomes-search/Cleveland_OH/price-na-100000/type-single-family-home

    TARGET_CITIES = [
        # Ohio
        "Cleveland_OH", "Youngstown_OH", "Dayton_OH", "Akron_OH",
        # Michigan
        "Detroit_MI", "Flint_MI", "Saginaw_MI",
        # Pennsylvania
        "Pittsburgh_PA", "Scranton_PA",
        # Indiana
        "Indianapolis_IN", "Gary_IN",
        # Others
        "Memphis_TN", "Birmingham_AL", "Jackson_MS",
        "Little-Rock_AR", "St-Louis_MO",
    ]

    # Anti-scraping: moderate
    # - Rate limiting
    # - Cloudflare protection
    # - JSON data in script tags (useful!)

    # Strategy:
    # 1. Search by city with price filter
    # 2. Look for __NEXT_DATA__ JSON in <script> tags (Next.js site)
    # 3. Parse structured JSON instead of HTML scraping
    # 4. Delay: 5-8 seconds
    # 5. Limit: 200 per city per run

    REQUEST_DELAY = (5, 8)
    MAX_PER_CITY = 200
```

### 4d. LandWatch.com (Rural + Land)

```python
# ingestion/adapters/usa/landwatch_us.py
"""
LandWatch.com — rural land and houses.
Good for finding cheap rural properties with land.
Target: houses with land under $100K.
"""

class LandWatchUSAdapter(USABaseAdapter):
    slug = "landwatch-us"
    base_url = "https://www.landwatch.com"

    # Search: landwatch.com/ohio/houses-for-sale?price-max=100000
    # Good rural coverage, many cheap properties with acreage

    # Strategy:
    # 1. Search by state with price filter
    # 2. Standard pagination
    # 3. Cards: price, acreage, location, property type
    # 4. Delay: 3-5 seconds
    # 5. Focus on "house" property type (not raw land)

    REQUEST_DELAY = (3, 5)
```

### 4e. Auction.com (Foreclosures)

```python
# ingestion/adapters/usa/auction_com.py
"""
Auction.com — foreclosure and bank-owned properties.
Cheapest US properties but require quick action.
Target: houses under $50K.
"""

class AuctionComAdapter(USABaseAdapter):
    slug = "auction-com"
    base_url = "https://www.auction.com"

    # These are foreclosures / bank-owned (REO) properties.
    # Prices start extremely low but:
    # - May need significant renovation
    # - Auction deadlines
    # - Cash buyers preferred

    # Strategy:
    # 1. Search by state with "Residential" property type
    # 2. Filter: max price $50K
    # 3. Extract: auction date, current bid, property details
    # 4. Delay: 3-5 seconds
    # 5. Tag as "auction" in listing type

    # LLM enrichment should note: "This is a foreclosure auction property.
    # Requires quick action, cash preferred, property sold as-is."

    PRICE_THRESHOLD = 50_000
    REQUEST_DELAY = (3, 5)
```

---

## 5. USA Adapter Registry

`ingestion/adapters/usa/__init__.py`:

```python
"""
USA adapter registry.
"""

from ingestion.adapters.usa.cheap_old_houses import CheapOldHousesAdapter
from ingestion.adapters.usa.redfin_us import RedfinUSAdapter
from ingestion.adapters.usa.realtor_com import RealtorComAdapter
from ingestion.adapters.usa.landwatch_us import LandWatchUSAdapter
from ingestion.adapters.usa.auction_com import AuctionComAdapter

USA_ADAPTER_MAP: dict[str, type] = {
    "cheap-old-houses-us": CheapOldHousesAdapter,  # Easy — curated, perfect fit
    "redfin-us": RedfinUSAdapter,                    # Easy — CSV download!
    "realtor-com": RealtorComAdapter,                # Medium — JSON in script tags
    "landwatch-us": LandWatchUSAdapter,              # Medium — rural specialist
    "auction-com": AuctionComAdapter,                # Medium — foreclosures
}
```

---

## 6. Update Main Registry

In `ingestion/adapters/__init__.py`, add:

```python
from ingestion.adapters.usa import USA_ADAPTER_MAP
ADAPTER_MAP.update(USA_ADAPTER_MAP)
```

---

## 7. Update auto_pipeline.py

Add to `SCRAPE_SOURCES`:

```python
# ── USA Sources ────────────────────────────────────────────
{"slug": "cheap-old-houses-us", "limit": 200},  # Curated — easy
{"slug": "redfin-us", "limit": 500},            # CSV download — easy
{"slug": "realtor-com", "limit": 300},           # Medium
{"slug": "landwatch-us", "limit": 300},          # Medium — rural
{"slug": "auction-com", "limit": 200},           # Medium — foreclosures
```

---

## 8. Database Updates

```sql
-- Ensure country column exists
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'japan';

-- USA adapters should set country = 'usa'
-- Add US-specific fields
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS property_tax_annual INTEGER;
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS hoa_monthly INTEGER;
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS lot_size_acres FLOAT;
```

---

## 9. LLM Enrichment — USA Context

Update LLM enrichment prompts for American properties:

- **Lifestyle tags**: "historic Victorian", "craftsman bungalow", "fixer-upper", "rural acreage", "small-town America", "college town", "rust belt revival"
- **What to Know**: property taxes (vary hugely by state/county), HOA fees, inspection contingencies, title insurance, closing costs (~2-5%), foreclosure risks, neighborhood crime data
- **Hazard data**: FEMA flood zones, tornado alley, hurricane zones, wildfire risk (use FEMA API)
- **No translation needed**: All English sources

---

## 10. .env Updates

```bash
# USA config
USA_SCRAPE_DELAY_SECONDS=3
USA_PRICE_MAX=100000
```

---

## Priority Order

1. **CheapOldHouses.com** — perfect fit, easy scrape, curated quality
2. **Redfin CSV** — cleanest structured data, no real scraping
3. **LandWatch** — rural coverage, medium difficulty
4. **Realtor.com** — biggest coverage, medium difficulty
5. **Auction.com** — foreclosures, niche but cheap

Test each:
```bash
cd /Users/test/Documents/CheapHouse\ Japan
source ingestion/venv/bin/activate
python -m ingestion.adapters.usa.cheap_old_houses --test
```
