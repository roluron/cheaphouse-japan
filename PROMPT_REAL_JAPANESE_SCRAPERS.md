# PROMPT À COLLER DANS ANTIGRAVITY — Vrais scrapers vers les sites immobiliers japonais

```
Auto-approve all changes and commands. Don't ask for permission.

## Context

Our current scrapers (OldHousesJapan, AllAkiyas) are middlemen — they link to THEIR pages, not to the original Japanese real estate listings. This is a problem:
1. Users click a listing and land on some random aggregator, not the actual source
2. Our freshness checker can't verify if the REAL listing is still live
3. We have no original data — just recycled content from other aggregators
4. It looks unprofessional and we lose credibility

We need to scrap these adapters and build NEW ones that go directly to the real Japanese property sites. Each listing's `source_url` must point to the ORIGINAL detail page on the Japanese site.

## Target sites — in priority order

### 1. LIFULL HOME'S (homes.co.jp) — TOP PRIORITY
- URL: https://www.homes.co.jp/kodate/b-1030010/
- One of Japan's biggest real estate portals
- Direct akiya/cheap house section: search for 空き家 (akiya) or filter by very low price
- Listings under ¥5,000,000 is our sweet spot
- Listing detail pages: `https://www.homes.co.jp/kodate/b-{id}/`
- Data available: price, layout (間取り), building area, land area, year built, address, station access, images, condition notes
- Language: Japanese (we translate via our pipeline)

### 2. at home (athome.co.jp)
- URL: https://www.athome.co.jp/kodate/
- Another major portal, strong rural coverage
- Can filter by price range (e.g., under 500万円)
- Listing pages: `https://www.athome.co.jp/kodate/{id}/`
- Good structured data in consistent HTML format

### 3. Suumo (suumo.jp)
- URL: https://suumo.jp/jj/bukken/ichiran/JJ010FJ001/
- Largest real estate portal in Japan (Recruit Holdings)
- Very structured data, good coverage nationwide
- WARNING: Suumo has aggressive anti-scraping. Use respectful delays (3-5s between requests), proper User-Agent, and respect robots.txt
- If scraping is blocked, skip Suumo for now and focus on the other two

### 4. Real Estate Japan (realestate.co.jp)
- URL: https://realestate.co.jp/en/forsale/listing/
- Already in English — less translation needed
- Targets international buyers (our exact audience)
- Listings have direct links and good structured data
- Smaller inventory but high quality for our use case

## Adapter architecture

Follow the existing BaseAdapter pattern. Each adapter must:

1. Implement `get_listing_urls()` — return a list of individual property detail page URLs
2. Implement `extract_listing(url)` — parse one detail page into a RawListing
3. Set `source_url` to the ACTUAL detail page URL on the Japanese site — this is CRITICAL

### Scraping strategy for Japanese sites

These sites are in Japanese. Here's how to handle it:

```python
# Common patterns for Japanese real estate sites
# Price: usually in format "980万円" (= ¥9,800,000) or "980 万円"
# Area: "80.5㎡" or "80.5m²"
# Rooms: "3LDK", "4DK", "6SDK" (Japanese layout notation)
# Year built: "昭和55年" (= 1980), "平成10年" (= 1998), "令和3年" (= 2021)
# Station: "○○駅 徒歩10分" (= 10 min walk from XX station)

import re

def parse_japanese_price(text):
    """Parse Japanese price format to JPY integer."""
    text = text.replace(',', '').replace(' ', '')
    # Match "980万円" or "9800万" or "1億2000万円"
    oku_match = re.search(r'(\d+)億', text)
    man_match = re.search(r'(\d+)万', text)

    total = 0
    if oku_match:
        total += int(oku_match.group(1)) * 100_000_000
    if man_match:
        total += int(man_match.group(1)) * 10_000
    return total if total > 0 else None

def parse_japanese_year(text):
    """Convert Japanese era year to Western year."""
    era_map = {
        '令和': 2018,  # Reiwa: 2019 = 令和1年
        '平成': 1988,  # Heisei: 1989 = 平成1年
        '昭和': 1925,  # Showa: 1926 = 昭和1年
        '大正': 1911,  # Taisho: 1912 = 大正1年
    }
    for era, offset in era_map.items():
        match = re.search(rf'{era}(\d+)年', text)
        if match:
            return offset + int(match.group(1))
    # Try direct Western year
    match = re.search(r'(19|20)\d{2}', text)
    if match:
        return int(match.group(0))
    return None

def parse_area_sqm(text):
    """Parse area in m² from Japanese format."""
    match = re.search(r'([\d,.]+)\s*(?:㎡|m²|m2|sqm)', text)
    if match:
        return float(match.group(1).replace(',', ''))
    # Tsubo conversion (1 tsubo = 3.306 m²)
    match = re.search(r'([\d,.]+)\s*坪', text)
    if match:
        return round(float(match.group(1).replace(',', '')) * 3.306, 1)
    return None
```

