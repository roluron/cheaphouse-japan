# PROMPT: European Scrapers — France, Italy, Portugal, Sweden

> Paste this prompt in Antigravity. It builds adapters for European property sites using the same BaseAdapter pattern as the Japan scrapers. This is for the **multi-country expansion** of CheapHouse.

---

## Context

We already have a working ingestion pipeline for Japan with 10 adapters in `ingestion/adapters/`. Each adapter extends `BaseAdapter` and implements `get_listing_urls()` + `extract_listing(url)`. The pipeline stores results via `storage.save_raw_listings()` into Supabase.

Now we're expanding to **Europe**: France, Italy, Portugal, Sweden. Each country gets its own set of adapters. The goal is the same — find **cheap/affordable houses** for international buyers.

---

## 1. Directory Structure

Create a new directory for European adapters:

```
ingestion/
  adapters/
    europe/
      __init__.py          # European adapter registry
      # France
      green_acres_fr.py
      immobilier_notaires_fr.py
      # Italy
      immobiliare_it.py
      gate_away_com.py
      italian_houses_for_sale.py
      one_euro_houses.py
      # Portugal
      idealista_pt.py
      imovirtual_com.py
      # Sweden
      hemnet_se.py
      blocket_se.py
```

---

## 2. European BaseAdapter Extension

Create `ingestion/adapters/europe/base_europe.py`:

```python
"""
European adapter base class.
Extends BaseAdapter with EUR/SEK price handling and European address parsing.
"""

from ingestion.base_adapter import BaseAdapter

class EuropeBaseAdapter(BaseAdapter):
    """Base for all European adapters."""

    country: str = ""           # "france", "italy", "portugal", "sweden"
    currency: str = "EUR"       # EUR or SEK
    default_language: str = ""  # "fr", "it", "pt", "sv"

    # Price thresholds for "cheap" (in local currency)
    PRICE_THRESHOLDS = {
        "france": 150_000,      # €150K
        "italy": 100_000,       # €100K
        "portugal": 80_000,     # €80K
        "sweden": 1_500_000,    # 1.5M SEK (~€130K)
    }
```

---

## 3. Utility Functions

Create `ingestion/utils_europe.py`:

```python
"""
European price and text utilities.
"""

import re
from typing import Optional

def parse_price_eur(text: str) -> Optional[int]:
    """
    Parse European price formats:
    - "85 000 €" or "85.000 €" (French/Italian)
    - "€85,000" (English portals)
    - "85000" (plain)
    """
    if not text:
        return None
    cleaned = re.sub(r'[^\d]', '', text.strip())
    if not cleaned:
        return None
    price = int(cleaned)
    # Sanity check: if > 100M, probably parsing error
    if price > 100_000_000:
        return None
    return price

def parse_price_sek(text: str) -> Optional[int]:
    """
    Parse Swedish krona prices:
    - "1 250 000 kr"
    - "1,250,000 SEK"
    """
    if not text:
        return None
    cleaned = re.sub(r'[^\d]', '', text.strip())
    if not cleaned:
        return None
    return int(cleaned)

def parse_area_sqm_europe(text: str) -> Optional[float]:
    """
    Parse area: "120 m²", "120 m2", "120 mq" (Italian), "120 kvm" (Swedish).
    """
    if not text:
        return None
    match = re.search(r'(\d+[\.,]?\d*)\s*(?:m²|m2|mq|kvm|sqm)', text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

def extract_region(address: str, country: str) -> Optional[str]:
    """Extract region/department from address string."""
    # Each country has different admin divisions
    # France: département (e.g., "Creuse", "Dordogne")
    # Italy: provincia (e.g., "Toscana", "Calabria")
    # Portugal: distrito (e.g., "Bragança", "Alentejo")
    # Sweden: län (e.g., "Dalarna", "Jämtland")
    # For now, return raw address — LLM enrichment will normalize
    return address

def eur_to_jpy(eur: int) -> int:
    """Rough EUR→JPY for comparison (updated periodically)."""
    return int(eur * 162)  # ~162 JPY/EUR as of 2026

def sek_to_jpy(sek: int) -> int:
    """Rough SEK→JPY for comparison."""
    return int(sek * 14)  # ~14 JPY/SEK as of 2026
```

---

## 4. French Adapters

