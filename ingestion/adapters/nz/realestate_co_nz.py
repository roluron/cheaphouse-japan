"""
realestate.co.nz — NZ's second-largest property portal.
Run by the Real Estate Institute of NZ. Quality listings.

Strategy:
  1. Search by region with price filter
  2. Look for __NEXT_DATA__ or JSON in page source
  3. Parse listing cards, follow detail pages
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


class RealEstateCoNZAdapter(NZBaseAdapter):
    """Adapter for realestate.co.nz — NZ's #2 property portal."""

    slug = "realestate-co-nz"
    base_url = "https://www.realestate.co.nz"

    REGIONS = [
        "west-coast", "southland", "otago",
        "whanganui", "manawatu", "taranaki",
        "hawkes-bay", "gisborne", "bay-of-plenty",
    ]

    def __init__(self):
        super().__init__()
        self.delay = 4
        self.client.headers.update({
            "Accept-Language": "en-NZ,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def get_listing_urls(self) -> list[str]:
        """Scrape listing URLs from search pages."""
        urls: list[str] = []

        for region in self.REGIONS:
            for page in range(1, 6):  # Up to 5 pages per region
                try:
                    search_url = (
                        f"{self.base_url}/residential/sale/{region}"
                        f"?maxPrice={self.PRICE_THRESHOLD}"
                        f"&page={page}"
                    )

                    html = self.fetch_page(search_url)

                    # Try __NEXT_DATA__ first
                    next_urls = self._extract_urls_from_next_data(html)
                    if next_urls:
                        new_count = 0
                        for u in next_urls:
                            if u not in urls:
                                urls.append(u)
                                new_count += 1
                        if new_count == 0:
                            break
                        time.sleep(self.delay)
                        continue

                    # Fallback: parse HTML
                    soup = BeautifulSoup(html, "lxml")
                    found = 0
                    for a in soup.select("a[href]"):
                        href = a.get("href", "")
                        # Match /43002611/residential/sale/... or /residential/sale/.../digits
                        if re.search(r'/\d{5,}/', href) or re.search(r'/residential/sale/[\w-]+/[\w-]+/\d+', href):
                            full = make_absolute_url(self.base_url, href)
                            if full not in urls:
                                urls.append(full)
                                found += 1

                    if found == 0:
                        break  # No more results

                    time.sleep(self.delay)

                except Exception as e:
                    logger.warning(f"[{self.slug}] Error {region} p{page}: {e}")
                    break

            logger.info(f"[{self.slug}] {region}: running total {len(urls)} URLs")

        logger.info(f"[{self.slug}] Total: {len(urls)} listing URLs")
        return urls

    def _extract_urls_from_next_data(self, html: str) -> list[str]:
        """Extract listing URLs from __NEXT_DATA__ JSON."""
        match = re.search(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>',
            html, re.DOTALL
        )
        if not match:
            return []

        try:
            data = json.loads(match.group(1))
            listings = (
                data.get("props", {})
                .get("pageProps", {})
                .get("searchResults", {})
                .get("listings", [])
            )
            urls = []
            for item in listings:
                listing_url = item.get("url") or item.get("listingUrl", "")
                if listing_url:
                    urls.append(make_absolute_url(self.base_url, listing_url))
            return urls
        except (json.JSONDecodeError, AttributeError):
            return []

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract listing details from a detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Try JSON-LD
        json_listing = self._extract_json_ld(soup)
        if json_listing:
            return json_listing

        # Try __NEXT_DATA__
        next_listing = self._extract_from_next_data(html, url)
        if next_listing:
            return next_listing

        # Fallback: HTML parsing
        return self._parse_html_listing(soup, url)

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[RawListing]:
        """Try extracting from JSON-LD."""
        for script in soup.select('script[type="application/ld+json"]'):
            if not script.string:
                continue
            try:
                ld = json.loads(script.string)
                if isinstance(ld, dict) and "RealEstate" in str(ld.get("@type", "")):
                    # Parse JSON-LD real estate listing
                    return None  # Usually too sparse to be useful
            except json.JSONDecodeError:
                pass
        return None

    def _extract_from_next_data(self, html: str, url: str) -> Optional[RawListing]:
        """Extract listing from __NEXT_DATA__."""
        match = re.search(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>',
            html, re.DOTALL
        )
        if not match:
            return None

        try:
            data = json.loads(match.group(1))
            listing = (
                data.get("props", {})
                .get("pageProps", {})
                .get("listing")
            )
            if not listing:
                return None

            title = listing.get("title") or listing.get("address", "")
            if not title:
                return None

            price_raw = listing.get("priceDisplay") or listing.get("price", "")
            price_nzd = parse_price_nzd(price_raw)

            address = listing.get("address") or listing.get("location", "")
            region = listing.get("region") or listing.get("district", "")

            beds = listing.get("bedrooms")
            baths = listing.get("bathrooms")
            rooms = None
            if beds or baths:
                parts = []
                if beds:
                    parts.append(f"{beds}bed")
                if baths:
                    parts.append(f"{baths}bath")
                rooms = " / ".join(parts)

            images = []
            for img in listing.get("images", []) or listing.get("photos", []):
                if isinstance(img, str):
                    images.append(img)
                elif isinstance(img, dict):
                    images.append(img.get("url") or img.get("fullUrl", ""))

            return RawListing(
                source_slug=self.slug,
                source_url=url,
                source_listing_id=str(listing.get("id", "")),
                title=clean_text(title),
                description=clean_text(listing.get("description")),
                price_raw=price_raw or None,
                price_jpy=nzd_to_jpy(price_nzd) if price_nzd else None,
                prefecture=clean_text(region) if region else None,
                city=clean_text(listing.get("suburb")),
                address_raw=clean_text(address) if address else None,
                land_sqm=parse_land_area_nz(str(listing.get("landArea", ""))),
                building_sqm=parse_area_sqm_nz(str(listing.get("floorArea", ""))),
                rooms=rooms,
                image_urls=[i for i in images if i][:20],
                building_type="detached",
                raw_data={"country": self.country, "currency": self.currency,
                          "price_nzd": price_nzd},
            )

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"[{self.slug}] NEXT_DATA parse error: {e}")
            return None

    def _parse_html_listing(self, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        """Fallback HTML parsing."""
        # Title
        title_el = soup.select_one("h1") or soup.select_one("title")
        title = clean_text(title_el.get_text()) if title_el else None
        if not title:
            return None

        # Price
        price_el = (
            soup.select_one("[class*='price']")
            or soup.select_one("[class*='Price']")
        )
        price_raw = clean_text(price_el.get_text()) if price_el else None
        price_nzd = parse_price_nzd(price_raw) if price_raw else None

        # Address
        addr_el = soup.select_one("[class*='address']")
        address = clean_text(addr_el.get_text()) if addr_el else None

        # Description
        desc_el = soup.select_one("[class*='description']")
        description = clean_text(desc_el.get_text()) if desc_el else None

        # Images
        images = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if src and not src.startswith("data:") and "logo" not in src.lower():
                if any(kw in src.lower() for kw in ["photo", "image", "listing", "property", "media"]):
                    full = make_absolute_url(self.base_url, src)
                    if full not in images:
                        images.append(full)

        # Listing ID from URL
        listing_id = None
        id_match = re.search(r'/(\d+)/?$', url)
        if id_match:
            listing_id = id_match.group(1)

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=listing_id,
            title=title,
            description=description,
            price_raw=price_raw,
            price_jpy=nzd_to_jpy(price_nzd) if price_nzd else None,
            address_raw=address,
            image_urls=images[:20],
            building_type="detached",
            raw_data={"country": self.country, "currency": self.currency,
                      "price_nzd": price_nzd},
        )
