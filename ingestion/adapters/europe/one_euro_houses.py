"""
1EuroHouses.com adapter — catalog of Italian municipalities offering 1-euro houses.
These are renovation projects with conditions (residency, renovation timeline).
Good for the "adventure buyer" segment.

NOTE: This site lists municipalities/programs, not individual properties.
Each listing represents a 1€ house program in a specific town.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.adapters.europe.base_europe import EuropeBaseAdapter
from ingestion.models import RawListing
from ingestion.utils import clean_text, make_absolute_url
from ingestion.utils_europe import parse_area_sqm_europe

logger = logging.getLogger(__name__)


class OneEuroHousesAdapter(EuropeBaseAdapter):
    """Adapter for 1EuroHouses.com — 1€ house program catalog."""

    slug = "1euro-houses"
    country = "italy"
    currency = "EUR"
    default_language = "en"
    base_url = "https://1eurohouses.com"

    HEADERS = {
        "Accept-Language": "en-GB,en;q=0.9",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
    }

    def __init__(self):
        super().__init__()
        self.delay = 2
        self.client.headers.update(self.HEADERS)

    def get_listing_urls(self) -> list[str]:
        """Collect municipality/program pages."""
        urls: list[str] = []

        # Try main listings page and town pages
        for start_url in [
            f"{self.base_url}/towns/",
            f"{self.base_url}/1-euro-houses/",
            self.base_url,
        ]:
            try:
                html = self.fetch_page(start_url)
            except Exception as e:
                logger.warning(f"[{self.slug}] Page failed: {e}")
                continue

            soup = BeautifulSoup(html, "lxml")

            for a in soup.select("a[href]"):
                href = a.get("href", "")
                # Look for town/municipality pages
                if self._is_town_page(href):
                    full = make_absolute_url(self.base_url, href)
                    if full not in urls:
                        urls.append(full)

            time.sleep(self.delay)

        logger.info(f"[{self.slug}] Found {len(urls)} town/program URLs")
        return urls

    def _is_town_page(self, href: str) -> bool:
        """Check if URL is a town program page."""
        if not href:
            return False
        skip = [
            "/about", "/contact", "/privacy", "/terms",
            "/wp-", "/#", "javascript:", "mailto:",
            "/category/", "/tag/",
        ]
        for s in skip:
            if s in href.lower():
                return False

        # Town pages typically have slugs after the base domain
        if re.search(r'1eurohouses\.com/[a-z][\w-]+/?$', href):
            return True
        if "/towns/" in href:
            return True
        return False

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract municipality/program info from a page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed: {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Title (town name)
        h1 = soup.select_one("h1.entry-title, h1")
        title = clean_text(h1.get_text()) if h1 else None
        if not title:
            return None

        # Listing ID from URL slug
        listing_id = url.rstrip("/").split("/")[-1]

        # These are 1€ houses — price is always €1
        price_raw = "€1 (1 Euro House Program)"
        price_jpy = 162  # 1 EUR ≈ 162 JPY

        # Try to find region info
        text = soup.get_text()
        region = None
        italian_regions = [
            "Calabria", "Sicily", "Sardinia", "Molise", "Basilicata",
            "Abruzzo", "Puglia", "Campania", "Lazio", "Tuscany",
            "Liguria", "Piedmont", "Lombardy", "Veneto",
        ]
        for r in italian_regions:
            if r.lower() in text.lower():
                region = r
                break

        # Description (article content)
        desc_el = soup.select_one(
            ".entry-content, article .content, .post-content, article"
        )
        description = None
        if desc_el:
            desc_text = clean_text(desc_el.get_text()[:2000])
            description = desc_text

        # Images
        images = self._extract_images(soup)

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=listing_id,
            country=self.country,
            title=f"1€ House Program — {title}",
            price_jpy=price_jpy,
            price_raw=price_raw,
            prefecture=region,
            address_raw=title,  # Town name as address
            description=description,
            image_urls=images,
            building_type="detached",
            condition_notes="1 Euro House Program — requires renovation commitment",
        )

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        """Extract images."""
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
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)
        return images[:15]
