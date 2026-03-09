# PROMPT À COLLER DANS ANTIGRAVITY — Scrapers athome.co.jp + suumo.jp

```
Auto-approve all changes and commands. Don't ask for permission.

## Context

We already have adapters for homes.co.jp and realestate.co.jp that scrape directly from Japanese real estate portals. Now we need TWO MORE adapters for the remaining major sites: athome.co.jp and suumo.jp.

The existing adapters follow the BaseAdapter pattern in `ingestion/base_adapter.py`. The Japanese text parsing helpers (parse_japanese_price, parse_japanese_year, parse_area_sqm) are already in `ingestion/utils.py` — reuse them.

CRITICAL RULE: `source_url` on every listing MUST point to the original detail page on athome.co.jp or suumo.jp. Never to our own site or any aggregator.

---

## ADAPTER 1: at home (athome.co.jp)

### Site overview
- One of Japan's top 3 real estate portals
- Excellent rural/countryside coverage (perfect for akiya hunting)
- Clean, consistent HTML structure
- Less aggressive anti-scraping than Suumo
- URL structure is predictable

### Create `ingestion/adapters/athome_co_jp.py`

```python
"""
at home (athome.co.jp) adapter
Scrapes cheap detached houses from Japan's major real estate portal.
Strong rural coverage — ideal for akiya and countryside properties.
"""

from base_adapter import BaseAdapter
from models import RawListing
from utils import parse_japanese_price, parse_japanese_year, parse_area_sqm
import re


