"""
homes.co.nz — NZ property data platform with valuations.
Unique: provides estimated values, sales history, and suburb stats.
Good for enrichment data even if listings overlap with Trade Me.

Strategy:
  1. Use suburb/region pages for bulk discovery
  2. Filter by estimated value < NZD 300K
  3. Extract: address, estimate, beds/baths, land area, last sold price
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.adapters.nz.base_nz import NZBaseAdapter
from ingestion.models import RawListing
from ingestion.utils import clean_text, make_absolute_url
from ingestion.utils_nz import parse_price_nzd, parse_area_sqm_nz, parse_land_area_nz, nzd_to_jpy

logger = logging.getLogger(__name__)


class HomesCoNZAdapter(NZBaseAdapter):
    """Adapter for homes.co.nz — property data + valuations."""

    slug = "homes-co-nz"
    base_url = "https://homes.co.nz"

    # Regions with affordable properties
    SEARCH_REGIONS = [
        "west-coast", "southland", "gore", "invercargill",
        "greymouth", "whanganui", "kawerau",
        "opotiki", "tararua", "wairoa",
    ]

    def __init__(self):
        super().__init__()
        self.delay = 4
        self.client.headers.update({
            "Accept-Language": "en-NZ,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def get_listing_urls(self) -> list[str]:
        """Find property URLs from regional search pages."""
        urls: list[str] = []

        for region in self.SEARCH_REGIONS:
            for page in range(1, 4):
                try:
                    search_url = (
                        f"{self.base_url}/s/{region}"
                        f"?price_max={self.PRICE_THRESHOLD}"
                        f"&sort=price-asc"
                        f"&page={page}"
                    )

                    html = self.fetch_page(search_url)
                    soup = BeautifulSoup(html, "lxml")

                    # Try finding property links
                    found = 0
                    for a in soup.select("a[href]"):
                        href = a.get("href", "")
                        # homes.co.nz property URLs: /address/123-main-street-greymouth
                        if re.search(r'/address/[\w-]+', href) and "/s/" not in href:
                            full = make_absolute_url(self.base_url, href)
                            if full not in urls:
                                urls.append(full)
                                found += 1

                    if found == 0:
                        break

                    time.sleep(self.delay)

                except Exception as e:
                    logger.warning(f"[{self.slug}] Error {region} p{page}: {e}")
                    break

        logger.info(f"[{self.slug}] Total: {len(urls)} property URLs")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract property data from a homes.co.nz property page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Try __NEXT_DATA__ or JSON in page
        next_listing = self._extract_from_json(html, url)
        if next_listing:
            return next_listing

        # Fallback HTML
        return self._parse_html(soup, url)

    def _extract_from_json(self, html: str, url: str) -> Optional[RawListing]:
        """Try extracting from embedded JSON data."""
        match = re.search(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>',
            html, re.DOTALL
        )
        if not match:
            return None

        try:
            data = json.loads(match.group(1))
            prop = (
                data.get("props", {})
                .get("pageProps", {})
                .get("property")
            )
            if not prop:
                return None

            address = prop.get("address") or prop.get("displayAddress", "")
            title = address or "Property"

            # homes.co.nz shows estimates, not asking prices
            estimate = prop.get("estimatedValue") or prop.get("estimate")
            price_raw = f"Estimated: NZ${estimate:,}" if estimate else None
            price_nzd = estimate if isinstance(estimate, int) else parse_price_nzd(str(estimate)) if estimate else None

            # Skip if above threshold
            if price_nzd and price_nzd > self.PRICE_THRESHOLD:
                return None

            region = prop.get("region") or prop.get("district", "")
            suburb = prop.get("suburb", "")

            beds = prop.get("bedrooms")
            baths = prop.get("bathrooms")
            rooms = None
            if beds or baths:
                parts = []
                if beds:
                    parts.append(f"{beds}bed")
                if baths:
                    parts.append(f"{baths}bath")
                rooms = " / ".join(parts)

            land_area = prop.get("landArea")
            floor_area = prop.get("floorArea")

            images = []
            for img in prop.get("photos", []) or prop.get("images", []):
                if isinstance(img, str):
                    images.append(img)
                elif isinstance(img, dict):
                    images.append(img.get("url", ""))

            return RawListing(
                source_slug=self.slug,
                source_url=url,
                source_listing_id=str(prop.get("id", "")),
                title=clean_text(title),
                description=clean_text(prop.get("description")),
                price_raw=price_raw,
                price_jpy=nzd_to_jpy(price_nzd) if price_nzd else None,
                prefecture=clean_text(region) if region else None,
                city=clean_text(suburb) if suburb else None,
                address_raw=clean_text(address) if address else None,
                land_sqm=float(land_area) if land_area else None,
                building_sqm=float(floor_area) if floor_area else None,
                rooms=rooms,
                image_urls=[i for i in images if i][:20],
                building_type="detached",
                raw_data={"country": self.country, "currency": self.currency,
                          "price_nzd": price_nzd, "data_type": "valuation"},
            )

        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.warning(f"[{self.slug}] JSON parse error: {e}")
            return None

    def _parse_html(self, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        """Fallback HTML parsing."""
        title_el = soup.select_one("h1") or soup.select_one("title")
        title = clean_text(title_el.get_text()) if title_el else None
        if not title:
            return None

        # Estimate / price
        price_el = (
            soup.select_one("[class*='estimate']")
            or soup.select_one("[class*='value']")
            or soup.select_one("[class*='price']")
        )
        price_raw = clean_text(price_el.get_text()) if price_el else None
        price_nzd = parse_price_nzd(price_raw) if price_raw else None

        if price_nzd and price_nzd > self.PRICE_THRESHOLD:
            return None

        # Images
        images = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if src and not src.startswith("data:") and "logo" not in src.lower():
                full = make_absolute_url(self.base_url, src)
                if full not in images:
                    images.append(full)

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            title=title,
            price_raw=price_raw,
            price_jpy=nzd_to_jpy(price_nzd) if price_nzd else None,
            image_urls=images[:20],
            building_type="detached",
            raw_data={"country": self.country, "currency": self.currency,
                      "price_nzd": price_nzd, "data_type": "valuation"},
        )
