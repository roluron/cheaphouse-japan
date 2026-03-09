# PROMPT: New Zealand Scrapers — Cheap Houses in NZ

> Paste this prompt in a **separate Antigravity window** (same project folder). It builds adapters for New Zealand property sites using the same BaseAdapter pattern.

---

## Context

We have a working ingestion pipeline for Japan in `ingestion/adapters/`. Each adapter extends `BaseAdapter` and implements `get_listing_urls()` + `extract_listing(url)`. We're expanding to **New Zealand** — focusing on **affordable houses** for international buyers.

New Zealand has a unique appeal: stunning landscapes, English-speaking, friendly visa options. Cheap houses exist in rural South Island and smaller North Island towns. Prices are in NZD.

---

## 1. Directory Structure

```
ingestion/
  adapters/
    nz/
      __init__.py              # NZ adapter registry
      trademe_nz.py            # Trade Me Property (NZ's #1 — has API!)
      realestate_co_nz.py      # realestate.co.nz (#2 portal)
      homes_co_nz.py           # homes.co.nz (property data + valuations)
      one_roof_nz.py           # OneRoof.co.nz (NZ Herald property)
      harcourts_nz.py          # Harcourts (major NZ agency)
```

---

## 2. NZ BaseAdapter

Create `ingestion/adapters/nz/base_nz.py`:

```python
"""
New Zealand adapter base class.
"""

from ingestion.base_adapter import BaseAdapter

class NZBaseAdapter(BaseAdapter):
    """Base for all NZ adapters."""

    country: str = "new-zealand"
    currency: str = "NZD"
    default_language: str = "en"

    # Price threshold: NZD 300K (~USD 180K) — NZ is expensive
    # For truly "cheap" NZ: under NZD 200K in rural areas
    PRICE_THRESHOLD = 300_000

    # Cheapest regions:
    # South Island: West Coast, Southland, Gore, Invercargill
    # North Island: Whanganui, Kawerau, South Waikato, Ōpōtiki
    TARGET_REGIONS = [
        # South Island (cheapest)
        "west-coast", "southland", "gore", "invercargill",
        "timaru", "oamaru", "greymouth",
        # North Island (affordable)
        "whanganui", "kawerau", "south-waikato",
        "opotiki", "tararua", "wairoa",
    ]
```

---

## 3. Utility Functions

Create `ingestion/utils_nz.py`:

```python
"""
New Zealand price and property utilities.
"""

import re
from typing import Optional

def parse_price_nzd(text: str) -> Optional[int]:
    """
    Parse NZD price formats:
    - "$350,000" or "NZ$350,000"
    - "$350K"
    - "Asking price: $280,000"
    - "By Negotiation" → None
    - "Tender" → None
    - "Auction" → None (but flag it)
    """
    if not text:
        return None

    text_upper = text.strip().upper()

    # Non-price listings
    if any(kw in text_upper for kw in ["NEGOTIATION", "TENDER", "AUCTION",
                                         "DEADLINE", "BY NEG", "PBN"]):
        return None  # Price not disclosed

    # Handle K shorthand
    k_match = re.search(r'[\$NZ]*\s*([\d,.]+)\s*K', text_upper)
    if k_match:
        return int(float(k_match.group(1).replace(',', '')) * 1000)

    # Standard price
    cleaned = re.sub(r'[^\d]', '', text)
    if not cleaned:
        return None
    price = int(cleaned)
    return price if price < 10_000_000 else None  # Sanity cap

def parse_area_sqm_nz(text: str) -> Optional[float]:
    """Parse area: '120m²', '120 sqm', '120m2'."""
    if not text:
        return None
    match = re.search(r'([\d,]+\.?\d*)\s*(?:m²|m2|sqm)', text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', ''))
    return None

def parse_land_area_nz(text: str) -> Optional[float]:
    """
    Parse NZ land area (often in m² or hectares):
    - "809m²" → 809.0
    - "2.5 hectares" → 25000.0
    - "1 acre" → 4047.0
    """
    if not text:
        return None

    # Hectares
    ha_match = re.search(r'([\d,.]+)\s*(?:hectares?|ha)', text, re.IGNORECASE)
    if ha_match:
        return float(ha_match.group(1).replace(',', '')) * 10_000

    # Acres
    acre_match = re.search(r'([\d,.]+)\s*(?:acres?|ac)', text, re.IGNORECASE)
    if acre_match:
        return float(acre_match.group(1).replace(',', '')) * 4_047

    # Square meters
    sqm_match = re.search(r'([\d,]+)\s*(?:m²|m2|sqm)', text, re.IGNORECASE)
    if sqm_match:
        return float(sqm_match.group(1).replace(',', ''))

    return None

def nzd_to_jpy(nzd: int) -> int:
    """Rough NZD→JPY for cross-country comparison."""
    return int(nzd * 90)  # ~90 JPY/NZD as of 2026
```

---

## 4. Adapters

### 4a. Trade Me Property (PRIORITY — NZ's #1 + has API!)