class AthomeCoJpAdapter(BaseAdapter):
    slug = "athome-co-jp"
    base_url = "https://www.athome.co.jp"
    rate_limit_seconds = 3  # Be respectful

    # Search for cheap detached houses (中古一戸建て = used detached house)
    # Price filter: price_to in 万円 (10,000 JPY units)
    # 500 = under ¥5,000,000 | 1000 = under ¥10,000,000
    #
    # athome search works by area. We target all of Japan's regions:
    # Hokkaido/Tohoku, Kanto, Chubu, Kinki, Chugoku, Shikoku, Kyushu
    #
    # IMPORTANT: Inspect the actual athome search page to confirm URL patterns.
    # The structure below is the typical pattern but may need adjustment.

    REGION_SEARCH_URLS = [
        # Format: base search URL for used detached houses, filtered cheap
        # athome typically uses paths like:
        # /kodate/chuko/hokkaido/price-range/
        # or query params like ?price_to=1000
        #
        # Navigate to https://www.athome.co.jp/kodate/chuko/ and inspect
        # the search form to find the exact URL structure.
        # Filter for properties under ¥10M (1000万円)

        # Hokkaido & Tohoku
        "https://www.athome.co.jp/kodate/chuko/hokkaido/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/aomori/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/akita/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/iwate/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/yamagata/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/miyagi/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/fukushima/list/?price_to=1000",

        # Kanto (less cheap, but some gems)
        "https://www.athome.co.jp/kodate/chuko/ibaraki/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/tochigi/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/gunma/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/chiba/list/?price_to=500",

        # Chubu
        "https://www.athome.co.jp/kodate/chuko/niigata/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/nagano/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/toyama/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/ishikawa/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/fukui/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/yamanashi/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/gifu/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/shizuoka/list/?price_to=1000",

        # Kinki
        "https://www.athome.co.jp/kodate/chuko/shiga/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kyoto/list/?price_to=500",
        "https://www.athome.co.jp/kodate/chuko/nara/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/wakayama/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/hyogo/list/?price_to=500",
        "https://www.athome.co.jp/kodate/chuko/mie/list/?price_to=1000",

        # Chugoku
        "https://www.athome.co.jp/kodate/chuko/tottori/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/shimane/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/okayama/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/hiroshima/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/yamaguchi/list/?price_to=1000",

        # Shikoku
        "https://www.athome.co.jp/kodate/chuko/tokushima/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kagawa/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/ehime/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kochi/list/?price_to=1000",

        # Kyushu & Okinawa
        "https://www.athome.co.jp/kodate/chuko/fukuoka/list/?price_to=500",
        "https://www.athome.co.jp/kodate/chuko/saga/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/nagasaki/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kumamoto/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/oita/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/miyazaki/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kagoshima/list/?price_to=1000",
    ]

    # NOTE: The above URLs are best-guess based on athome's typical structure.
    # You MUST inspect the actual site to confirm:
    # 1. Go to https://www.athome.co.jp/kodate/chuko/
    # 2. Select a prefecture
    # 3. Set price filter to under 1000万円
    # 4. Look at the resulting URL structure
    # 5. Adjust REGION_SEARCH_URLS accordingly

    def get_listing_urls(self):
        """Crawl search result pages across all prefectures."""
        urls = []
        for search_url in self.REGION_SEARCH_URLS:
            page = 1
            while True:
                # athome pagination is typically ?page=N or &page=N
                separator = '&' if '?' in search_url else '?'
                paginated_url = f"{search_url}{separator}page={page}" if page > 1 else search_url

                soup = self.get(paginated_url)
                if not soup:
                    break

                # Find listing detail links
                # athome detail pages typically match: /kodate/{numeric_id}/
                # or /kodate/chuko/{numeric_id}/
                # Inspect the actual HTML to find the right selector
                links = soup.select('a[href*="/kodate/"]')

                new_urls = []
                for link in links:
                    href = link.get('href', '')
                    # Filter for actual detail pages (numeric ID pattern)
                    if re.search(r'/kodate/\d+/?', href) or re.search(r'/kodate/chuko/\d+/?', href):
                        full_url = href if href.startswith('http') else f"https://www.athome.co.jp{href}"
                        if full_url not in urls and full_url not in new_urls:
                            new_urls.append(full_url)

                if not new_urls:
                    break

                urls.extend(new_urls)
                page += 1
                if page > 30:  # Safety limit per prefecture
                    break

            print(f"  {search_url.split('/')[-3]}: found {len(urls)} listings so far")

        print(f"Total athome listings found: {len(urls)}")
        return urls

    def extract_listing(self, url):
        """Extract property details from an athome detail page."""
        soup = self.get(url)
        if not soup:
            return None

        # athome detail pages typically have:
        # - A property spec table (物件概要) with <th>/<td> pairs
        # - A photo gallery
        # - Location/map section
        #
        # Common table headers to look for:
        # 価格 = price
        # 間取り = layout/rooms (e.g., "3LDK")
        # 建物面積 = building area
        # 土地面積 = land area
        # 築年月 = year built
        # 所在地 = address
        # 交通 = transport/station access
        # 構造 = building structure (木造 = wood, 鉄骨 = steel, etc.)
        # 階建 = number of floors

        # Extract the spec table into a dict
        specs = {}
        for row in soup.select('table th, table dt'):
            key = row.get_text(strip=True)
            # Get the sibling td or dd
            value_el = row.find_next_sibling('td') or row.find_next_sibling('dd')
            if value_el:
                specs[key] = value_el.get_text(strip=True)

        # Parse address to extract prefecture and city
        address = specs.get('所在地', '') or specs.get('住所', '')
        prefecture, city = self._parse_address(address)

        # Parse station access: "○○線 ○○駅 徒歩10分"
        transport = specs.get('交通', '') or specs.get('最寄り駅', '')
        station, distance = self._parse_transport(transport)

        # Images: look for gallery/slider images
        images = []
        for img in soup.select('.gallery img, .photo img, [class*="slide"] img, [class*="photo"] img'):
            src = img.get('data-src') or img.get('data-original') or img.get('src', '')
            if src and not src.endswith(('.gif', '.svg')) and 'icon' not in src and 'logo' not in src:
                if src.startswith('//'):
                    src = f"https:{src}"
                elif src.startswith('/'):
                    src = f"https://www.athome.co.jp{src}"
                images.append(src)

        return RawListing(
            source_slug=self.slug,
            source_url=url,  # REAL athome URL
            title=self._extract_title(soup),
            description=self._extract_description(soup),
            price_jpy=parse_japanese_price(specs.get('価格', '') or specs.get('販売価格', '')),
            prefecture=prefecture,
            city=city,
            address_raw=address,
            building_sqm=parse_area_sqm(specs.get('建物面積', '')),
            land_sqm=parse_area_sqm(specs.get('土地面積', '') or specs.get('敷地面積', '')),
            year_built=parse_japanese_year(specs.get('築年月', '') or specs.get('築年', '')),
            rooms=specs.get('間取り', ''),
            nearest_station=station,
            station_distance=distance,
            image_urls=images[:20],  # Cap at 20 images
            building_type="detached",
        )

    def _extract_title(self, soup):
        """Get the property title from page."""
        # Try og:title, h1, or page title
        og = soup.find('meta', property='og:title')
        if og and og.get('content'):
            return og['content'].strip()
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        return soup.title.string.strip() if soup.title else ''

    def _extract_description(self, soup):
        """Get property description text."""
        # Look for description/comment sections
        for selector in ['.description', '.comment', '.bukkenComment', '[class*="desc"]', '[class*="comment"]']:
            el = soup.select_one(selector)
            if el:
                return el.get_text(strip=True)[:2000]
        # Fallback: og:description
        og = soup.find('meta', property='og:description')
        if og and og.get('content'):
            return og['content'].strip()
        return ''

    def _parse_address(self, address_text):
        """Extract prefecture and city from Japanese address string."""
        from config import PREFECTURE_MAP  # kanji → romanized mapping
        prefecture = ''
        city = ''
        for kanji, romaji in PREFECTURE_MAP.items():
            if kanji in address_text:
                prefecture = romaji
                # City is usually right after prefecture name
                after_pref = address_text.split(kanji)[-1]
                # City ends with 市, 町, 村, 区, 郡
                city_match = re.match(r'(.+?[市町村区郡])', after_pref)
                if city_match:
                    city = city_match.group(1)
                break
        return prefecture, city

    def _parse_transport(self, transport_text):
        """Parse station name and walking distance from transport text."""
        station = ''
        distance = None
        # Pattern: "○○駅" = station name
        st_match = re.search(r'([^\s]+駅)', transport_text)
        if st_match:
            station = st_match.group(1)
        # Pattern: "徒歩N分" = N minutes walk
        dist_match = re.search(r'徒歩(\d+)分', transport_text)
        if dist_match:
            distance = f"{dist_match.group(1)} min walk"
        return station, distance