### 4a. Green-Acres.fr (PRIORITY — easiest to scrape)

```python
# ingestion/adapters/europe/green_acres_fr.py
"""
Green-Acres.fr adapter — international property portal focused on France.
Lower anti-scraping than SeLoger/Leboncoin. English interface available.
Target: houses under €150K in rural France.
"""

class GreenAcresFrAdapter(EuropeBaseAdapter):
    slug = "green-acres-fr"
    country = "france"
    currency = "EUR"
    base_url = "https://www.green-acres.fr"

    # Search URL for cheap houses
    # green-acres.fr/properties/france/house?price_max=150000&sort=date
    SEARCH_URL = "https://www.green-acres.fr/properties/france/house"
    SEARCH_PARAMS = {
        "price_max": 150000,
        "sort": "date",
    }

    # Scraping strategy:
    # 1. Paginate search results (standard ?page=N pagination)
    # 2. Extract listing cards: title, price, location, area, image
    # 3. Follow detail links for full description + photos
    # 4. Delay: 2-3 seconds between requests
    # 5. Use English Accept-Language header

    HEADERS = {
        "Accept-Language": "en-GB,en;q=0.9,fr;q=0.8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
```

### 4b. Immobilier.notaires.fr (Official notary database)

```python
# ingestion/adapters/europe/immobilier_notaires_fr.py
"""
Notaires de France — official notary property database.
Direct-from-seller listings, often cheaper than agency listings.
Moderate anti-scraping. Target: houses under €100K in rural departments.
"""

class NotairesFrAdapter(EuropeBaseAdapter):
    slug = "notaires-fr"
    country = "france"
    currency = "EUR"
    base_url = "https://www.immobilier.notaires.fr"

    # Target cheap departments:
    # Creuse (23), Haute-Vienne (87), Allier (03), Nièvre (58),
    # Indre (36), Cher (18), Cantal (15), Corrèze (19)
    CHEAP_DEPARTMENTS = ["23", "87", "03", "58", "36", "18", "15", "19"]

    # Search URL pattern:
    # /immobilier/vente/maison/{departement}?price_max=100000

    # Scraping strategy:
    # 1. Iterate through CHEAP_DEPARTMENTS
    # 2. Paginate search results within each département
    # 3. Extract: address, price, area, rooms, land area, photos
    # 4. Delay: 3s between requests (government site, be respectful)
    # 5. These are notary sales — often below market price
```

**IMPORTANT**: Do NOT scrape SeLoger or Leboncoin — they have aggressive anti-bot systems and have sued scrapers. Green-Acres and Notaires are safer and have better cheap property coverage.

---

## 5. Italian Adapters

### 5a. Gate-Away.com (English portal for foreigners)

```python
# ingestion/adapters/europe/gate_away_com.py
"""
Gate-Away.com — English portal for buying property in Italy.
Specifically targets international buyers. Easy to scrape.
Target: houses under €100K across Italy.
"""

class GateAwayComAdapter(EuropeBaseAdapter):
    slug = "gate-away-it"
    country = "italy"
    currency = "EUR"
    base_url = "https://www.gate-away.com"

    # Search: gate-away.com/properties-for-sale-in-italy?price_max=100000
    SEARCH_PARAMS = {"price_max": 100000, "type": "house"}

    # Regions with cheapest properties:
    # Calabria, Molise, Basilicata, Abruzzo, Sicily, Sardinia
    TARGET_REGIONS = [
        "calabria", "molise", "basilicata", "abruzzo",
        "sicily", "sardinia", "puglia"
    ]

    # Scraping strategy:
    # 1. Search by region (cleaner results)
    # 2. Paginate with standard ?page=N
    # 3. Cards contain: price, location, area, rooms, thumbnail
    # 4. Detail pages: full description, all photos, agent contact
    # 5. Delay: 2s (easy site, but be polite)
```

### 5b. ItalianHousesForSale.net

```python
# ingestion/adapters/europe/italian_houses_for_sale.py
"""
ItalianHousesForSale.com — curated cheap Italian property listings.
Easy to scrape, English-language, focuses on affordable rural homes.
"""

class ItalianHousesForSaleAdapter(EuropeBaseAdapter):
    slug = "italian-houses"
    country = "italy"
    currency = "EUR"
    base_url = "https://www.italianhousesforsale.com"

    # Scraping strategy:
    # 1. Browse regional listing pages
    # 2. Simple HTML structure, minimal JS
    # 3. Extract: title, price, location, description, photos
    # 4. Delay: 2s between requests
```

