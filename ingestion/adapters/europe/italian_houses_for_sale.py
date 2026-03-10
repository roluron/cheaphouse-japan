"""
ItalianHousesForSale.com adapter — curated cheap Italian property listings.
Easy to scrape, English-language, focuses on affordable rural homes.
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


class ItalianHousesForSaleAdapter(EuropeBaseAdapter):
    """Adapter for ItalianHousesForSale.com — curated cheap Italian houses."""

    slug = "italian-houses"
    country = "italy"
    currency = "EUR"
    default_language = "en"
    base_url = "https://www.italianhousesforsale.com"

    # Regional listing pages — actual URL pattern: /property/region
    REGION_URLS = [
        "/property/calabria",
        "/property/molise",
        "/property/basilicata",
        "/property/abruzzo",
        "/property/sicily",
        "/property/sardinia",
        "/property/apulia",
        "/property/tuscany",
        "/property/lazio",
        "/property/liguria",
        "/property/campania",
        "/property/umbria",
        "/property/le-marche",
        "/property/piedmont",
        "/property/emilia-romagna",
    ]

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
        """Collect listing URLs from regional listing pages."""
        urls: list[str] = []

        for region_path in self.REGION_URLS:
            region_url = self.base_url + region_path
            try:
                html = self.fetch_page(region_url)
            except Exception as e:
                logger.warning(f"[{self.slug}] Region page failed: {e}")
                continue

            soup = BeautifulSoup(html, "lxml")

            # Find property listing links
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                # Property detail pages typically have a pattern like /property-name-12345/
                if self._looks_like_listing_url(href, region_path):
                    full = make_absolute_url(self.base_url, href)
                    if full not in urls:
                        urls.append(full)

            time.sleep(self.delay)

        logger.info(f"[{self.slug}] Found {len(urls)} listing URLs")
        return urls

    def _looks_like_listing_url(self, href: str, region_path: str) -> bool:
        """Check if a URL looks like a property listing."""
        if not href:
            return False
        # Skip navigation, category, and non-listing pages
        skip_patterns = [
            "/category/", "/tag/", "/about", "/contact",
            "/privacy", "/terms", "/wp-", "/#", "/page/",
            "javascript:", "mailto:", "tel:", "/property-for-sale",
        ]
        for p in skip_patterns:
            if p in href.lower():
                return False

        # Must contain italianhousesforsale.com or be relative
        if "italianhousesforsale.com" in href or href.startswith("/"):
            # Match detail page URLs: /property/region/listing-slug
            region_name = region_path.strip("/").split("/")[-1]
            if f"/{region_name}/" in href and href.count("/") >= 3:
                return True
            # Or has /property/ path with enough depth
            if "/property/" in href and href.count("/") >= 4:
                return True
            # Property pages often have longer slugs with hyphens
            if re.search(r'/[\w]+-[\w]+-[\w]+', href):
                return True

        return False

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract listing data from a detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed: {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Title
        h1 = soup.select_one("h1.entry-title, h1")
        title = clean_text(h1.get_text()) if h1 else None
        if not title:
            return None

        # Listing ID from URL
        listing_id = url.rstrip("/").split("/")[-1]

        # Price
        price_eur = None
        price_raw = None
        price_el = soup.select_one(".price, [class*='price']")
        if not price_el:
            # Search in text content for price patterns
            text = soup.get_text()
            price_match = re.search(r'€\s*([\d,.\s]+)', text)
            if price_match:
                price_raw = f"€{price_match.group(1).strip()}"
                price_eur = parse_price_eur(price_raw)
        else:
            price_raw = clean_text(price_el.get_text())
            price_eur = parse_price_eur(price_raw)

        price_jpy = self.price_to_jpy(price_eur) if price_eur else None

        # Region from URL path
        region = None
        for rp in self.REGION_URLS:
            region_name = rp.strip("/")
            if region_name in url.lower():
                region = region_name.title()
                break

        # Area
        building_sqm = None
        text = soup.get_text()
        area_match = re.search(r'(\d+[\.,]?\d*)\s*(?:m²|m2|mq|sqm)', text, re.IGNORECASE)
        if area_match:
            building_sqm = float(area_match.group(1).replace(',', '.'))

        # Description
        desc_el = soup.select_one(".entry-content, .property-description, article .content")
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
                for skip in ["logo", "icon", "avatar", "favicon", "placeholder"]
            ):
                continue
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)
        return images[:20]