```

---

## ADAPTER 2: Suumo (suumo.jp)

### Site overview
- THE biggest real estate portal in Japan (owned by Recruit Holdings)
- Massive inventory, best data quality
- WARNING: Suumo has aggressive bot detection:
  - Rate limiting
  - JavaScript rendering for some content
  - CAPTCHA on excessive requests
  - May block cloud server IPs
- We scrape from a Mac Mini (residential IP) which is MUCH better than cloud

### Anti-scraping strategy

Since we run on a Mac Mini with a residential IP, we have an advantage. But we still need to be careful:

1. **Long delays**: 5 seconds between requests minimum (not 3 like other sites)
2. **Randomized delays**: Add random 1-3 seconds on top of the base delay
3. **Session cookies**: Accept and send cookies like a real browser
4. **Realistic headers**: Full browser header set including Accept-Language, Referer, etc.
5. **Batch limits**: Max 200 listings per scrape run. Spread over multiple days for full coverage.
6. **Retry with backoff**: If we get a 403 or CAPTCHA, stop immediately and wait 30 minutes

### Create `ingestion/adapters/suumo_jp.py`

```python
"""
Suumo (suumo.jp) adapter
Scrapes cheap detached houses from Japan's largest real estate portal.

WARNING: Suumo has aggressive anti-scraping measures.
This adapter uses extra-cautious rate limiting and browser-like behavior.
Run from residential IP only (Mac Mini, not cloud).
"""

import random
import time
from base_adapter import BaseAdapter
from models import RawListing
from utils import parse_japanese_price, parse_japanese_year, parse_area_sqm
import re
import requests