### 5c. 1EuroHouses.com

```python
# ingestion/adapters/europe/one_euro_houses.py
"""
1EuroHouses.com — catalog of Italian municipalities offering 1-euro houses.
These are renovation projects with conditions (residency, renovation timeline).
Good for the "adventure buyer" segment.
"""

class OneEuroHousesAdapter(EuropeBaseAdapter):
    slug = "1euro-houses"
    country = "italy"
    currency = "EUR"
    base_url = "https://1eurohouses.com"

    # NOTE: This site lists municipalities, not individual properties.
    # Strategy: scrape municipality pages, extract:
    # - Town name, region, requirements
    # - Application process
    # - Climate/lifestyle info
    # The LLM enrichment will tag these specially as "1 Euro Program"
```

### 5d. Immobiliare.it (Major portal — careful scraping)

```python
# ingestion/adapters/europe/immobiliare_it.py
"""
Immobiliare.it — Italy's largest property portal.
HARD to scrape: moderate anti-bot, rate limiting, dynamic loading.
Use with caution. Target: under €80K in southern regions.
"""

class ImmobiliareItAdapter(EuropeBaseAdapter):
    slug = "immobiliare-it"
    country = "italy"
    currency = "EUR"
    base_url = "https://www.immobiliare.it"

    # Search URL: immobiliare.it/vendita-case/calabria/?prezzoMassimo=80000
    REGIONS_URL_MAP = {
        "calabria": "/vendita-case/calabria/",
        "molise": "/vendita-case/molise/",
        "basilicata": "/vendita-case/basilicata/",
        "abruzzo": "/vendita-case/abruzzo/",
        "sicilia": "/vendita-case/sicilia/",
    }

    # Anti-scraping measures:
    # - Rate limiting (5-10 req/min safe)
    # - Cookie-based sessions
    # - Some pages load via JavaScript

    # Strategy:
    # 1. Use requests-html or cloudscraper for JS-rendered pages
    # 2. Rotate User-Agent strings
    # 3. Delay: 8-12 seconds between requests (SLOW AND SAFE)
    # 4. Limit to 100 listings per run (stay under radar)
    # 5. Extract from search result cards, NOT detail pages

    MAX_LISTINGS_PER_RUN = 100
    REQUEST_DELAY = (8, 12)  # Random delay range in seconds
```

---

## 6. Portuguese Adapters

### 6a. Idealista.pt (Has API!)

```python
# ingestion/adapters/europe/idealista_pt.py
"""
Idealista.pt — Portugal's biggest property portal.
HAS AN OFFICIAL API: https://developers.idealista.com/
Register for free API key → much better than scraping.
Target: houses under €80K in interior Portugal.
"""

class IdealistaPtAdapter(EuropeBaseAdapter):
    slug = "idealista-pt"
    country = "portugal"
    currency = "EUR"
    base_url = "https://api.idealista.com"

    # API APPROACH (preferred over scraping):
    # 1. Register at developers.idealista.com for API key
    # 2. OAuth2 authentication
    # 3. Search endpoint: /3.5/pt/search
    # 4. Parameters: propertyType=homes, maxPrice=80000, country=pt
    # 5. Rate limit: 100 requests/month on free tier
    #    → Use smartly: one request per region per day

    # Target regions (cheapest):
    # Bragança, Guarda, Castelo Branco, Portalegre, Beja
    TARGET_DISTRICTS = [
        "bragança", "guarda", "castelo-branco",
        "portalegre", "beja", "évora"
    ]

    # If API quota exhausted, fall back to scraping:
    # Scraping difficulty: MEDIUM (Cloudflare, but manageable with delays)
    FALLBACK_SCRAPE_DELAY = (5, 10)

    # Add to .env:
    # IDEALISTA_API_KEY=your-key
    # IDEALISTA_API_SECRET=your-secret
```

### 6b. Imovirtual.com

