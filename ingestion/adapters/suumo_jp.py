"""
Suumo (suumo.jp) adapter.
Scrapes detached houses from Japan's largest real estate portal.

Two search modes:
1. KEYWORD search: Premium/character houses using Japanese keywords:
   - 設計士住宅 (architect-designed house)
   - デザイナーズ住宅 (designer house)
   - 古民家 (traditional old house/kominka)
   - 自然素材 (natural materials)
   - 平屋 (single-story house)
2. PRICE search: 中古一戸建て (used detached houses) under ¥10M across all areas

Strategy: Extract data from search result cards (.property_unit elements)
instead of visiting individual detail pages.

Suumo has AGGRESSIVE anti-scraping. This adapter uses:
- 5-8s randomized delays between requests
- Browser-like headers with Accept-Language: ja
- Immediate stop on 403/CAPTCHA
- Hard limit of 200 requests per run
"""

from __future__ import annotations

import logging
import random
import urllib.parse
import re
import time
from typing import Optional

from bs4 import BeautifulSoup, Tag

from ingestion.base_adapter import BaseAdapter
from ingestion.config import PREFECTURE_MAP
from ingestion.models import RawListing
from ingestion.utils import (
    parse_price_jpy,
    parse_area_sqm,
    extract_year_built,
    normalize_prefecture,
    clean_text,
    make_absolute_url,
)

logger = logging.getLogger(__name__)