class SuumoJpAdapter(BaseAdapter):
    slug = "suumo-jp"
    base_url = "https://suumo.jp"
    rate_limit_seconds = 5  # Minimum delay, we add random on top

    def __init__(self):
        super().__init__()
        # Use a persistent session with browser-like headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0',
        })
        self._request_count = 0

    def _polite_get(self, url):
        """GET with extra politeness for Suumo."""
        # Randomized delay: 5-8 seconds
        delay = self.rate_limit_seconds + random.uniform(1, 3)
        time.sleep(delay)

        # Set referer to look like natural browsing
        self.session.headers['Referer'] = 'https://suumo.jp/jj/bukken/ichiran/'

        try:
            resp = self.session.get(url, timeout=30)

            self._request_count += 1

            # Detect anti-scraping blocks
            if resp.status_code == 403:
                print(f"  BLOCKED by Suumo (403). Stopping. Made {self._request_count} requests.")
                return None
            if resp.status_code == 429:
                print(f"  Rate limited by Suumo (429). Waiting 60s...")
                time.sleep(60)
                return None
            if 'captcha' in resp.text.lower() or 'recaptcha' in resp.text.lower():
                print(f"  CAPTCHA detected. Stopping. Made {self._request_count} requests.")
                return None

            resp.raise_for_status()

            from bs4 import BeautifulSoup
            return BeautifulSoup(resp.text, 'html.parser')

        except requests.RequestException as e:
            print(f"  Request error: {e}")
            return None

    # Suumo search URL structure for cheap detached houses:
    # https://suumo.jp/jj/bukken/ichiran/JJ012FC001/?ar=010&bs=021&ta=01&kb=1&kt=1000&ekTjCd=&ekTjNm=&tj=0&pc=30
    #
    # Key params:
    # ar = area code (010=Hokkaido, 020=Tohoku, 030=Kanto, etc.)
    # bs = property type (021 = 中古一戸建て = used detached house)
    # kb = price from (1 = lowest)
    # kt = price to (in 万円, so 1000 = under ¥10M)
    # pc = results per page (30 or 50)
    # pn = page number
    #
    # IMPORTANT: You MUST inspect suumo.jp to find the exact current URL structure.
    # Go to https://suumo.jp/ → 中古一戸建て (used houses) → set price filter → check URL

    AREA_CODES = {
        '010': 'Hokkaido',
        '020': 'Tohoku',     # Aomori, Iwate, Miyagi, Akita, Yamagata, Fukushima
        '030': 'Kanto',      # Ibaraki, Tochigi, Gunma, Chiba, Saitama (skip Tokyo)
        '040': 'Chubu',      # Niigata, Toyama, Ishikawa, Fukui, Yamanashi, Nagano, Gifu, Shizuoka
        '060': 'Kinki',      # Shiga, Kyoto, Nara, Wakayama, Hyogo, Mie
        '070': 'Chugoku',    # Tottori, Shimane, Okayama, Hiroshima, Yamaguchi
        '080': 'Shikoku',    # Tokushima, Kagawa, Ehime, Kochi
        '090': 'Kyushu',     # Fukuoka, Saga, Nagasaki, Kumamoto, Oita, Miyazaki, Kagoshima
    }

    def get_listing_urls(self):
        """Crawl Suumo search results to collect listing URLs."""
        urls = []

        for area_code, area_name in self.AREA_CODES.items():
            print(f"  Scanning {area_name}...")
            page = 1

            while True:
                # Build search URL — adjust based on actual Suumo URL structure
                search_url = (
                    f"https://suumo.jp/jj/bukken/ichiran/JJ012FC001/"
                    f"?ar={area_code}&bs=021&kb=1&kt=1000&pc=30&pn={page}"
                )

                soup = self._polite_get(search_url)
                if not soup:
                    break  # Blocked or error — stop this area

                # Suumo listing links typically have this pattern:
                # <a href="/jj/bukken/shosai/JJ012FD001/?ar=010&bs=021&nc=12345678">
                # or the link contains a property ID
                #
                # Look for links inside property cards:
                links = soup.select('a[href*="/jj/bukken/shosai/"]')

                if not links:
                    # Also try: links inside .property_unit or .cassetteitem
                    links = soup.select('.property_unit a[href], .cassetteitem a[href]')

                new_urls = []
                for link in links:
                    href = link.get('href', '')
                    if '/shosai/' in href or re.search(r'nc=\d+', href):
                        full_url = href if href.startswith('http') else f"https://suumo.jp{href}"
                        if full_url not in urls and full_url not in new_urls:
                            new_urls.append(full_url)

                if not new_urls:
                    break

                urls.extend(new_urls)
                page += 1

                # Suumo safety limits
                if page > 10:  # Max 10 pages per area (300 listings)
                    break
                if self._request_count > 200:  # Hard stop at 200 requests per run
                    print(f"  Hit request limit ({self._request_count}). Stopping gracefully.")
                    return urls

            print(f"  {area_name}: {len(new_urls) if 'new_urls' in dir() else 0} new URLs")

        print(f"Total Suumo listings found: {len(urls)}")
        return urls

    def extract_listing(self, url):
        """Extract property details from a Suumo detail page."""
        soup = self._polite_get(url)
        if not soup:
            return None

        # Suumo detail pages have a well-structured spec table (物件概要)
        # Usually in <table> with clear <th>/<td> pairs
        #
        # Key headers:
        # 販売価格 = selling price
        # 間取り = rooms/layout
        # 建物面積 = building area
        # 土地面積 = land area
        # 築年月 = year/month built
        # 所在地 = address (full, with prefecture)
        # 沿線・駅 = train line & station
        # 駅徒歩 = walking distance from station
        # 建物構造 = building structure

        specs = {}
        # Try multiple table selectors — Suumo changes layout sometimes
        for table in soup.select('table'):
            for row in table.select('tr'):
                ths = row.select('th')
                tds = row.select('td')
                for th, td in zip(ths, tds):
                    key = th.get_text(strip=True)
                    val = td.get_text(strip=True)
                    if key and val:
                        specs[key] = val

        # Also check <dl> format
        for dl in soup.select('dl'):
            dts = dl.select('dt')
            dds = dl.select('dd')
            for dt, dd in zip(dts, dds):
                key = dt.get_text(strip=True)
                val = dd.get_text(strip=True)
                if key and val:
                    specs[key] = val

        # Address parsing
        address = specs.get('所在地', '') or specs.get('住所', '')
        prefecture, city = self._parse_address(address)

        # Station parsing
        transport = specs.get('沿線・駅', '') or specs.get('交通', '')
        walk_time = specs.get('駅徒歩', '')
        station = ''
        distance = None
        st_match = re.search(r'([^\s「」]+駅)', transport)
        if st_match:
            station = st_match.group(1)
        dist_match = re.search(r'(\d+)分', walk_time or transport)
        if dist_match:
            distance = f"{dist_match.group(1)} min walk"

        # Images
        images = []
        for img in soup.select('.property_view_gallery img, .property_photo img, [class*="bukkenPhoto"] img, .cassette_photo img'):
            src = img.get('data-src') or img.get('data-original') or img.get('src', '')
            if src and 'noimage' not in src and not src.endswith('.gif'):
                if src.startswith('//'):
                    src = f"https:{src}"
                elif src.startswith('/'):
                    src = f"https://suumo.jp{src}"
                images.append(src)

        # Price: try 販売価格 first, then 価格
        price_text = specs.get('販売価格', '') or specs.get('価格', '')

        return RawListing(
            source_slug=self.slug,
            source_url=url,  # REAL Suumo URL
            title=self._extract_title(soup),
            description=self._extract_description(soup),
            price_jpy=parse_japanese_price(price_text),
            prefecture=prefecture,
            city=city,
            address_raw=address,
            building_sqm=parse_area_sqm(specs.get('建物面積', '') or specs.get('専有面積', '')),
            land_sqm=parse_area_sqm(specs.get('土地面積', '') or specs.get('敷地面積', '')),
            year_built=parse_japanese_year(specs.get('築年月', '') or specs.get('築年', '')),
            rooms=specs.get('間取り', ''),
            nearest_station=station,
            station_distance=distance,
            image_urls=images[:20],
            building_type="detached",
            structure=specs.get('建物構造', ''),
        )

    def _extract_title(self, soup):
        og = soup.find('meta', property='og:title')
        if og and og.get('content'):
            return og['content'].strip()
        h1 = soup.find('h1')
        return h1.get_text(strip=True) if h1 else ''

    def _extract_description(self, soup):
        for sel in ['.property_comment', '.bukkenComment', '[class*="appeal"]', '[class*="comment"]']:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True)[:2000]
        og = soup.find('meta', property='og:description')
        return og['content'].strip() if og and og.get('content') else ''

    def _parse_address(self, address_text):
        from config import PREFECTURE_MAP
        for kanji, romaji in PREFECTURE_MAP.items():
            if kanji in address_text:
                after_pref = address_text.split(kanji)[-1]
                city_match = re.match(r'(.+?[市町村区郡])', after_pref)
                city = city_match.group(1) if city_match else ''
                return romaji, city
        return '', ''