### LIFULL HOME'S Adapter (`adapters/homes_co_jp.py`)

```python
"""
LIFULL HOME'S (homes.co.jp) adapter
Scrapes cheap detached houses directly from Japan's major real estate portal.
"""

class HomesCoJpAdapter(BaseAdapter):
    slug = "homes-co-jp"
    base_url = "https://www.homes.co.jp"

    # Target: detached houses (kodate) under ¥10M across all prefectures
    # The search URL filters for cheap properties
    SEARCH_URLS = [
        # Price range 1: Under ¥3M (super cheap akiya territory)
        "https://www.homes.co.jp/kodate/chuko/price-01/",
        # Price range 2: ¥3M-¥5M
        "https://www.homes.co.jp/kodate/chuko/price-02/",
        # Price range 3: ¥5M-¥10M
        "https://www.homes.co.jp/kodate/chuko/price-03/",
    ]
    # NOTE: These URLs are examples. Inspect the actual site to find the correct
    # search result URL structure with pagination. homes.co.jp uses query params
    # like ?page=2 or has numbered page links.

    def get_listing_urls(self):
        """Crawl search result pages to collect individual listing URLs."""
        urls = []
        for search_url in self.SEARCH_URLS:
            page = 1
            while True:
                resp = self.get(f"{search_url}?page={page}")
                if not resp:
                    break
                # Find all listing detail links
                # Pattern: <a href="/kodate/b-XXXXXXX/"> or similar
                links = resp.select('a[href*="/kodate/b-"]')
                if not links:
                    break
                for link in links:
                    href = link.get('href', '')
                    full_url = f"https://www.homes.co.jp{href}" if href.startswith('/') else href
                    if full_url not in urls:
                        urls.append(full_url)
                page += 1
                # Safety limit
                if page > 50:
                    break
        return urls

    def extract_listing(self, url):
        """Extract property details from a single listing page."""
        soup = self.get(url)
        if not soup:
            return None

        # Extract from the property detail table (物件概要)
        # homes.co.jp uses <table> or <dl> for property specs
        # Look for: 価格 (price), 間取り (layout), 建物面積 (building area),
        # 土地面積 (land area), 築年月 (year built), 所在地 (address),
        # 最寄駅 (nearest station)

        return RawListing(
            source_slug=self.slug,
            source_url=url,  # THIS IS THE REAL SOURCE URL
            title=self._extract_title(soup),
            description=self._extract_description(soup),
            price_jpy=self._extract_price(soup),
            prefecture=self._extract_prefecture(soup),
            city=self._extract_city(soup),
            address_raw=self._extract_address(soup),
            building_sqm=self._extract_building_area(soup),
            land_sqm=self._extract_land_area(soup),
            year_built=self._extract_year(soup),
            rooms=self._extract_layout(soup),
            nearest_station=self._extract_station(soup),
            station_distance=self._extract_station_distance(soup),
            image_urls=self._extract_images(soup),
            building_type="detached",
        )

    # Implement each _extract method based on the actual HTML structure
    # of homes.co.jp detail pages. Inspect the page to find the right
    # CSS selectors. Common patterns:
    # - Property table: table.bukkenSpec or dl.bukkenDetail
    # - Price: .bukkenPrice or th containing "価格"
    # - Images: .bukkenGallery img or .bukkenSlider img
```

### at home Adapter (`adapters/athome_co_jp.py`)

Same pattern as homes.co.jp. Key differences:
- Search URL structure: `https://www.athome.co.jp/kodate/chuko/?price_to=1000` (price in 万円)
- Listing URLs: `https://www.athome.co.jp/kodate/{property_id}/`
- athome uses more consistent HTML structure — look for `<table class="data">` patterns

### Real Estate Japan Adapter (`adapters/realestate_co_jp.py`)

Easier because it's already in English:
- Search: `https://realestate.co.jp/en/forsale/listing/?price_max=10000000&property_type=house`
- Already uses English labels (Price, Size, Year Built, etc.)
- Less parsing needed, still output `source_url` pointing to their detail page

