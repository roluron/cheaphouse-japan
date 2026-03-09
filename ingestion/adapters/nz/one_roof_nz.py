"""
OneRoof.co.nz — NZ Herald's property platform.
Search with price + property type filters, parse detail pages.
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


class OneRoofNZAdapter(NZBaseAdapter):
    """Adapter for OneRoof.co.nz — NZ Herald property platform."""

    slug = "oneroof-nz"
    base_url = "https://www.oneroof.co.nz"

    SEARCH_REGIONS = [
        "west-coast", "southland", "otago",
        "whanganui", "manawatu", "taranaki",
        "gisborne", "bay-of-plenty",
    ]

    def __init__(self):
        super().__init__()
        self.delay = 4
        self.client.headers.update({
            "Accept-Language": "en-NZ,en;q=0.9",
        })

    def get_listing_urls(self) -> list[str]:
        urls: list[str] = []
        for region in self.SEARCH_REGIONS:
            for page in range(1, 5):
                try:
                    search_url = (
                        f"{self.base_url}/search"
                        f"?price_max={self.PRICE_THRESHOLD}"
                        f"&region={region}&property_type=house&page={page}"
                    )
                    html = self.fetch_page(search_url)
                    soup = BeautifulSoup(html, "lxml")
                    found = 0
                    for a in soup.select("a[href]"):
                        href = a.get("href", "")
                        if re.search(r'/property/[\w-]+/\d+', href) or "/listing/" in href:
                            full = make_absolute_url(self.base_url, href.split("?")[0])
                            if full not in urls:
                                urls.append(full)
                                found += 1
                    if found == 0:
                        break
                    time.sleep(self.delay)
                except Exception as e:
                    logger.warning(f"[{self.slug}] Error {region} p{page}: {e}")
                    break
        logger.info(f"[{self.slug}] Total: {len(urls)} listing URLs")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Try __NEXT_DATA__
        match = re.search(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>',
            html, re.DOTALL,
        )
        if match:
            result = self._parse_next_data(match.group(1), url)
            if result:
                return result

        return self._parse_html(soup, url)

    def _parse_next_data(self, raw_json: str, url: str) -> Optional[RawListing]:
        try:
            data = json.loads(raw_json)
            listing = data.get("props", {}).get("pageProps", {}).get("listing") or \
                      data.get("props", {}).get("pageProps", {}).get("property")
            if not listing:
                return None

            title = listing.get("title") or listing.get("address", "")
            if not title:
                return None

            price_raw = listing.get("priceDisplay") or listing.get("price", "")
            price_nzd = parse_price_nzd(price_raw)
            region = listing.get("region") or listing.get("district", "")
            beds = listing.get("bedrooms")
            baths = listing.get("bathrooms")
            rooms = " / ".join(
                ([f"{beds}bed"] if beds else []) + ([f"{baths}bath"] if baths else [])
            ) or None

            images = []
            for img in listing.get("images", []) or []:
                if isinstance(img, str):
                    images.append(img)
                elif isinstance(img, dict):
                    images.append(img.get("url") or img.get("fullSize", ""))

            return RawListing(
                source_slug=self.slug, source_url=url,
                source_listing_id=str(listing.get("id", "")),
                title=clean_text(title),
                description=clean_text(listing.get("description")),
                price_raw=price_raw or None,
                price_jpy=nzd_to_jpy(price_nzd) if price_nzd else None,
                prefecture=clean_text(region) if region else None,
                city=clean_text(listing.get("suburb")),
                address_raw=clean_text(listing.get("address")),
                land_sqm=parse_land_area_nz(str(listing.get("landArea", ""))),
                building_sqm=parse_area_sqm_nz(str(listing.get("floorArea", ""))),
                rooms=rooms, image_urls=[i for i in images if i][:20],
                building_type="detached",
                raw_data={"country": self.country, "currency": self.currency, "price_nzd": price_nzd},
            )
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"[{self.slug}] JSON parse error: {e}")
            return None

    def _parse_html(self, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        title_el = soup.select_one("h1") or soup.select_one("title")
        title = clean_text(title_el.get_text()) if title_el else None
        if not title:
            return None

        price_el = soup.select_one("[class*='price']")
        price_raw = clean_text(price_el.get_text()) if price_el else None
        price_nzd = parse_price_nzd(price_raw) if price_raw else None

        desc_el = soup.select_one("[class*='description']")
        description = clean_text(desc_el.get_text()) if desc_el else None

        images = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if src and not src.startswith("data:") and "logo" not in src.lower():
                full = make_absolute_url(self.base_url, src)
                if full not in images:
                    images.append(full)

        listing_id = None
        id_match = re.search(r'/(\d+)/?$', url)
        if id_match:
            listing_id = id_match.group(1)

        return RawListing(
            source_slug=self.slug, source_url=url, source_listing_id=listing_id,
            title=title, description=description, price_raw=price_raw,
            price_jpy=nzd_to_jpy(price_nzd) if price_nzd else None,
            image_urls=images[:20], building_type="detached",
            raw_data={"country": self.country, "currency": self.currency, "price_nzd": price_nzd},
        )