```

### Suumo failsafe behavior

If Suumo blocks us (403, CAPTCHA, repeated errors):
1. The adapter stops immediately — it does NOT retry aggressively
2. It saves whatever URLs it collected so far
3. Print a clear message: "Suumo blocked after N requests. Run again tomorrow for more coverage."
4. Next run continues where we left off (the dedup pipeline handles overlaps)

This is by design. We're not trying to DDoS Suumo — we're slowly building up inventory over days/weeks.

---

## Update the adapter registry

In `adapters/__init__.py`, make sure both new adapters are registered:

```python
from .athome_co_jp import AthomeCoJpAdapter
from .suumo_jp import SuumoJpAdapter

# Add to ADAPTER_MAP:
ADAPTER_MAP = {
    # ... existing adapters ...
    "athome-co-jp": AthomeCoJpAdapter,
    "suumo-jp": SuumoJpAdapter,
}
```

## Update `seed_sources.sql`

Add Suumo if not already there:

```sql
INSERT INTO sources (name, slug, base_url, scrape_interval_hours, is_active, notes)
VALUES
    ('Suumo', 'suumo-jp', 'https://suumo.jp', 48, true,
     'Largest Japanese portal. Aggressive anti-scraping — use cautious delays. 48h refresh.')
ON CONFLICT (slug) DO UPDATE SET
    is_active = EXCLUDED.is_active,
    notes = EXCLUDED.notes;
