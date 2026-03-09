"""
at home (athome.co.jp) adapter.
Scrapes cheap detached houses from Japan's major real estate portal.
Strong rural coverage — ideal for akiya and countryside properties.

Target: 中古一戸建て (used detached houses) under ¥10M across all prefectures.

Strategy: Extract data directly from search result cards (.card-box elements)
since athome's detail pages use bot protection (認証中 challenge).
The search result cards contain ALL property data we need.
"""

from __future__ import annotations

import logging
import re
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


class AthomeCoJpAdapter(BaseAdapter):
    """
    Adapter for at home — athome.co.jp.

    Extracts data from search result cards (.card-box) rather than
    individual detail pages, since athome uses bot protection on
    detail page visits.
    """

    slug = "athome-co-jp"
    base_url = "https://www.athome.co.jp"

    # Per-prefecture search URLs for used detached houses.
    # price_to in 万円 units (1000 = ¥10M, 500 = ¥5M).
    REGION_SEARCH_URLS = [
        # ── Hokkaido & Tohoku ──────────────────────────────
        "https://www.athome.co.jp/kodate/chuko/hokkaido/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/aomori/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/akita/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/iwate/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/yamagata/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/miyagi/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/fukushima/list/?price_to=1000",
        # ── Kanto ──────────────────────────────────────────
        "https://www.athome.co.jp/kodate/chuko/ibaraki/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/tochigi/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/gunma/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/chiba/list/?price_to=500",
        "https://www.athome.co.jp/kodate/chuko/saitama/list/?price_to=500",
        # ── Chubu ──────────────────────────────────────────
        "https://www.athome.co.jp/kodate/chuko/niigata/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/nagano/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/toyama/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/ishikawa/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/fukui/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/yamanashi/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/gifu/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/shizuoka/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/aichi/list/?price_to=500",
        # ── Kinki ──────────────────────────────────────────
        "https://www.athome.co.jp/kodate/chuko/shiga/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kyoto/list/?price_to=500",
        "https://www.athome.co.jp/kodate/chuko/nara/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/wakayama/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/hyogo/list/?price_to=500",
        "https://www.athome.co.jp/kodate/chuko/mie/list/?price_to=1000",
        # ── Chugoku ────────────────────────────────────────
        "https://www.athome.co.jp/kodate/chuko/tottori/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/shimane/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/okayama/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/hiroshima/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/yamaguchi/list/?price_to=1000",
        # ── Shikoku ────────────────────────────────────────
        "https://www.athome.co.jp/kodate/chuko/tokushima/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kagawa/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/ehime/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kochi/list/?price_to=1000",
        # ── Kyushu & Okinawa ───────────────────────────────
        "https://www.athome.co.jp/kodate/chuko/fukuoka/list/?price_to=500",
        "https://www.athome.co.jp/kodate/chuko/saga/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/nagasaki/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kumamoto/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/oita/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/miyazaki/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/kagoshima/list/?price_to=1000",
        "https://www.athome.co.jp/kodate/chuko/okinawa/list/?price_to=1000",
    ]

    MAX_PAGES_PER_PREFECTURE = 30

    def __init__(self):
        super().__init__()
        self.delay = 3  # 3s between requests
        # athome requires Accept-Language: ja to return full property cards.
        # Without it, the server returns a 7KB stripped page instead of 1.1MB.
        self.client.headers.update({
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
        })

    # ── Override: we extract from search cards, not detail pages ──

    def get_listing_urls(self) -> list[str]:
        """Not used — we extract directly from cards. Returns empty."""
        return []

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Not used — data extracted from search result cards."""
        return None

    def run(self) -> list[RawListing]:
        """
        Override BaseAdapter.run() to scrape search result pages
        and extract listings from cards, not individual detail pages.
        """
        import time

        logger.info(f"[{self.slug}] Starting card-based scrape run...")
        results: list[RawListing] = []
        seen_ids: set[str] = set()

        for search_url in self.REGION_SEARCH_URLS:
            pref_slug = search_url.split("/list/")[0].split("/")[-1]
            page = 1

            while page <= self.MAX_PAGES_PER_PREFECTURE:
                if page > 1:
                    paginated_url = f"{search_url}&page={page}"
                else:
                    paginated_url = search_url

                logger.info(f"[{self.slug}] {pref_slug} page {page}...")

                try:
                    html = self.fetch_page(paginated_url)
                except Exception as e:
                    logger.warning(f"[{self.slug}] {pref_slug} p{page} failed: {e}")
                    break

                soup = BeautifulSoup(html, "lxml")
                cards = soup.select(".card-box")

                if not cards:
                    break

                new_on_page = 0
                for card in cards:
                    listing = self._extract_from_card(card, pref_slug)
                    if listing and listing.source_listing_id not in seen_ids:
                        seen_ids.add(listing.source_listing_id or listing.source_url)
                        results.append(listing)
                        new_on_page += 1

                logger.info(
                    f"[{self.slug}] {pref_slug} p{page}: "
                    f"+{new_on_page} listings ({len(results)} total)"
                )

                if new_on_page == 0:
                    break

                page += 1
                time.sleep(self.delay)

        logger.info(
            f"[{self.slug}] Run complete: {len(results)} listings extracted."
        )
        return results

    # ── Card extraction ──────────────────────────────────

    def _extract_from_card(self, card: Tag, pref_slug: str) -> Optional[RawListing]:
        """Extract a RawListing from a single .card-box element."""

        # Get listing ID from checkbox or link
        checkbox = card.select_one("input[type='checkbox'][id]")
        listing_id = checkbox.get("id") if checkbox else None

        # Build detail URL (even though we can't visit it, it's the source_url)
        detail_link = card.select_one("a[href*='/kodate/']")
        if detail_link:
            href = detail_link.get("href", "").split("?")[0]
            source_url = make_absolute_url(self.base_url, href)
        elif listing_id:
            source_url = f"{self.base_url}/kodate/{listing_id}/"
        else:
            return None

        # Title from .title-wrap__title-text
        title_el = card.select_one(".title-wrap__title-text")
        title = clean_text(title_el.get_text()) if title_el else None
        if not title:
            return None

        # Extract spec table data: .property-detail-table__block contains
        # pairs of labels and values
        specs = self._extract_card_specs(card)

        # Price
        price_el = card.select_one(".property-price")
        price_raw = clean_text(price_el.get_text()) if price_el else specs.get("価格", "")

        # Address → prefecture + city
        address = specs.get("所在地", "") or specs.get("住所", "")
        prefecture, city = self._parse_address(address)

        # If no prefecture from address, use the slug
        if not prefecture:
            prefecture = normalize_prefecture(pref_slug) or pref_slug.capitalize()

        # Transport → station + distance
        transport = specs.get("交通", "") or specs.get("最寄り駅", "")
        station, distance = self._parse_transport(transport)

        # Images from swiper slides
        images = self._extract_card_images(card)

        return RawListing(
            source_slug=self.slug,
            source_url=source_url,  # Original athome.co.jp URL
            source_listing_id=listing_id,
            title=title,
            price_jpy=parse_price_jpy(price_raw) if price_raw else None,
            price_raw=price_raw,
            prefecture=prefecture,
            city=city,
            address_raw=clean_text(address) if address else None,
            building_sqm=parse_area_sqm(specs.get("建物面積", "") or specs.get("専有面積", "")),
            land_sqm=parse_area_sqm(specs.get("土地面積", "") or specs.get("敷地面積", "")),
            year_built=extract_year_built(specs.get("築年月", "") or specs.get("築年", "")),
            rooms=self._extract_layout(specs),
            nearest_station=station,
            station_distance=distance,
            image_urls=images,
            building_type="detached",
            structure=self._parse_structure(specs.get("構造", "") or specs.get("建物構造", "")),
        )

    def _extract_card_specs(self, card: Tag) -> dict[str, str]:
        """Extract spec data from .property-detail-table__block elements."""
        specs: dict[str, str] = {}

        # Each block contains a label (th/dt) and value (td/dd)
        for block in card.select(".property-detail-table__block"):
            text = block.get_text(separator="|", strip=True)
            parts = text.split("|", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip()
                if key and val:
                    specs[key] = val

        # Also try .property-detail-table__group which has th/td
        for group in card.select(".property-detail-table__group"):
            th = group.select_one("th, dt, .label")
            td = group.select_one("td, dd, .value")
            if th and td:
                key = th.get_text(strip=True)
                val = td.get_text(strip=True)
                if key and val and key not in specs:
                    specs[key] = val

        return specs

    def _extract_card_images(self, card: Tag) -> list[str]:
        """Extract images from the card's swiper/gallery."""
        images: list[str] = []
        for img in card.select(".swiper-slide img, .bukken-item img"):
            src = img.get("src", "") or img.get("data-src", "")
            if not src or src.startswith("data:"):
                continue
            if "noimage" in src.lower() or "icon" in src.lower():
                continue
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)
        return images[:20]

    def _extract_layout(self, specs: dict[str, str]) -> Optional[str]:
        text = specs.get("間取り", "")
        if text:
            # Normalize full-width to half-width
            text = text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
            match = re.search(r"\d+[SLDK]+", text)
            return match.group(0) if match else clean_text(text)
        return None

    def _parse_address(self, address_text: str) -> tuple[Optional[str], Optional[str]]:
        if not address_text:
            return None, None
        for kanji, romaji in PREFECTURE_MAP.items():
            if kanji in address_text:
                after_pref = address_text.split(kanji)[-1]
                city_match = re.match(r"(.+?[市町村区郡])", after_pref)
                city = clean_text(city_match.group(1)) if city_match else None
                return romaji, city
        return None, None

    def _parse_transport(self, transport_text: str) -> tuple[Optional[str], Optional[str]]:
        if not transport_text:
            return None, None
        station = None
        distance = None
        # Clean up full-width quotes
        transport_text = transport_text.replace("「", "").replace("」", "")
        st_match = re.search(r"([^\s/]+駅)", transport_text)
        if st_match:
            station = st_match.group(1)
        dist_match = re.search(r"徒歩\s*(\d+)\s*分", transport_text)
        if dist_match:
            distance = f"{dist_match.group(1)} min walk"
        return station, distance

    def _parse_structure(self, text: str) -> Optional[str]:
        if not text:
            return None
        if "木造" in text:
            return "wood"
        if "鉄骨" in text or "S造" in text:
            return "steel"
        if "鉄筋" in text or "RC" in text:
            return "rc"
        return clean_text(text)
