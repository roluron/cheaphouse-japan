"""
Scraper adapter for allakiyas.com

Site structure:
  - /en/{prefecture-ken}/traditional-house/for-sale/ — listings by prefecture
  - Each listing is a div.listing containing structured data:
    - City + Prefecture headers
    - Price in USD + JPY (structured)
    - Land area (m²)
    - Building area (m²)
    - Year built
    - Bilingual description (EN + JA)
    - Rooms, floors, structure
  - Images require registration — we extract card data only

Strategy:
  - Iterate through curated prefecture pages
  - Parse each div.listing for structured data
  - 10 listings per page (paginated, we start with page 1)
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from bs4 import BeautifulSoup, Tag

from ingestion.base_adapter import BaseAdapter
from ingestion.models import RawListing
from ingestion.utils import (
    clean_text,
    extract_year_built,
    normalize_prefecture,
    make_absolute_url,
)

logger = logging.getLogger(__name__)

# Prefectures to scrape — curated list of rural/semi-rural areas
SCRAPE_PREFECTURES = [
    "hokkaido",
    "aomori-ken",
    "akita-ken",
    "iwate-ken",
    "yamagata-ken",
    "niigata-ken",
    "nagano-ken",
    "tottori-ken",
    "shimane-ken",
    "okayama-ken",
    "hiroshima-ken",
    "yamaguchi-ken",
    "ehime-ken",
    "kochi-ken",
    "oita-ken",
    "kumamoto-ken",
    "miyazaki-ken",
    "kagoshima-ken",
    "kyoto-fu",
    "nara-ken",
    "wakayama-ken",
    "fukui-ken",
    "shiga-ken",
    "gifu-ken",
]


class AllAkiyasAdapter(BaseAdapter):
    slug = "all-akiyas"
    base_url = "https://www.allakiyas.com"

    def get_listing_urls(self) -> list[str]:
        """Return prefecture page URLs to scrape."""
        return [
            f"{self.base_url}/en/{pref}/traditional-house/for-sale/"
            for pref in SCRAPE_PREFECTURES
        ]

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Not used — we override run() for multi-card extraction."""
        return None

    def run(self) -> list[RawListing]:
        """
        Custom run: iterate prefecture pages, extract all div.listing cards.
        """
        logger.info(f"[{self.slug}] Starting multi-prefecture scrape...")
        all_listings: list[RawListing] = []
        errors = 0

        for pref_slug in SCRAPE_PREFECTURES:
            url = f"{self.base_url}/en/{pref_slug}/traditional-house/for-sale/"
            try:
                html = self.fetch_page(url)
                listings = self._extract_listings(html, pref_slug, url)
                all_listings.extend(listings)
                logger.info(
                    f"[{self.slug}] {pref_slug}: {len(listings)} listings"
                )
            except Exception as e:
                errors += 1
                logger.error(f"[{self.slug}] Error on {pref_slug}: {e}")

            time.sleep(self.delay)

        logger.info(
            f"[{self.slug}] Complete: {len(all_listings)} listings "
            f"from {len(SCRAPE_PREFECTURES)} prefectures, {errors} errors."
        )
        return all_listings

    def _extract_listings(
        self, html: str, pref_slug: str, page_url: str
    ) -> list[RawListing]:
        """Extract all div.listing cards from a prefecture page."""
        soup = BeautifulSoup(html, "lxml")
        cards = soup.find_all("div", class_="listing")
        listings = []

        prefecture = self._slug_to_prefecture(pref_slug)

        for i, card in enumerate(cards):
            try:
                listing = self._parse_card(card, prefecture, pref_slug, page_url, i)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.warning(f"[{self.slug}] Error parsing card {i} on {pref_slug}: {e}")

        return listings

    def _parse_card(
        self, card: Tag, prefecture: str, pref_slug: str,
        page_url: str, index: int
    ) -> Optional[RawListing]:
        """Parse a single div.listing card into a RawListing."""
        text = card.get_text()

        # ── City ─────────────────────────────────────────
        city = self._extract_city(card)

        # ── Price ────────────────────────────────────────
        price_jpy = self._extract_price_jpy(text)
        price_usd = self._extract_price_usd(text)
        price_raw = None
        if price_jpy:
            price_raw = f"¥{price_jpy:,}"
        elif price_usd:
            price_raw = f"${price_usd:,}"

        # ── Areas ────────────────────────────────────────
        land_sqm = self._extract_metric(text, "Land", "土地面積")
        building_sqm = self._extract_metric(text, "Building", "建物面積")

        # ── Year built ───────────────────────────────────
        year_built = self._extract_year(text)

        # ── Description ──────────────────────────────────
        description = self._extract_description(text)

        # ── Rooms/Layout ─────────────────────────────────
        rooms = self._extract_rooms(text)

        # ── Floors ───────────────────────────────────────
        floors = self._extract_floors(text)

        # ── Structure ────────────────────────────────────
        structure = self._extract_structure(text)

        # Skip if we got essentially nothing
        if not description and not price_jpy and not building_sqm:
            return None

        # Generate unique ID
        city_slug = (city or "unknown").lower().replace(" ", "-")
        listing_id = f"{pref_slug}-{city_slug}-{index}"

        title = f"Traditional House in {city or 'Unknown'}, {prefecture}"

        return RawListing(
            source_slug=self.slug,
            source_listing_id=listing_id,
            source_url=page_url,
            title=title,
            description=description,
            price_raw=price_raw,
            price_jpy=price_jpy,
            prefecture=prefecture,
            city=city,
            land_sqm=land_sqm,
            building_sqm=building_sqm,
            year_built=year_built,
            rooms=rooms,
            floors=floors,
            building_type="detached",
            structure=structure,
            image_urls=[],
        )

    # ── Extraction helpers ───────────────────────────────

    def _extract_city(self, card: Tag) -> Optional[str]:
        """Extract city name from the listing card header links."""
        # Look for "Traditional houses for sale in CityName"
        for a in card.find_all("a", href=True):
            link_text = a.get_text()
            match = re.search(
                r"(?:for sale|for rent) in (.+?)$", link_text, re.IGNORECASE
            )
            if match:
                city = match.group(1).strip()
                # Skip if it's just the prefecture
                if "Ken" not in city and "Fu" not in city:
                    return city
        return None

    def _extract_price_jpy(self, text: str) -> Optional[int]:
        """Extract JPY price: '¥2,300,000' or '230 万円'."""
        # Try ¥ format first
        match = re.search(r"[¥￥]([\d,]+)", text)
        if match:
            try:
                val = int(match.group(1).replace(",", ""))
                if val >= 1:
                    return val
            except ValueError:
                pass

        # Try 万円 format
        match = re.search(r"([\d,]+)\s*万円", text)
        if match:
            try:
                return int(float(match.group(1).replace(",", "")) * 10_000)
            except ValueError:
                pass

        return None

    def _extract_price_usd(self, text: str) -> Optional[int]:
        """Extract USD price: 'USD $14,746'."""
        match = re.search(r"USD\s*\$\s*([\d,]+)", text)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                pass
        return None

    def _extract_metric(self, text: str, en_label: str, ja_label: str) -> Optional[float]:
        """Extract a metric like 'Land土地面積659 m²' or 'Building建物面積133 m²'."""
        pattern = rf"(?:{en_label}|{ja_label})\s*([\d,.]+)\s*(?:m²|㎡)"
        match = re.search(pattern, text)
        if match:
            try:
                return round(float(match.group(1).replace(",", "")), 1)
            except ValueError:
                pass
        return None

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year built: 'Built建築年1975'."""
        match = re.search(r"(?:Built|建築年)\s*(\d{4})", text)
        if match:
            year = int(match.group(1))
            if 1900 <= year <= 2030:
                return year
        return None

    def _extract_description(self, text: str) -> Optional[str]:
        """Extract the English description from the bilingual card text."""
        # The description appears after the structured data (price, area, year)
        # and before the Japanese text or the Scale/Layout section

        # Find the content between the structured header and the structured sections
        # Look for text after the year/area data but before Scale/Layout
        match = re.search(
            r"(?:Built建築年\d{4}|m²|㎡)\s*(.+?)(?:Scale / Layout|構造・間取り|View more)",
            text, re.DOTALL
        )
        if match:
            desc = match.group(1).strip()
            # Try to get just the English part (before the Japanese text)
            # Japanese text typically starts with a series of kanji/hiragana
            # Split at the point where we see a long run of Japanese characters
            jp_split = re.split(r"[。！？]\s*(?=[ぁ-ん\u4e00-\u9fff]{4,})", desc, maxsplit=1)
            if jp_split:
                en_desc = jp_split[0].strip()
                if len(en_desc) > 20:
                    return clean_text(en_desc)
            return clean_text(desc[:500])
        return None

    def _extract_rooms(self, text: str) -> Optional[str]:
        """Extract room layout: '7DK + 2 solariums', '6K', etc."""
        # Look in Floor plan section
        match = re.search(r"Floor plan:\s*(.+?)(?:\n|$|間取り)", text)
        if match:
            return clean_text(match.group(1))

        # Fallback: Japanese room format
        match = re.search(r"(\d+[LDKS]{1,4}(?:\+.+?)?)\b", text)
        if match:
            return match.group(1)
        return None

    def _extract_floors(self, text: str) -> Optional[int]:
        """Extract number of floors."""
        if "One-story" in text or "平屋" in text:
            return 1
        match = re.search(r"(\d+)\s*stor", text, re.IGNORECASE)
        if match:
            val = int(match.group(1))
            if 1 <= val <= 5:
                return val
        return None

    def _extract_structure(self, text: str) -> Optional[str]:
        """Extract structure type from the Structure section."""
        match = re.search(r"Structure構造\s*(.+?)(?:\n|View more|Register)", text)
        if match:
            struct = match.group(1).strip()
            # Get just the English part
            if "木造" in struct:
                idx = struct.find("木")
                struct = struct[:idx].strip() if idx > 0 else struct
            return clean_text(struct) if struct else None
        return None

    def _slug_to_prefecture(self, slug: str) -> str:
        """Convert 'yamaguchi-ken' → 'Yamaguchi'."""
        name = slug.replace("-ken", "").replace("-fu", "").replace("-to", "").replace("-do", "")
        name = name.replace("-", " ").title()
        return normalize_prefecture(name) or name