```python
# ingestion/adapters/nz/trademe_nz.py
"""
Trade Me Property — New Zealand's dominant marketplace (~80% market share).
HAS AN OFFICIAL API: https://developer.trademe.co.nz/
Register for free API key. This is the best approach.
"""

class TradeMeNZAdapter(NZBaseAdapter):
    slug = "trademe-nz"
    base_url = "https://api.trademe.co.nz"

    # API APPROACH (strongly preferred):
    # 1. Register at developer.trademe.co.nz
    # 2. OAuth 1.0a authentication
    # 3. Search endpoint: /v1/Search/Property/Residential.json
    # 4. Parameters:
    #    - price_max=300000
    #    - property_type=House (or Lifestyle, Section, etc.)
    #    - district=  (filter by region)
    #    - sort_order=ExpiryAsc (newest first)
    #    - rows=50 (per page)
    # 5. Rate limit: 300 requests/day (free tier)
    #    → Budget carefully: ~20 regions × 5 pages = 100 requests

    # Target districts (cheapest):
    DISTRICT_IDS = {
        "west-coast": 28,
        "southland": 27,
        "whanganui": 19,
        "south-waikato": 5,
        "kawerau": 7,
        "opotiki": 7,
        "tararua": 22,
    }

    # API response contains structured JSON:
    # - ListingId, Title, PriceDisplay, Address
    # - Bedrooms, Bathrooms, LandArea, FloorArea
    # - PhotoUrls, District, Suburb
    # - EndDate (auction), StartPrice, BuyNowPrice

    # Fallback: scrape trademe.co.nz/property if API quota exhausted
    FALLBACK_SCRAPE_URL = "https://www.trademe.co.nz/a/property/residential/sale/search"
    FALLBACK_DELAY = (5, 8)

    # Add to .env:
    # TRADEME_CONSUMER_KEY=your-key
    # TRADEME_CONSUMER_SECRET=your-secret
    # TRADEME_OAUTH_TOKEN=your-token
    # TRADEME_OAUTH_TOKEN_SECRET=your-token-secret
```

### 4b. realestate.co.nz

```python
# ingestion/adapters/nz/realestate_co_nz.py
"""
realestate.co.nz — NZ's second-largest property portal.
Run by the Real Estate Institute of NZ. Quality listings.
Medium scraping difficulty.
"""

class RealEstateCoNZAdapter(NZBaseAdapter):
    slug = "realestate-co-nz"
    base_url = "https://www.realestate.co.nz"

    # Search URL:
    # realestate.co.nz/residential/sale?maxPrice=300000&region=west-coast

    # Strategy:
    # 1. Search by region with price filter
    # 2. Standard pagination
    # 3. Look for __NEXT_DATA__ or JSON API in XHR requests
    # 4. Cards: price, address, beds/baths, photos
    # 5. Detail pages: full description, features, open home times
    # 6. Delay: 3-5 seconds

    REGIONS = [
        "west-coast", "southland", "otago",
        "whanganui", "manawatu", "taranaki",
        "hawkes-bay", "gisborne", "bay-of-plenty",
    ]

    SEARCH_PARAMS = {
        "maxPrice": 300000,
        "propertyType": "residential",
        "saleMethod": "sale",
    }

    REQUEST_DELAY = (3, 5)
```

### 4c. homes.co.nz (Property data + estimates)

```python
# ingestion/adapters/nz/homes_co_nz.py
"""
homes.co.nz — NZ property data platform with valuations.
Unique: provides estimated values, sales history, and suburb stats.
Good for enrichment data even if listings overlap with Trade Me.
"""

class HomesCoNZAdapter(NZBaseAdapter):
    slug = "homes-co-nz"
    base_url = "https://homes.co.nz"

    # This site is valuable for:
    # - Property valuations (estimated current value)
    # - Sales history (recent sales in area)
    # - Suburb profiles (median price, demographics)
    # - School zones

    # Scraping strategy:
    # 1. Use suburb/region pages for bulk discovery
    # 2. Filter by estimated value < NZD 300K
    # 3. Extract: address, estimate, beds/baths, land area, last sold price
    # 4. Delay: 3-5 seconds
    # 5. Some data is behind free login — try unauthenticated first

    REQUEST_DELAY = (3, 5)
```

### 4d. OneRoof.co.nz (NZ Herald)

```python
# ingestion/adapters/nz/one_roof_nz.py
"""
OneRoof.co.nz — NZ Herald's property platform.
Good editorial content + listings. Newer platform.
"""

class OneRoofNZAdapter(NZBaseAdapter):
    slug = "oneroof-nz"
    base_url = "https://www.oneroof.co.nz"

    # Search: oneroof.co.nz/search?price_max=300000&property_type=house

    # Strategy:
    # 1. Search with price filter
    # 2. Standard pagination or infinite scroll (check)
    # 3. Cards: price, address, key features
    # 4. May use React/Next.js — look for JSON data in page source
    # 5. Delay: 3-5 seconds

    REQUEST_DELAY = (3, 5)
```

### 4e. Harcourts NZ (Major agency)

