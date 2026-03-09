"""
Heritage Homes Japan (heritagehomesjapan.com) adapter.
Scrapes renovated machiya and kominka from Kyoto-based specialists.

Heritage Homes Japan curates traditional Japanese properties:
- Kyomachiya (京町家) — Kyoto townhouses
- Kominka (古民家) — rural traditional houses
- Guesthouses — renovated for hospitality

Small curated inventory, all in English, WordPress site.
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


class HeritageHomesAdapter(BaseAdapter):
    """Adapter for Heritage Homes Japan — heritagehomesjapan.com."""

    slug = "heritage-homes"
    base_url = "https://heritagehomesjapan.com"

    # Category listing pages
    CATEGORY_URLS = [
        "https://heritagehomesjapan.com/listings/kyomachiya/",
        "https://heritagehomesjapan.com/listings/kominka/",
        "https://heritagehomesjapan.com/listings/guesthouses/",
    ]

    def __init__(self):
        super().__init__()
        self.delay = 3
        self.client.headers.update({
            "Accept-Language": "en-US,en;q=0.9",
        })

    def get_listing_urls(self) -> list[str]:
        """Collect listing URLs from all category pages."""
        urls: list[str] = []

        for cat_url in self.CATEGORY_URLS:
            try:
                html = self.fetch_page(cat_url)
            except Exception as e:
                logger.warning(f"[{self.slug}] Category failed: {e}")
                continue

            soup = BeautifulSoup(html, "lxml")
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                if "/for-sale/" in href:
                    full = make_absolute_url(self.base_url, href)
                    if full not in urls:
                        urls.append(full)

        # Skip land-only listings
        urls = [u for u in urls if "niseko-land" not in u.lower()]

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
        text = soup.get_text(separator="\n", strip=True)

        # Title
        h1 = soup.select_one("h1.entry-title, h1.entry-prop, h1")
        title = clean_text(h1.get_text()) if h1 else None
        if not title:
            return None

        # Listing ID from URL slug
        slug_match = re.search(r"/for-sale/([^/]+)", url)
        listing_id = slug_match.group(1) if slug_match else None

        # Price — from .price_area or text
        price_jpy = None
        price_raw = None
        price_el = soup.select_one(".price_area")
        if price_el:
            price_raw = clean_text(price_el.get_text())
        if not price_raw:
            # Fallback: look in text
            price_match = re.search(r"¥\s*([\d,.]+)\s*M", text)
            if price_match:
                price_raw = f"¥{price_match.group(1)}M"

        if price_raw:
            # Parse "¥ 150M" or "¥ 61.9M" → JPY
            m = re.search(r"([\d,.]+)\s*M", price_raw)
            if m:
                amount = float(m.group(1).replace(",", ""))
                price_jpy = int(amount * 1_000_000)

        # Areas from text
        building_sqm = None
        land_sqm = None
        for line in text.split("\n"):
            if "total floor area" in line.lower() or "Total floor area" in line:
                area_m = re.search(r"([\d,.]+)\s*m²", line)
                if area_m:
                    building_sqm = float(area_m.group(1).replace(",", ""))
            if "land area" in line.lower() and "m²" in line:
                area_m = re.search(r"([\d,.]+)\s*m²", line)
                if area_m:
                    land_sqm = float(area_m.group(1).replace(",", ""))

        # Year of construction
        year_built = None
        year_match = re.search(r"(?:Year of construction|Built)[:\s]*(\d{4})", text, re.IGNORECASE)
        if year_match:
            year_built = int(year_match.group(1))
        if not year_built:
            # Look for year patterns in text
            for line in text.split("\n"):
                if "year" in line.lower() and "construction" in line.lower():
                    m = re.search(r"(\d{4})", line)
                    if m:
                        y = int(m.group(1))
                        if 1800 <= y <= 2030:
                            year_built = y
                            break

        # Prefecture — most properties are Kyoto or nearby
        prefecture = self._detect_prefecture(text, url)

        # Images
        images = self._extract_images(soup)

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=listing_id,
            title=title,
            price_jpy=price_jpy,
            price_raw=price_raw,
            prefecture=prefecture,
            address_raw=None,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            year_built=year_built,
            image_urls=images,
            building_type="detached",
            structure="wood",  # All heritage homes are traditional wood
        )

    def _detect_prefecture(self, text: str, url: str) -> Optional[str]:
        """Detect prefecture from text or URL context."""
        text_lower = text.lower()
        pref_keywords = {
            "kyoto": "Kyoto",
            "osaka": "Osaka",
            "nara": "Nara",
            "hyogo": "Hyogo",
            "shiga": "Shiga",
            "gifu": "Gifu",
            "takayama": "Gifu",
            "miyama": "Kyoto",
            "niseko": "Hokkaido",
        }
        for keyword, pref in pref_keywords.items():
            if keyword in text_lower or keyword in url.lower():
                return pref
        # Default — most Heritage Homes listings are in Kyoto
        return "Kyoto"

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        images: list[str] = []
        for img in soup.select("img[src], img[data-src]"):
            src = img.get("data-src") or img.get("src", "")
            if not src or src.startswith("data:"):
                continue
            if any(
                skip in src.lower()
                for skip in ["logo", "icon", "avatar", "favicon", "placeholder"]
            ):
                continue
            # Only property images (usually uploaded to WordPress)
            if "wp-content/uploads" in src or "heritagehomes" in src:
                full = make_absolute_url(self.base_url, src)
                if full not in images:
                    images.append(full)
        return images[:20]
