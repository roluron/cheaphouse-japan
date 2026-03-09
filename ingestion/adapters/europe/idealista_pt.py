"""
Idealista.pt adapter — Portugal's biggest property portal.
HAS AN OFFICIAL API: https://developers.idealista.com/
Can fall back to scraping. Target: houses under €80K in interior Portugal.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.adapters.europe.base_europe import EuropeBaseAdapter
from ingestion.models import RawListing
from ingestion.utils import clean_text, make_absolute_url
from ingestion.utils_europe import parse_price_eur, parse_area_sqm_europe

logger = logging.getLogger(__name__)


class IdealistaPtAdapter(EuropeBaseAdapter):
    """Adapter for Idealista.pt — Portugal's biggest property portal."""

    slug = "idealista-pt"
    country = "portugal"
    currency = "EUR"
    default_language = "pt"
    base_url = "https://www.idealista.pt"

    # Cheapest districts in Portugal
    TARGET_DISTRICTS = [
        "braganca", "guarda", "castelo-branco",
        "portalegre", "beja", "evora",
    ]

    FALLBACK_SCRAPE_DELAY = (5, 10)

    HEADERS = {
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
    }

    def __init__(self):
        super().__init__()
        self.delay = 6
        self.client.headers.update(self.HEADERS)
        # Check for API credentials
        self.api_key = os.environ.get("IDEALISTA_API_KEY", "")
        self.api_secret = os.environ.get("IDEALISTA_API_SECRET", "")
        self.use_api = bool(self.api_key and self.api_secret)
        if self.use_api:
            logger.info(f"[{self.slug}] Using Idealista API")
        else:
            logger.info(f"[{self.slug}] No API keys — falling back to scraping")

    def get_listing_urls(self) -> list[str]:
        """Collect listing URLs via scraping (API would return data directly)."""
        urls: list[str] = []

        for district in self.TARGET_DISTRICTS:
            page = 1
            while page <= 5:
                search_url = (
                    f"{self.base_url}/comprar/moradia/{district}/"
                    f"?maxPrice=80000&order=date&pagina={page}"
                )
                try:
                    html = self.fetch_page(search_url)
                except Exception as e:
                    logger.warning(f"[{self.slug}] {district} page {page} failed: {e}")
                    break

                soup = BeautifulSoup(html, "lxml")

                found_any = False
                for a in soup.select("a[href]"):
                    href = a.get("href", "")
                    if "/imovel/" in href:
                        full = make_absolute_url(self.base_url, href)
                        if full not in urls:
                            urls.append(full)
                            found_any = True

                if not found_any:
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
        h1 = soup.select_one("h1, .main-info__title")
        title = clean_text(h1.get_text()) if h1 else None
        if not title:
            return None

        # Listing ID
        id_match = re.search(r'/imovel/(\d+)', url)
        listing_id = id_match.group(1) if id_match else url.split("/")[-2]

        # Price
        price_eur = None
        price_raw = None
        price_el = soup.select_one(
            ".info-data-price, [class*='price'], [class*='preco']"
        )
        if price_el:
            price_raw = clean_text(price_el.get_text())
            price_eur = parse_price_eur(price_raw)

        price_jpy = self.price_to_jpy(price_eur) if price_eur else None

        # Location
        location_el = soup.select_one(
            ".main-info__title-minor, [class*='location']"
        )
        region = clean_text(location_el.get_text()) if location_el else None

        # Area
        building_sqm = None
        for el in soup.select("[class*='detail'], [class*='feature']"):
            text = el.get_text()
            area = parse_area_sqm_europe(text)
            if area:
                building_sqm = area
                break

        # Rooms
        rooms = None
        text = soup.get_text()
        m = re.search(r'(\d+)\s*(?:quarto|assoalhada|room|T\d)', text, re.IGNORECASE)
        if m:
            rooms = m.group(1)
        # Also check T-notation: T2, T3, etc.
        t_match = re.search(r'\bT(\d)\b', text)
        if t_match:
            rooms = t_match.group(1)

        # Description
        desc_el = soup.select_one(
            ".comment, [class*='description'], [class*='descricao']"
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
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)
        return images[:20]