```python
# ingestion/adapters/nz/harcourts_nz.py
"""
Harcourts — NZ's largest real estate agency.
Direct agency listings, sometimes exclusive to Harcourts.
"""

class HarcourtsNZAdapter(NZBaseAdapter):
    slug = "harcourts-nz"
    base_url = "https://harcourts.co.nz"

    # Search: harcourts.co.nz/properties?price_to=300000&property_type=residential

    # Strategy:
    # 1. Browse listings by region
    # 2. Harcourts sites tend to be simpler HTML
    # 3. Extract: price, address, beds/baths, description
    # 4. Delay: 3 seconds
    # 5. Especially good for South Island rural properties

    REQUEST_DELAY = 3
```

---

## 5. NZ Adapter Registry

`ingestion/adapters/nz/__init__.py`:

```python
"""
New Zealand adapter registry.
"""

from ingestion.adapters.nz.trademe_nz import TradeMeNZAdapter
from ingestion.adapters.nz.realestate_co_nz import RealEstateCoNZAdapter
from ingestion.adapters.nz.homes_co_nz import HomesCoNZAdapter
from ingestion.adapters.nz.one_roof_nz import OneRoofNZAdapter
from ingestion.adapters.nz.harcourts_nz import HarcourtsNZAdapter

NZ_ADAPTER_MAP: dict[str, type] = {
    "trademe-nz": TradeMeNZAdapter,              # Easy — HAS OFFICIAL API
    "realestate-co-nz": RealEstateCoNZAdapter,    # Medium — #2 portal
    "homes-co-nz": HomesCoNZAdapter,              # Medium — valuations
    "oneroof-nz": OneRoofNZAdapter,               # Medium — NZ Herald
    "harcourts-nz": HarcourtsNZAdapter,           # Easy — major agency
}
```

---

## 6. Update Main Registry

In `ingestion/adapters/__init__.py`, add:

```python
from ingestion.adapters.nz import NZ_ADAPTER_MAP
ADAPTER_MAP.update(NZ_ADAPTER_MAP)
```

---

## 7. Update auto_pipeline.py

Add to `SCRAPE_SOURCES`:

```python
# ── New Zealand Sources ────────────────────────────────────
{"slug": "trademe-nz", "limit": 300},       # API — best source
{"slug": "realestate-co-nz", "limit": 200}, # Medium
{"slug": "homes-co-nz", "limit": 200},      # Medium — valuations
{"slug": "oneroof-nz", "limit": 150},       # Medium
{"slug": "harcourts-nz", "limit": 150},     # Easy — agency
```

---

## 8. Database Updates

```sql
-- NZ adapters should set country = 'new-zealand'
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'japan';

-- NZ-specific: many listings don't show price (auction/tender)
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS sale_method TEXT;
-- Values: 'asking_price', 'auction', 'tender', 'by_negotiation', 'deadline_sale'
```

---

## 9. LLM Enrichment — NZ Context

Update LLM enrichment prompts for NZ properties:

- **Lifestyle tags**: "coastal lifestyle", "rural farmland", "mountain views", "ski town", "wine region", "fishing village", "DOC land access" (Department of Conservation), "hot springs nearby"
- **What to Know**:
  - Overseas Investment Office (OIO) rules for foreign buyers
  - LIM reports (Land Information Memorandum) — essential
  - Building inspection (weathertight issues common in 90s–00s builds)
  - Earthquake-prone buildings (especially Wellington, Christchurch)
  - Leasehold vs freehold land (important in NZ!)
  - Council rates (property tax equivalent)
  - "Cross lease" vs "fee simple" title types
- **Hazard data**: NZ Earthquake Commission (EQC) zones, tsunami risk (coastal), flood plains (council data)
- **No translation needed**: All English

---

## 10. .env Updates

```bash
# Trade Me API (register at developer.trademe.co.nz)
TRADEME_CONSUMER_KEY=your-key
TRADEME_CONSUMER_SECRET=your-secret
TRADEME_OAUTH_TOKEN=your-token
TRADEME_OAUTH_TOKEN_SECRET=your-token-secret

# NZ config
NZ_SCRAPE_DELAY_SECONDS=3
NZ_PRICE_MAX=300000
```

---

## 11. NZ-Specific Features for Frontend

When we build the multi-country frontend (PROMPT_MULTI_COUNTRY.md), NZ properties should show:

- **Sale method badge**: "Auction", "Tender", "By Negotiation", "Asking Price"
- **Title type**: Freehold / Leasehold / Cross-lease / Unit title
- **Council rates**: Annual $ amount
- **OIO warning**: Flag if property might trigger foreign buyer restrictions
- **EQC zone**: Earthquake risk indicator

---

## Priority Order

1. **Trade Me** — official API, ~80% of NZ listings, structured data
2. **realestate.co.nz** — #2 portal, good rural coverage
3. **Harcourts** — easy, South Island specialist
4. **OneRoof** — NZ Herald platform, growing
5. **homes.co.nz** — valuations + enrichment data

Test each:
```bash
cd /Users/test/Documents/CheapHouse\ Japan
source ingestion/venv/bin/activate
python -m ingestion.adapters.nz.trademe_nz --test
```