```python
# ingestion/adapters/europe/imovirtual_com.py
"""
Imovirtual.com — second-largest Portuguese property portal.
Good coverage of rural/interior properties.
Medium scraping difficulty.
"""

class ImovirtualComAdapter(EuropeBaseAdapter):
    slug = "imovirtual-pt"
    country = "portugal"
    currency = "EUR"
    base_url = "https://www.imovirtual.com"

    # Search: /comprar/moradia/?search%5Bfilter_float_price%3Ato%5D=80000
    SEARCH_PARAMS = {
        "search[filter_float_price:to]": 80000,
        "search[filter_enum_market]": "secondary",  # Resale only
    }

    # Scraping strategy:
    # 1. Standard pagination (?page=N)
    # 2. Cards: price, location, area, rooms, thumbnail
    # 3. Detail pages: full description, photos, features
    # 4. Delay: 3-5 seconds
    # 5. Use Portuguese Accept-Language header

    HEADERS = {
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    }
```

---

## 7. Swedish Adapters

### 7a. Hemnet.se (Sweden's main portal)

```python
# ingestion/adapters/europe/hemnet_se.py
"""
Hemnet.se — Sweden's dominant property portal (90%+ market share).
Medium-hard scraping. Target: houses under 1.5M SEK in rural areas.
"""

class HemnetSeAdapter(EuropeBaseAdapter):
    slug = "hemnet-se"
    country = "sweden"
    currency = "SEK"
    base_url = "https://www.hemnet.se"

    # Search: /bostader?price_max=1500000&item_types[]=villa
    SEARCH_PARAMS = {
        "price_max": 1500000,
        "item_types[]": "villa",
    }

    # Cheapest regions (län):
    # Dalarna, Gävleborg, Västernorrland, Jämtland, Norrbotten
    TARGET_REGIONS = [
        "dalarna", "gavleborg", "vasternorrland",
        "jamtland", "norrbotten", "varmland"
    ]

    # Anti-scraping measures:
    # - Rate limiting
    # - Session cookies required
    # - Some content loaded via JS (GraphQL API)

    # Strategy:
    # 1. Use GraphQL internal API if discoverable (check Network tab)
    # 2. Otherwise scrape search result pages
    # 3. Delay: 5-8 seconds
    # 4. Limit: 150 per run
    # 5. Swedish Accept-Language header

    MAX_LISTINGS_PER_RUN = 150
    REQUEST_DELAY = (5, 8)
    HEADERS = {
        "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
    }
```

### 7b. Blocket.se (General marketplace)

```python
# ingestion/adapters/europe/blocket_se.py
"""
Blocket.se — Sweden's largest marketplace (like Leboncoin).
Has an unofficial REST API. Easier than Hemnet.
Target: houses under 1M SEK (bargains from private sellers).
"""

class BlocketSeAdapter(EuropeBaseAdapter):
    slug = "blocket-se"
    country = "sweden"
    currency = "SEK"
    base_url = "https://www.blocket.se"

    # Blocket has a semi-public API:
    # pip install blocket-api  (unofficial wrapper)
    # OR scrape: /annonser/hela_sverige/bostad/villor?price_to=1000000

    # Strategy:
    # 1. Try unofficial API first (easier, structured JSON)
    # 2. Fall back to scraping if API broken
    # 3. Private seller listings = often cheaper
    # 4. Delay: 3-5 seconds
    # 5. Filter: bostad (housing) → villor (houses)

    USE_UNOFFICIAL_API = True  # Try blocket-api PyPI package first
```

---

## 8. European Adapter Registry

Update `ingestion/adapters/europe/__init__.py`:

