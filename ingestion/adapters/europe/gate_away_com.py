"""
Gate-Away.com adapter — English portal for buying property in Italy.
Specifically targets international buyers. Easy to scrape.
Target: houses under €100K across Italy.
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
from ingestion.utils_europe import parse_price_eur, parse_area_sqm_europe

logger = logging.getLogger(__name__)


class GateAwayComAdapter(EuropeBaseAdapter):
    """Adapter for Gate-Away.com — English portal for Italian properties."""

    slug = "gate-away-it"
    country = "italy"
    currency = "EUR"
    default_language = "en"
    base_url = "https://www.gate-away.com"

    # Target regions with cheapest properties
    TARGET_REGIONS = [
        "calabria", "molise", "basilicata", "abruzzo",
        "sicily", "sardinia", "puglia",
    ]

    SEARCH_URL = "https://www.gate-away.com/properties-for-sale-in-italy"

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
        """Collect listing URLs from search results."""
        urls: list[str] = []

        for region in self.TARGET_REGIONS:
            page = 1
            while page <= 10:  # Max 10 pages per region
                search_url = (
                    f"{self.SEARCH_URL}/{region}"
                    f"?price_max=100000&type=house&page={page}"
                )
                try:
                    html = self.fetch_page(search_url)
                except Exception as e:
                    logger.warning(f"[{self.slug}] Search page failed: {e}")
                    break

                soup = BeautifulSoup(html, "lxml")
                cards = soup.select("a.property-card, a.listing-card, a[href*='/property/']")

                if not cards:
                    # Try broader selectors
                    cards = soup.select("a[href*='gate-away.com/property']")

                if not cards:
                    break

                for a in cards:
                    href = a.get("href", "")
                    if "/property/" in href or "/properties/" in href:
                        full = make_absolute_url(self.base_url, href)
                        if full not in urls:
                            urls.append(full)

                # Check for next page
                next_link = soup.select_one("a.next, a[rel='next'], .pagination a:last-child")
                if not next_link:
                    break

                page += 1
                time.sleep(self.delay)

            time.sleep(self.delay)

        logger.info(f"[{self.slug}] Found {len(urls)} listing URLs")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract listing data from a detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed: {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Title
        h1 = soup.select_one("h1")
        title = clean_text(h1.get_text()) if h1 else None
        if not title:
            return None

        # Listing ID from URL
        id_match = re.search(r'/property/(\d+)', url)
        if not id_match:
            id_match = re.search(r'/(\d+)(?:\.html)?$', url)
        listing_id = id_match.group(1) if id_match else url

        # Price
        price_eur = None
        price_raw = None
        price_el = soup.select_one(
            ".price, .property-price, [class*='price'], "
            "[itemprop='price']"
        )
        if price_el:
            price_raw = clean_text(price_el.get_text())
            price_eur = parse_price_eur(price_raw)

        # Convert to JPY for storage
        price_jpy = self.price_to_jpy(price_eur) if price_eur else None

        # Location / Region
        location_el = soup.select_one(
            ".location, .property-location, [class*='location'], "
            "[itemprop='addressRegion']"
        )
        region = clean_text(location_el.get_text()) if location_el else None

        # Area
        building_sqm = None
        land_sqm = None
        for el in soup.select("[class*='area'], [class*='size'], .detail, .feature"):
            text = el.get_text()
            if re.search(r'm²|m2|sqm|mq', text, re.IGNORECASE):
                area = parse_area_sqm_europe(text)
                if area:
                    if "land" in text.lower() or "terrain" in text.lower():
                        land_sqm = area
                    else:
                        building_sqm = area

        # Rooms
        rooms = None
        rooms_el = soup.select_one("[class*='room'], [class*='bedroom']")
        if rooms_el:
            m = re.search(r'(\d+)', rooms_el.get_text())
            if m:
                rooms = m.group(1)

        # Description
        desc_el = soup.select_one(
            ".description, .property-description, "
            "[itemprop='description'], #description"
        )
        description = clean_text(desc_el.get_text()) if desc_el else None

        # Images
        images = self._extract_images(soup)

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=listing_id,
            country=self.country,
            title=title,
            price_jpy=price_jpy,
            price_raw=price_raw,
            prefecture=region,  # Using prefecture field for region
            address_raw=region,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            rooms=rooms,
            description=description,
            image_urls=images,
            building_type="detached",
        )

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        """Extract property images from detail page."""
        images: list[str] = []
        for img in soup.select("img[src], img[data-src], img[data-lazy-src]"):
            src = img.get("data-lazy-src") or img.get("data-src") or img.get("src", "")
            if not src or src.startswith("data:"):
                continue
            if any(
                skip in src.lower()
                for skip in ["logo", "icon", "avatar", "favicon", "placeholder", "pixel", "blank"]
            ):
                continue
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)
        return images[:20]