## Update the adapter registry

In `adapters/__init__.py`, replace the old adapters:

```python
from .homes_co_jp import HomesCoJpAdapter
from .athome_co_jp import AthomeCoJpAdapter
from .realestate_co_jp import RealEstateCoJpAdapter
from .all_akiyas import AllAkiyasAdapter  # Keep as fallback for now

ADAPTER_MAP = {
    "homes-co-jp": HomesCoJpAdapter,
    "athome-co-jp": AthomeCoJpAdapter,
    "realestate-co-jp": RealEstateCoJpAdapter,
    "all-akiyas": AllAkiyasAdapter,  # Keep but deprioritize
    # REMOVED: "old-houses-japan" — middleman, not original source
    # REMOVED: "cheap-houses-japan" — newsletter stub, never worked
}
```

## Update `seed_sources.sql`

```sql
-- New direct sources
INSERT INTO sources (name, slug, base_url, scrape_interval_hours, is_active, notes)
VALUES
    ('LIFULL HOMES', 'homes-co-jp', 'https://www.homes.co.jp', 24, true,
     'Major Japanese portal. Direct listings. Japanese language.'),
    ('at home', 'athome-co-jp', 'https://www.athome.co.jp', 24, true,
     'Major Japanese portal. Good rural coverage. Japanese language.'),
    ('Real Estate Japan', 'realestate-co-jp', 'https://realestate.co.jp', 24, true,
     'English-language portal targeting international buyers.'),
    ('Akiya Mart', 'akiya-mart', 'https://akiya-mart.com', 24, false,
     'Future: requires login. Placeholder.')
ON CONFLICT (slug) DO UPDATE SET
    is_active = EXCLUDED.is_active,
    notes = EXCLUDED.notes;

-- Deactivate old middleman sources
UPDATE sources SET is_active = false, notes = 'Deprecated: middleman site, not original source'
WHERE slug IN ('old-houses-japan', 'cheap-houses-japan');
```

## Add Japanese text utilities to `utils.py`

Add the helper functions from above (parse_japanese_price, parse_japanese_year, parse_area_sqm) to `ingestion/utils.py` so all adapters can share them.

## Important scraping rules

1. **Rate limiting**: 3 second delay between requests to Japanese sites. They are polite about robots.txt but will block aggressive scrapers.

2. **User-Agent**: Use a realistic browser User-Agent, not python-requests default.

3. **Respect robots.txt**: Check each site's robots.txt before scraping. If they disallow certain paths, skip those.

4. **Start small**: For each new adapter, test with `python run.py test-adapter homes-co-jp --limit 5` first. Get 5 listings working perfectly before running full scrape.

5. **The adapter doesn't need to be perfect on first try**: The HTML structure of Japanese sites requires actual inspection. Build the skeleton, test it, then refine the CSS selectors based on what you find. Use `--dry-run` to check URL collection before full extraction.

6. **source_url MUST be the original Japanese site URL** — this is the whole point of this rewrite. Never set source_url to our own domain or an aggregator.

7. **Images**: Japanese sites often use lazy-loading or JavaScript galleries. Try to extract `data-src` or `data-original` attributes, not just `src`. Some images may be behind a viewer — get the highest resolution thumbnail available.

8. **Encoding**: Japanese sites use UTF-8 or Shift_JIS. Always specify `encoding='utf-8'` or detect it. BeautifulSoup handles this well.

## Test plan

After building each adapter:

1. `python run.py test-adapter homes-co-jp --limit 3` — verify 3 listings parse correctly
2. Check that `source_url` points to the actual homes.co.jp detail page
3. Check that price_jpy is a valid integer (not None, not 0)
4. Check that prefecture/city are extracted
5. `python run.py scrape --source homes-co-jp --limit 50` — small batch to DB
6. Run the pipeline: `python run.py pipeline --limit 50` to see the full flow

Do homes-co-jp FIRST. Get it working end-to-end. Then athome, then realestate.co.jp.

## RULES

- EVERY listing must have source_url pointing to the REAL Japanese site detail page
- Remove old-houses-japan adapter entirely (delete the file)
- Remove cheap-houses-japan adapter entirely (delete the file)
- Keep all-akiyas as fallback but mark as low priority
- Japanese text parsing helpers go in shared utils.py
- Test each adapter with --limit 5 before running full scrape
- Respect rate limits — 3s delay minimum between requests
- Build must pass, push to GitHub
```
