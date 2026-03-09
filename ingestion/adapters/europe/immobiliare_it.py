"""
Immobiliare.it adapter — Italy's largest property portal.
HARD to scrape: moderate anti-bot, rate limiting, dynamic loading.
Use with caution. Target: under €80K in southern regions.
"""

from __future__ import annotations

import logging
import random
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.adapters.europe.base_europe import EuropeBaseAdapter
from ingestion.models import RawListing
from ingestion.utils import clean_text, make_absolute_url
from ingestion.utils_europe import parse_price_eur, parse_area_sqm_europe

logger = logging.getLogger(__name__)


class ImmobiliareItAdapter(EuropeBaseAdapter):
    """Adapter for Immobiliare.it — Italy's #1 portal (cautious scraping)."""

    slug = "immobiliare-it"
    country = "italy"
    currency = "EUR"
    default_language = "it"
    base_url = "https://www.immobiliare.it"

    REGIONS_URL_MAP = {
        "calabria": "/vendita-case/calabria/",
        "molise": "/vendita-case/molise/",
        "basilicata": "/vendita-case/basilicata/",
        "abruzzo": "/vendita-case/abruzzo/",
        "sicilia": "/vendita-case/sicilia/",
    }

    MAX_LISTINGS_PER_RUN = 100
    REQUEST_DELAY = (8, 12)  # Random delay range in seconds

    HEADERS = {
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def __init__(self):
        super().__init__()
        self.delay = random.randint(*self.REQUEST_DELAY)
        self.client.headers.update(self.HEADERS)

    def _random_delay(self):
        """Sleep a random amount within the delay range."""
        time.sleep(random.uniform(*self.REQUEST_DELAY))

    def get_listing_urls(self) -> list[str]:
        """Collect listing URLs from search result pages (limited)."""
        urls: list[str] = []

        for region, path in self.REGIONS_URL_MAP.items():
            if len(urls) >= self.MAX_LISTINGS_PER_RUN:
                break

            page = 1
            while page <= 3 and len(urls) < self.MAX_LISTINGS_PER_RUN:
                search_url = (
                    f"{self.base_url}{path}"
                    f"?prezzoMassimo=80000&pag={page}"
                )
                try:
                    html = self.fetch_page(search_url)
                except Exception as e:
                    logger.warning(f"[{self.slug}] {region} page {page} failed: {e}")
                    break

                soup = BeautifulSoup(html, "lxml")

                found_any = False
                for a in soup.select("a[href]"):
                    href = a.get("href", "")
                    if "/annunci/" in href and re.search(r'\d+', href):
                        full = make_absolute_url(self.base_url, href)
                        if full not in urls:
                            urls.append(full)
                            found_any = True

                if not found_any:
                    break

                page += 1
                self._random_delay()

            self._random_delay()

        logger.info(f"[{self.slug}] Found {len(urls)} listing URLs (cap: {self.MAX_LISTINGS_PER_RUN})")
        return urls[:self.MAX_LISTINGS_PER_RUN]

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract from search result card data (avoid hitting detail pages)."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed: {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Title
        h1 = soup.select_one("h1, .im-titleBlock__title")
        title = clean_text(h1.get_text()) if h1 else None
        if not title:
            return None

        # Listing ID
        id_match = re.search(r'/annunci/(\d+)', url)
        listing_id = id_match.group(1) if id_match else url.split("/")[-2]

        # Price
        price_eur = None
        price_raw = None
        price_el = soup.select_one(
            ".im-mainFeatures__title, [class*='price'], "
            "[class*='prezzo']"
        )
        if price_el:
            price_raw = clean_text(price_el.get_text())
            price_eur = parse_price_eur(price_raw)

        price_jpy = self.price_to_jpy(price_eur) if price_eur else None

        # Location
        location_el = soup.select_one(
            ".im-titleBlock__subtitle, [class*='location'], "
            "[class*='indirizzo']"
        )
        region = clean_text(location_el.get_text()) if location_el else None

        # Area & rooms from features
        building_sqm = None
        rooms = None
        for feat in soup.select("[class*='feature'], [class*='caratteristica'], .im-mainFeatures__value"):
            text = feat.get_text()
            area = parse_area_sqm_europe(text)
            if area:
                building_sqm = area
            m = re.search(r'(\d+)\s*(?:local|stanz|room|vani)', text, re.IGNORECASE)
            if m:
                rooms = m.group(1)

        # Description
        desc_el = soup.select_one(
            ".im-description__text, [class*='description'], "
            "[class*='descrizione']"
        )
        description = clean_text(desc_el.get_text()[:2000]) if desc_el else None

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
            prefecture=region,
            address_raw=region,
            building_sqm=building_sqm,
            rooms=rooms,
            description=description,
            image_urls=images,
            building_type="detached",
        )

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        """Extract property images."""
        images: list[str] = []
        for img in soup.select("img[src], img[data-src]"):
            src = img.get("data-src") or img.get("src", "")
            if not src or src.startswith("data:"):
                continue
            if any(
                skip in src.lower()
                for skip in ["logo", "icon", "avatar", "favicon", "placeholder", "pixel"]
            ):
                continue
            if "immobiliare" in src or "pwm.im-cdn" in src:
                full = make_absolute_url(self.base_url, src)
                if full not in images:
                    images.append(full)
        return images[:20]
