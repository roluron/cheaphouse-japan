"""
Harcourts — NZ's largest real estate agency.
Direct agency listings, sometimes exclusive. Simpler HTML.
Especially good for South Island rural properties.
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


class HarcourtsNZAdapter(NZBaseAdapter):
    """Adapter for Harcourts — harcourts.co.nz."""

    slug = "harcourts-nz"
    base_url = "https://harcourts.co.nz"

    SEARCH_REGIONS = [
        "west-coast", "southland", "otago",
        "canterbury", "whanganui", "manawatu",
        "taranaki", "gisborne",
    ]

    def __init__(self):
        super().__init__()
        self.delay = 3
        self.client.headers.update({
            "Accept-Language": "en-NZ,en;q=0.9",
        })

    def get_listing_urls(self) -> list[str]:
        urls: list[str] = []
        for region in self.SEARCH_REGIONS:
            for page in range(1, 4):
                try:
                    search_url = (
                        f"{self.base_url}/properties"
                        f"?price_to={self.PRICE_THRESHOLD}"
                        f"&property_type=residential"
                        f"&region={region}&page={page}"
                    )
                    html = self.fetch_page(search_url)
                    soup = BeautifulSoup(html, "lxml")

                    found = 0
                    for a in soup.select("a[href]"):
                        href = a.get("href", "")
                        if "/properties/" in href and href != "/properties/":
                            if re.search(r'/properties/[\w-]+', href):
                                full = make_absolute_url(self.base_url, href.split("?")[0])
                                if full not in urls and "search" not in full:
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

        # Try JSON-LD
        for script in soup.select('script[type="application/ld+json"]'):
            if script.string:
                try:
                    ld = json.loads(script.string)
                    if isinstance(ld, dict) and "RealEstate" in str(ld.get("@type", "")):
                        result = self._parse_json_ld(ld, soup, url)
                        if result:
                            return result
                except json.JSONDecodeError:
                    pass

        return self._parse_html(soup, url)

    def _parse_json_ld(self, ld: dict, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        title = ld.get("name", "")
        if not title:
            return None

        price_raw = str(ld.get("offers", {}).get("price", ""))
        price_nzd = parse_price_nzd(price_raw) if price_raw else None
        address = ld.get("address", {})
        if isinstance(address, dict):
            addr_text = f"{address.get('streetAddress', '')}, {address.get('addressLocality', '')}"
            region = address.get("addressRegion", "")
        else:
            addr_text = str(address)
            region = ""

        images = []
        img_data = ld.get("image", [])
        if isinstance(img_data, list):
            images = [i for i in img_data if isinstance(i, str)][:20]
        elif isinstance(img_data, str):
            images = [img_data]

        return RawListing(
            source_slug=self.slug, source_url=url,
            title=clean_text(title),
            price_raw=price_raw or None,
            price_jpy=nzd_to_jpy(price_nzd) if price_nzd else None,
            prefecture=clean_text(region) if region else None,
            address_raw=clean_text(addr_text),
            image_urls=images,
            building_type="detached",
            raw_data={"country": self.country, "currency": self.currency, "price_nzd": price_nzd},
        )

    def _parse_html(self, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        title_el = soup.select_one("h1") or soup.select_one("title")
        title = clean_text(title_el.get_text()) if title_el else None
        if not title:
            return None

        price_el = soup.select_one("[class*='price']") or soup.select_one("[class*='Price']")
        price_raw = clean_text(price_el.get_text()) if price_el else None
        price_nzd = parse_price_nzd(price_raw) if price_raw else None

        addr_el = soup.select_one("[class*='address']")
        address = clean_text(addr_el.get_text()) if addr_el else None

        desc_el = soup.select_one("[class*='description']")
        description = clean_text(desc_el.get_text()) if desc_el else None

        # Beds/baths from icons or text
        rooms = self._extract_rooms_html(soup)

        images = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if src and not src.startswith("data:") and "logo" not in src.lower():
                full = make_absolute_url(self.base_url, src)
                if full not in images:
                    images.append(full)

        return RawListing(
            source_slug=self.slug, source_url=url,
            title=title, description=description,
            price_raw=price_raw,
            price_jpy=nzd_to_jpy(price_nzd) if price_nzd else None,
            address_raw=address, rooms=rooms,
            image_urls=images[:20], building_type="detached",
            raw_data={"country": self.country, "currency": self.currency, "price_nzd": price_nzd},
        )

    def _extract_rooms_html(self, soup: BeautifulSoup) -> Optional[str]:
        parts = []
        for el in soup.select("[class*='bed'], [class*='bath']"):
            text = clean_text(el.get_text())
            if text and re.search(r'\d', text):
                parts.append(text)
        return " / ".join(parts)[:30] if parts else None