```

Note: 48h refresh interval for Suumo (not 24h) to avoid getting blocked.

## Test plan

### athome (should be straightforward):
1. `python run.py test-adapter athome-co-jp --limit 3`
2. Verify source_url points to athome.co.jp detail page
3. Verify price, address, area parse correctly
4. `python run.py scrape --source athome-co-jp --limit 50`

### Suumo (test carefully):
1. `python run.py test-adapter suumo-jp --limit 3`
2. Watch for 403/CAPTCHA in output
3. If blocked: check robots.txt, adjust User-Agent or delays
4. If working: `python run.py scrape --source suumo-jp --limit 30` (small batch first)
5. Do NOT run --limit 500 on Suumo on first try. Build up slowly.

Test athome FIRST (easier, less risk of blocking). Then Suumo.

## RULES

- source_url MUST point to the REAL athome.co.jp or suumo.jp detail page
- athome: 3 second delay minimum between requests
- Suumo: 5 second delay minimum + random 1-3s jitter
- Suumo: HARD STOP at 200 requests per run. Run multiple times over days for full coverage.
- If Suumo returns 403 or CAPTCHA, stop immediately. Do not retry. Wait at least 30 minutes.
- Reuse parse_japanese_price, parse_japanese_year, parse_area_sqm from utils.py
- All extracted text is in Japanese — our translate pipeline stage handles English conversion
- Build must pass, push to GitHub
```