```python
"""
European adapter registry.
"""

from ingestion.adapters.europe.green_acres_fr import GreenAcresFrAdapter
from ingestion.adapters.europe.immobilier_notaires_fr import NotairesFrAdapter
from ingestion.adapters.europe.immobiliare_it import ImmobiliareItAdapter
from ingestion.adapters.europe.gate_away_com import GateAwayComAdapter
from ingestion.adapters.europe.italian_houses_for_sale import ItalianHousesForSaleAdapter
from ingestion.adapters.europe.one_euro_houses import OneEuroHousesAdapter
from ingestion.adapters.europe.idealista_pt import IdealistaPtAdapter
from ingestion.adapters.europe.imovirtual_com import ImovirtualComAdapter
from ingestion.adapters.europe.hemnet_se import HemnetSeAdapter
from ingestion.adapters.europe.blocket_se import BlocketSeAdapter

EUROPE_ADAPTER_MAP: dict[str, type] = {
    # France
    "green-acres-fr": GreenAcresFrAdapter,       # Easy — international portal
    "notaires-fr": NotairesFrAdapter,             # Medium — official notary DB
    # Italy
    "gate-away-it": GateAwayComAdapter,           # Easy — English portal for foreigners
    "italian-houses": ItalianHousesForSaleAdapter, # Easy — curated cheap houses
    "1euro-houses": OneEuroHousesAdapter,          # Easy — 1€ house program catalog
    "immobiliare-it": ImmobiliareItAdapter,       # Hard — Italy's #1 portal
    # Portugal
    "idealista-pt": IdealistaPtAdapter,            # Medium — HAS OFFICIAL API
    "imovirtual-pt": ImovirtualComAdapter,         # Medium — 2nd largest
    # Sweden
    "hemnet-se": HemnetSeAdapter,                  # Hard — 90% market share
    "blocket-se": BlocketSeAdapter,                # Medium — marketplace + unofficial API
}
```

---

## 9. Update Main Registry

In `ingestion/adapters/__init__.py`, add at the bottom:

```python
# Import European adapters
from ingestion.adapters.europe import EUROPE_ADAPTER_MAP

# Merge into main registry
ADAPTER_MAP.update(EUROPE_ADAPTER_MAP)
```

---

## 10. Update auto_pipeline.py

Add European sources to the `SCRAPE_SOURCES` list in `auto_pipeline.py`:

```python
# ── European Sources ──────────────────────────────────────
# Easy sources first, hard sources last
{"slug": "green-acres-fr", "limit": 300},     # France — easy
{"slug": "notaires-fr", "limit": 200},        # France — medium
{"slug": "gate-away-it", "limit": 300},       # Italy — easy
{"slug": "italian-houses", "limit": 200},     # Italy — easy
{"slug": "1euro-houses", "limit": 50},        # Italy — 1€ program
{"slug": "idealista-pt", "limit": 200},       # Portugal — API
{"slug": "imovirtual-pt", "limit": 200},      # Portugal — medium
{"slug": "blocket-se", "limit": 200},         # Sweden — medium
{"slug": "hemnet-se", "limit": 150},          # Sweden — hard (last)
{"slug": "immobiliare-it", "limit": 100},     # Italy — hard (very last)
```

---

## 11. Database: Add country Column

Add a `country` column to the `raw_listings` table if not already present:

```sql
ALTER TABLE raw_listings ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'japan';
CREATE INDEX IF NOT EXISTS idx_raw_listings_country ON raw_listings(country);
```

Each European adapter should set `country` in the RawListing it returns.

---

## 12. LLM Enrichment for European Properties

Update the LLM prompts in the enrichment pipeline to handle European properties:

- **Translation**: French/Italian/Portuguese/Swedish → English (same pattern as Japanese)
- **Lifestyle tags**: Adapt for European contexts (e.g., "wine country", "medieval village", "coastal", "ski access", "renovation project")
- **What to Know**: European-specific concerns (renovation permits, residency requirements for 1€ houses, notary fees, local taxes, community obligations)
- **Hazard data**: European flood/earthquake maps (EU Copernicus data for floods, EFEHR for seismic)

---

## 13. .env Updates

Add these to `ingestion/.env`:

```bash
# Idealista API (register at developers.idealista.com)
IDEALISTA_API_KEY=your-key-here
IDEALISTA_API_SECRET=your-secret-here

# European scraping config
EUROPE_SCRAPE_DELAY_SECONDS=3
EUROPE_LLM_BATCH_SIZE=10
```

---

## Priority Order for Implementation

1. **gate-away.com** + **italianhousesforsale.com** — easiest, English, great content
2. **green-acres.fr** — easy, international, good cheap French houses
3. **idealista.pt** — has official API, best approach
4. **imovirtual.com** — standard scraping
5. **notaires.fr** — medium difficulty, unique source
6. **blocket.se** — unofficial API available
7. **1eurohouses.com** — small niche site
8. **hemnet.se** — harder, but essential for Sweden
9. **immobiliare.it** — hardest, save for last

Test each adapter individually before adding to auto_pipeline:
```bash
cd /Users/test/Documents/CheapHouse\ Japan
source ingestion/venv/bin/activate
python -m ingestion.adapters.europe.gate_away_com --test
```
