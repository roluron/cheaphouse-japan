"""
Eikoh Home (eikohome.co.jp) adapter.
Scrapes houses from a small Nara-based real estate agent.

This is a small, static HTML site with a limited but curated inventory
of rural properties in Nara Prefecture (奈良県). High-quality listings.

Categories scraped:
- /estate/item/existing/ — 中古住宅 (used houses)
- /estate/item/inaka/ — 田舎物件 (rural properties)
Skipped: /estate/item/tochi/ (land only), /estate/item/other/ (commercial)
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.base_adapter import BaseAdapter
from ingestion.models import RawListing
from ingestion.utils import (
    parse_price_jpy,
    parse_area_sqm,
    extract_year_built,
    clean_text,
    make_absolute_url,
)

logger = logging.getLogger(__name__)


class EikohHomeAdapter(BaseAdapter):
    """Adapter for Eikoh Home — eikohome.co.jp (Nara)."""

    slug = "eikohome"
    base_url = "https://www.eikohome.co.jp"

    # Categories to scrape (houses only, no land)
    INDEX_URL = "https://www.eikohome.co.jp/estate/index.html"
    HOUSE_CATEGORIES = {"existing", "inaka"}  # Skip 'tochi' (land) and 'other'

    def __init__(self):
        super().__init__()
        self.delay = 2
        self.client.headers.update({
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        })

    def get_listing_urls(self) -> list[str]:
        """Crawl the property index page for listing URLs."""
        html = self.fetch_page(self.INDEX_URL)
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []

        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if "/estate/item/" not in href or ".html" not in href:
                continue
            # Check category — only houses
            category = href.split("/item/")[1].split("/")[0] if "/item/" in href else ""
            if category not in self.HOUSE_CATEGORIES:
                continue
            full_url = make_absolute_url(self.base_url, href)
            if full_url not in urls:
                urls.append(full_url)

        logger.info(f"[{self.slug}] Found {len(urls)} house listings")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Parse a single listing detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Title from <title> tag
        title_tag = soup.select_one("title")
        title = None
        if title_tag:
            title = clean_text(title_tag.get_text().split("|")[0].split("｜")[0])
        if not title:
            h1 = soup.select_one("h1, h2")
            title = clean_text(h1.get_text()) if h1 else None
        if not title:
            return None

        # Listing ID from URL (e.g., e102.html → e102)
        id_match = re.search(r'/(\w+)\.html$', url)
        listing_id = id_match.group(1) if id_match else None

        # Extract spec table
        specs = self._extract_specs(soup)

        # Price
        price_raw = specs.get("金額", "") or specs.get("価格", "") or specs.get("販売価格", "")
        price_jpy = parse_price_jpy(price_raw) if price_raw else None

        # Areas
        building_text = specs.get("建物面積", "") or specs.get("延床面積", "")
        land_text = specs.get("土地面積", "") or specs.get("敷地面積", "")

        # Layout
        rooms = None
        layout_text = specs.get("間取", "") or specs.get("間取り", "")
        if layout_text:
            layout_text = layout_text.translate(
                str.maketrans("０１２３４５６７８９", "0123456789")
            )
            m = re.search(r"\d+[SLDK]+", layout_text)
            rooms = m.group(0) if m else clean_text(layout_text)

        # Year built (support Japanese era: 昭和, 平成, 令和)
        year_text = specs.get("築年月日", "") or specs.get("築年月", "") or specs.get("築年", "")
        year_built = self._parse_year(year_text)

        # Address
        address_raw = specs.get("所在地", "") or specs.get("住所", "") or specs.get("物件名", "")

        # Station/access
        access = specs.get("アクセス", "") or specs.get("交通", "")
        station, distance = self._parse_transport(access)

        # Structure
        structure_text = specs.get("建物構造", "") or specs.get("構造", "")
        structure = self._parse_structure(structure_text)

        # Images
        images = self._extract_images(soup, url)

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=listing_id,
            title=title,
            price_jpy=price_jpy,
            price_raw=clean_text(price_raw) if price_raw else None,
            prefecture="Nara",  # Eikoh Home operates in Nara
            city=self._extract_city(address_raw),
            address_raw=clean_text(address_raw) if address_raw else None,
            building_sqm=parse_area_sqm(building_text),
            land_sqm=parse_area_sqm(land_text),
            year_built=year_built,
            rooms=rooms,
            nearest_station=station,
            station_distance=distance,
            image_urls=images,
            building_type="detached",
            structure=structure,
        )

    def _extract_specs(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract all spec values from tables."""
        specs: dict[str, str] = {}
        for table in soup.select("table"):
            for row in table.select("tr"):
                cells = row.select("th, td")
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if key and val:
                        specs[key] = val
        return specs

    def _parse_year(self, text: str) -> Optional[int]:
        if not text:
            return None
        # Try Western year first
        m = re.search(r"(\d{4})年", text)
        if m:
            y = int(m.group(1))
            if 1900 <= y <= 2030:
                return y
        # Japanese era conversion
        era_map = {"昭和": 1925, "平成": 1988, "令和": 2018}
        for era, offset in era_map.items():
            if era in text:
                m2 = re.search(rf"{era}(\d+)年", text)
                if m2:
                    return offset + int(m2.group(1))
        return extract_year_built(text)

    def _extract_city(self, address: str) -> Optional[str]:
        if not address:
            return None
        m = re.search(r"(.+?[市町村区郡])", address)
        return clean_text(m.group(1)) if m else None

    def _parse_transport(self, text: str) -> tuple[Optional[str], Optional[str]]:
        if not text:
            return None, None
        text = text.replace("「", "").replace("」", "")
        station = None
        distance = None
        st_match = re.search(r"([^\s/]+駅)", text)
        if st_match:
            station = st_match.group(1)
        dist_match = re.search(r"徒歩[約\s]*(\d+)\s*分", text)
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

    def _extract_images(self, soup: BeautifulSoup, page_url: str) -> list[str]:
        images: list[str] = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if "/images/item/" in src or "/estate/" in src:
                if "noimage" in src.lower() or "icon" in src.lower():
                    continue
                full = make_absolute_url(self.base_url, src)
                if full not in images:
                    images.append(full)
        return images[:20]
