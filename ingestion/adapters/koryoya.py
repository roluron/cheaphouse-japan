"""
KORYOYA (koryoya.com) adapter.
Scrapes traditional Japanese houses built before 1950.

KORYOYA specializes in kominka (古民家) — old wooden houses with
traditional timber-frame construction. Small curated inventory,
all in English, all with rich spec tables.

Strategy: Scrape listing URLs from homepage, then extract spec tables
from each detail page. All data is in English.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.base_adapter import BaseAdapter
from ingestion.models import RawListing
from ingestion.utils import (
    parse_area_sqm,
    clean_text,
    make_absolute_url,
)

logger = logging.getLogger(__name__)


class KoryoyaAdapter(BaseAdapter):
    """Adapter for KORYOYA — koryoya.com. Traditional Japanese houses."""

    slug = "koryoya"
    base_url = "https://koryoya.com"

    def __init__(self):
        super().__init__()
        self.delay = 2
        self.client.headers.update({
            "Accept-Language": "en-US,en;q=0.9",
        })

    def get_listing_urls(self) -> list[str]:
        """Find all property URLs from homepage."""
        html = self.fetch_page(self.base_url)
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []

        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if "/properties/" in href and "/index.html" in href:
                full = make_absolute_url(self.base_url, href)
                if full not in urls:
                    urls.append(full)

        logger.info(f"[{self.slug}] Found {len(urls)} listings")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract listing data from a detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed: {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Extract spec table
        specs = self._extract_specs(soup)
        if not specs:
            return None

        # Title & ID
        title_tag = soup.select_one("title")
        title = clean_text(title_tag.get_text().split("|")[0]) if title_tag else None
        listing_id = specs.get("Property No.", "")
        name = specs.get("Property Name", "")
        if name and title:
            title = f"{name} — {title}"
        elif name:
            title = name

        if not title:
            return None

        # Price (in JPY string like "1,800,000 JPY")
        price_raw = specs.get("Price", "")
        price_jpy = None
        if price_raw:
            amount = re.search(r"([\d,]+)", price_raw)
            if amount:
                price_jpy = int(amount.group(1).replace(",", ""))

        # Location → prefecture + city
        location = specs.get("Location", "")
        prefecture, city = self._parse_location(location)

        # Areas
        land_sqm = parse_area_sqm(specs.get("Land Area", ""))
        floor_text = specs.get("Floor Area", "")
        building_sqm = parse_area_sqm(floor_text)

        # Year built
        year_text = specs.get("Year Built", "")
        year_built = None
        m = re.search(r"(\d{4})", year_text)
        if m:
            year_built = int(m.group(1))

        # Layout
        rooms = None
        layout_text = specs.get("Layout", "")
        if layout_text:
            m = re.search(r"\d+[SLDK]+", layout_text)
            rooms = m.group(0) if m else clean_text(layout_text)[:20]

        # Structure
        structure_text = specs.get("Structure", "")
        structure = None
        if "wood" in structure_text.lower():
            structure = "wood"
        elif "steel" in structure_text.lower():
            structure = "steel"
        elif "rc" in structure_text.lower() or "concrete" in structure_text.lower():
            structure = "rc"

        # Transport
        transport = specs.get("Public Transport", "")
        station, distance = self._parse_transport(transport)

        # Images
        images = self._extract_images(soup)

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=listing_id or None,
            title=title,
            description=specs.get("Remarks"),
            price_jpy=price_jpy,
            price_raw=price_raw if price_raw else None,
            prefecture=prefecture,
            city=city,
            address_raw=clean_text(location) if location else None,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            year_built=year_built,
            rooms=rooms,
            nearest_station=station,
            station_distance=distance,
            image_urls=images,
            building_type="detached",
            structure=structure,
        )

    def _extract_specs(self, soup: BeautifulSoup) -> dict[str, str]:
        specs: dict[str, str] = {}
        for table in soup.select("table"):
            for row in table.select("tr"):
                cells = row.select("th, td")
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if key and val and key != val:
                        specs[key] = val
        return specs

    def _parse_location(self, location: str) -> tuple[Optional[str], Optional[str]]:
        if not location:
            return None, None
        # "27-16, Aratani Cho, Fukui City, Fukui Pref."
        prefecture = None
        city = None
        pref_match = re.search(r"(\w+)\s+Pref", location)
        if pref_match:
            prefecture = pref_match.group(1)
        city_match = re.search(r"(\w+)\s+City", location)
        if city_match:
            city = city_match.group(1)
        if not city:
            town_match = re.search(r"(\w+)\s+Town", location)
            if town_match:
                city = town_match.group(1)
        return prefecture, city

    def _parse_transport(self, text: str) -> tuple[Optional[str], Optional[str]]:
        if not text:
            return None, None
        station = None
        distance = None
        st_match = re.search(r"(\w+)\s+Station", text)
        if st_match:
            station = st_match.group(1) + " Station"
        min_match = re.search(r"(\d+)\s*min", text.lower())
        if min_match:
            distance = f"{min_match.group(1)} min"
        return station, distance

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        images: list[str] = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if not src or "logo" in src.lower() or "icon" in src.lower():
                continue
            if src.startswith("data:"):
                continue
            full = make_absolute_url(self.base_url, src)
            if full not in images and "koryoya" in full:
                images.append(full)
        return images[:20]