class SuumoJpAdapter(BaseAdapter):
    """
    Adapter for Suumo — suumo.jp.

    Extremely cautious scraping. Card-based extraction from search results.
    """

    slug = "suumo-jp"
    base_url = "https://suumo.jp"

    # Area codes for Suumo search (ar= parameter)
    AREA_CODES = {
        "010": "Hokkaido",
        "020": "Aomori/Iwate/Miyagi/Akita/Yamagata/Fukushima",
        "030": "Ibaraki/Tochigi/Gunma",
        "040": "Saitama/Chiba",
        "060": "Niigata/Toyama/Ishikawa/Fukui/Yamanashi/Nagano",
        "070": "Gifu/Shizuoka/Aichi/Mie",
        "080": "Shiga/Kyoto/Nara/Wakayama/Hyogo",
        "090": "Tottori/Shimane/Okayama/Hiroshima/Yamaguchi",
        "100": "Tokushima/Kagawa/Ehime/Kochi",
        "110": "Fukuoka/Saga/Nagasaki/Kumamoto/Oita/Miyazaki/Kagoshima/Okinawa",
    }

    # Search URL template for used detached houses under ¥10M
    SEARCH_TEMPLATE = (
        "https://suumo.jp/jj/bukken/ichiran/JJ012FC001/"
        "?ar={area}&bs=021&kb=1&kt=1000&pc=30&page={page}"
    )

    # Keyword search template — no price cap, curated keywords
    KEYWORD_SEARCH_TEMPLATE = (
        "https://suumo.jp/jj/bukken/ichiran/JJ012FC001/"
        "?ar={area}&bs=021&fw={keyword}&pc=30&page={page}"
    )

    # Premium keywords — architect/designer/character houses
    PREMIUM_KEYWORDS = [
        "設計士住宅",
        "デザイナーズ住宅",
        "古民家",
        "自然素材",
        "平屋",
    ]

    MAX_PAGES_PER_AREA = 10
    MAX_PAGES_PER_KEYWORD = 3  # Keywords return fewer results
    MAX_REQUESTS = 200  # Hard limit per run
    MIN_DELAY = 5
    MAX_DELAY = 8

    def __init__(self):
        super().__init__()
        self.delay = 5  # Base delay
        self._request_count = 0
        self._blocked = False
        # Suumo needs proper Japanese browser headers
        self.client.headers.update({
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Upgrade-Insecure-Requests": "1",
        })

    # ── Override: extract from search cards ──

    def get_listing_urls(self) -> list[str]:
        """Not used."""
        return []

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Not used."""
        return None

    def _polite_delay(self) -> None:
        """Randomized delay between requests (5-8s)."""
        delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
        time.sleep(delay)

    def _safe_fetch(self, url: str) -> Optional[str]:
        """Fetch with anti-scraping checks."""
        if self._blocked:
            return None
        if self._request_count >= self.MAX_REQUESTS:
            logger.warning(f"[{self.slug}] Request limit ({self.MAX_REQUESTS}) reached.")
            self._blocked = True
            return None

        self._polite_delay()
        self._request_count += 1

        try:
            resp = self.client.get(url, follow_redirects=True)

            if resp.status_code == 403:
                logger.error(f"[{self.slug}] 403 FORBIDDEN — blocked! Stopping.")
                self._blocked = True
                return None

            if resp.status_code != 200:
                logger.warning(f"[{self.slug}] HTTP {resp.status_code}")
                return None

            # Check for CAPTCHA — look for actual blocking pages,
            # not just the word "robot" which appears in normal footer text.
            text_lower = resp.text[:3000].lower()
            if any(marker in text_lower for marker in [
                "captcha", "recaptcha", "are you a robot",
                "アクセスが制限されています", "アクセス制限",
                "不正なアクセス",
            ]):
                logger.error(f"[{self.slug}] CAPTCHA/block detected! Stopping.")
                self._blocked = True
                return None

            return resp.text

        except Exception as e:
            logger.error(f"[{self.slug}] Fetch error: {e}")
            return None

    def run(self) -> list[RawListing]:
        """Override BaseAdapter.run() for card-based extraction."""
        logger.info(f"[{self.slug}] Starting CAUTIOUS card-based scrape run...")
        logger.info(f"[{self.slug}] Config: {self.MIN_DELAY}-{self.MAX_DELAY}s delay, max {self.MAX_REQUESTS} requests")

        results: list[RawListing] = []
        seen_ids: set[str] = set()

        # ── Phase 1: KEYWORD search (premium/character houses) ──
        logger.info(f"[{self.slug}] Phase 1: Premium keyword searches...")
        for keyword in self.PREMIUM_KEYWORDS:
            if self._blocked:
                break
            kw_encoded = urllib.parse.quote(keyword)

            for area_code, area_name in self.AREA_CODES.items():
                if self._blocked:
                    break

                for page in range(1, self.MAX_PAGES_PER_KEYWORD + 1):
                    if self._blocked:
                        break

                    url = self.KEYWORD_SEARCH_TEMPLATE.format(
                        area=area_code, keyword=kw_encoded, page=page
                    )
                    new = self._scrape_page(url, results, seen_ids)

                    label = f"{keyword} {area_name} p{page}"
                    logger.info(
                        f"[{self.slug}] {label}: "
                        f"+{new} ({len(results)} total, req #{self._request_count})"
                    )
                    if new == 0:
                        break

        # ── Phase 2: PRICE search (cheap houses ≤¥10M) ──
        logger.info(f"[{self.slug}] Phase 2: Price-based search (≤¥10M)...")
        for area_code, area_name in self.AREA_CODES.items():
            if self._blocked:
                break

            for page in range(1, self.MAX_PAGES_PER_AREA + 1):
                if self._blocked:
                    break

                url = self.SEARCH_TEMPLATE.format(area=area_code, page=page)
                new = self._scrape_page(url, results, seen_ids)

                logger.info(
                    f"[{self.slug}] {area_name} p{page}: "
                    f"+{new} ({len(results)} total, req #{self._request_count})"
                )
                if new == 0:
                    break

        logger.info(
            f"[{self.slug}] Run complete: {len(results)} listings, "
            f"{self._request_count} requests made."
        )
        return results

    def _scrape_page(
        self,
        url: str,
        results: list[RawListing],
        seen_ids: set[str],
    ) -> int:
        """Fetch one search page, extract cards, return count of new listings."""
        html = self._safe_fetch(url)
        if not html:
            return 0

        soup = BeautifulSoup(html, "lxml")
        cards = soup.select(".property_unit")
        if not cards:
            return 0

        new_count = 0
        for card in cards:
            listing = self._extract_from_card(card)
            if listing:
                lid = listing.source_listing_id or listing.source_url
                if lid not in seen_ids:
                    seen_ids.add(lid)
                    results.append(listing)
                    new_count += 1

        return new_count

    # ── Card extraction ──────────────────────────────────

    def _extract_from_card(self, card: Tag) -> Optional[RawListing]:
        """Extract a RawListing from a single .property_unit element."""

        # Find detail link for source_url
        detail_link = card.select_one("a[href]")
        source_url = None
        listing_id = None

        for a in card.select("a[href]"):
            href = a.get("href", "")
            if "/bukken/" in href or "/chukoikkodate/" in href:
                source_url = make_absolute_url(self.base_url, href.split("?")[0])
                # Extract nc= (listing ID) from URL
                nc_match = re.search(r'nc=(\d+)', a.get("href", ""))
                if nc_match:
                    listing_id = nc_match.group(1)
                break

        if not source_url:
            # Use any link
            if detail_link:
                source_url = make_absolute_url(
                    self.base_url, detail_link.get("href", "").split("?")[0]
                )
            else:
                return None

        # Extract spec data from .dottable-line rows
        specs = self._extract_specs(card)

        # Title
        title = specs.get("物件名", "")
        if not title:
            title_el = card.select_one(".property_unit-title, h2, h3")
            title = clean_text(title_el.get_text()) if title_el else None
        if not title:
            return None

        # Price
        price_raw = specs.get("販売価格", "") or specs.get("価格", "")
        price_jpy = parse_price_jpy(price_raw) if price_raw else None

        # Address → prefecture + city
        address = specs.get("所在地", "") or specs.get("住所", "")
        prefecture, city = self._parse_address(address)

        # Station
        transport = specs.get("沿線・駅", "") or specs.get("交通", "")
        station, distance = self._parse_transport(transport)

        # Areas
        land_text = specs.get("土地面積", "")
        building_text = specs.get("建物面積", "") or specs.get("専有面積", "")

        # Year built
        year_text = specs.get("築年月", "") or specs.get("築年", "")

        # Layout
        rooms_text = specs.get("間取り", "")
        rooms = None
        if rooms_text:
            rooms_text_hw = rooms_text.translate(
                str.maketrans("０１２３４５６７８９", "0123456789")
            )
            m = re.search(r"\d+[SLDK]+", rooms_text_hw)
            rooms = m.group(0) if m else clean_text(rooms_text)

        # Images
        images = self._extract_images(card)

        return RawListing(
            source_slug=self.slug,
            source_url=source_url,
            source_listing_id=listing_id,
            title=clean_text(title),
            price_jpy=price_jpy,
            price_raw=clean_text(price_raw) if price_raw else None,
            prefecture=prefecture,
            city=city,
            address_raw=clean_text(address) if address else None,
            building_sqm=parse_area_sqm(building_text),
            land_sqm=parse_area_sqm(land_text),
            year_built=extract_year_built(year_text),
            rooms=rooms,
            nearest_station=station,
            station_distance=distance,
            image_urls=images,
            building_type="detached",
        )

    def _extract_specs(self, card: Tag) -> dict[str, str]:
        """Extract specs from .dottable-line rows in the card."""
        specs: dict[str, str] = {}

        for row in card.select(".dottable-line, tr"):
            # Try dt/dd pattern
            dt = row.select_one("dt, th")
            dd = row.select_one("dd, td")
            if dt and dd:
                key = dt.get_text(strip=True)
                val = dd.get_text(strip=True)
                if key and val:
                    specs[key] = val

        # Also check the card text for labeled data
        card_text = card.get_text(separator="\n")
        for label in ["物件名", "販売価格", "所在地", "沿線・駅", "土地面積",
                       "建物面積", "間取り", "築年月"]:
            if label not in specs and label in card_text:
                idx = card_text.index(label)
                after = card_text[idx + len(label):]
                val = after.split("\n")[0].strip().lstrip(":：\t ")
                if not val and "\n" in after:
                    val = after.split("\n")[1].strip()
                if val:
                    specs[label] = val

        return specs

    def _extract_images(self, card: Tag) -> list[str]:
        """Extract images from the card."""
        images: list[str] = []
        for img in card.select("img[src], img[data-src]"):
            src = img.get("data-src") or img.get("src", "")
            if not src or src.startswith("data:") or "noimage" in src.lower():
                continue
            if "icon" in src.lower() or "logo" in src.lower():
                continue
            if "sprite" in src.lower():
                continue
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)
        return images[:20]

    def _parse_address(self, address_text: str) -> tuple[Optional[str], Optional[str]]:
        if not address_text:
            return None, None
        for kanji, romaji in PREFECTURE_MAP.items():
            if kanji in address_text:
                after = address_text.split(kanji)[-1]
                city_match = re.match(r"(.+?[市町村区郡])", after)
                city = clean_text(city_match.group(1)) if city_match else None
                return romaji, city
        return None, None

    def _parse_transport(self, transport_text: str) -> tuple[Optional[str], Optional[str]]:
        if not transport_text:
            return None, None
        transport_text = transport_text.replace("「", "").replace("」", "")
        station = None
        distance = None
        st_match = re.search(r"([^\s/]+駅)", transport_text)
        if st_match:
            station = st_match.group(1)
        dist_match = re.search(r"徒歩\s*(\d+)\s*分", transport_text)
        if dist_match:
            distance = f"{dist_match.group(1)} min walk"
        return station, distance
