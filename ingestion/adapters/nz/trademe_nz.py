"""
Trade Me Property — New Zealand's dominant marketplace (~80% market share).
HAS AN OFFICIAL API: https://developer.trademe.co.nz/
Register for free API key. This is the best approach.

Strategy:
  1. Try API first (if credentials set in .env)
  2. Fall back to HTML scraping if API unavailable
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.adapters.nz.base_nz import NZBaseAdapter
from ingestion.models import RawListing
from ingestion.utils import clean_text, make_absolute_url
from ingestion.utils_nz import parse_price_nzd, parse_area_sqm_nz, parse_land_area_nz, nzd_to_jpy

logger = logging.getLogger(__name__)


class TradeMeNZAdapter(NZBaseAdapter):
    """Adapter for Trade Me Property — trademe.co.nz."""

    slug = "trademe-nz"
    base_url = "https://www.trademe.co.nz"

    # API base (preferred approach)
    API_BASE = "https://api.trademe.co.nz/v1"

    # Fallback scrape URL
    FALLBACK_SCRAPE_URL = "https://www.trademe.co.nz/a/property/residential/sale/search"

    # Target districts (cheapest regions) — Trade Me district IDs
    DISTRICT_IDS = {
        "west-coast": 28,
        "southland": 27,
        "whanganui": 19,
        "south-waikato": 5,
        "kawerau": 7,
        "opotiki": 7,
        "tararua": 22,
        "otago": 24,
        "manawatu": 20,
        "gisborne": 8,
    }

    def __init__(self):
        super().__init__()
        self.delay = 3
        self.api_key = os.environ.get("TRADEME_CONSUMER_KEY", "")
        self.api_secret = os.environ.get("TRADEME_CONSUMER_SECRET", "")
        self.oauth_token = os.environ.get("TRADEME_OAUTH_TOKEN", "")
        self.oauth_secret = os.environ.get("TRADEME_OAUTH_TOKEN_SECRET", "")
        self.use_api = bool(self.api_key and self.oauth_token)

        if self.use_api:
            logger.info(f"[{self.slug}] API credentials found — using API mode")
        else:
            logger.info(f"[{self.slug}] No API credentials — using HTML scraping")

        self.client.headers.update({
            "Accept-Language": "en-NZ,en;q=0.9",
        })

    def get_listing_urls(self) -> list[str]:
        """Get listing URLs — API or HTML fallback."""
        if self.use_api:
            return self._get_urls_api()
        return self._get_urls_scrape()

    def _get_urls_api(self) -> list[str]:
        """Get listing URLs from Trade Me API."""
        urls: list[str] = []

        for region, district_id in self.DISTRICT_IDS.items():
            try:
                api_url = (
                    f"{self.API_BASE}/Search/Property/Residential.json"
                    f"?price_max={self.PRICE_THRESHOLD}"
                    f"&district={district_id}"
                    f"&property_type=House"
                    f"&sort_order=ExpiryDesc"
                    f"&rows=50&page=1"
                )

                # OAuth 1.0a headers would go here
                # For now, use consumer key as query param (sandbox mode)
                api_url += f"&oauth_consumer_key={self.api_key}"

                html = self.fetch_page(api_url)
                try:
                    data = json.loads(html)
                except json.JSONDecodeError:
                    logger.warning(f"[{self.slug}] API returned non-JSON for {region}")
                    continue

                listings = data.get("List", [])
                for item in listings:
                    listing_id = item.get("ListingId")
                    if listing_id:
                        detail_url = f"https://www.trademe.co.nz/a/property/residential/sale/listing/{listing_id}"
                        if detail_url not in urls:
                            urls.append(detail_url)

                logger.info(f"[{self.slug}] API: {region} → {len(listings)} listings")
                time.sleep(1)  # Rate limit: 300 req/day

            except Exception as e:
                logger.warning(f"[{self.slug}] API error for {region}: {e}")

        logger.info(f"[{self.slug}] API total: {len(urls)} listing URLs")
        return urls

    def _get_urls_scrape(self) -> list[str]:
        """Fallback: scrape listing URLs from HTML search pages."""
        urls: list[str] = []

        for region in list(self.DISTRICT_IDS.keys())[:5]:  # Limit regions in scrape mode
            for page in range(1, 4):  # Max 3 pages per region
                try:
                    search_url = (
                        f"{self.FALLBACK_SCRAPE_URL}"
                        f"?price_max={self.PRICE_THRESHOLD}"
                        f"&region={region}"
                        f"&page={page}"
                    )

                    html = self.fetch_page(search_url)
                    soup = BeautifulSoup(html, "lxml")

                    found = 0
                    for a in soup.select("a[href]"):
                        href = a.get("href", "")
                        if "/a/property/residential/sale/listing/" in href:
                            full = make_absolute_url(self.base_url, href)
                            # Strip query params
                            full = full.split("?")[0]
                            if full not in urls:
                                urls.append(full)
                                found += 1

                    if found == 0:
                        break  # No more listings

                    time.sleep(self.delay)

                except Exception as e:
                    logger.warning(f"[{self.slug}] Scrape error {region} p{page}: {e}")
                    break

        logger.info(f"[{self.slug}] Scrape total: {len(urls)} listing URLs")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract listing from a Trade Me detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Try to find JSON-LD or __NEXT_DATA__ first
        listing_data = self._extract_json_data(soup)
        if listing_data:
            return self._parse_json_listing(listing_data, url)

        # Fallback: parse HTML
        return self._parse_html_listing(soup, url)

    def _extract_json_data(self, soup: BeautifulSoup) -> Optional[dict]:
        """Try extracting structured data from page."""
        # Try __NEXT_DATA__
        script = soup.select_one("script#__NEXT_DATA__")
        if script and script.string:
            try:
                data = json.loads(script.string)
                props = data.get("props", {}).get("pageProps", {})
                return props.get("listing") or props.get("listingDetail")
            except (json.JSONDecodeError, AttributeError):
                pass

        # Try JSON-LD
        for script in soup.select('script[type="application/ld+json"]'):
            if script.string:
                try:
                    ld = json.loads(script.string)
                    if isinstance(ld, dict) and ld.get("@type") in ("Product", "RealEstateListing"):
                        return ld
                except json.JSONDecodeError:
                    pass

        return None

    def _parse_json_listing(self, data: dict, url: str) -> Optional[RawListing]:
        """Parse structured JSON listing data."""
        title = data.get("Title") or data.get("title") or data.get("name", "")
        if not title:
            return None

        price_raw = data.get("PriceDisplay") or data.get("priceDisplay", "")
        price_nzd = parse_price_nzd(price_raw)

        address = data.get("Address") or data.get("address", "")
        if isinstance(address, dict):
            address = f"{address.get('suburb', '')}, {address.get('district', '')}"

        region = data.get("District") or data.get("Region", "")

        listing_id = str(data.get("ListingId") or data.get("listingId", ""))

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=listing_id or None,
            title=clean_text(title),
            description=clean_text(data.get("Body") or data.get("description")),
            price_raw=price_raw or None,
            price_jpy=nzd_to_jpy(price_nzd) if price_nzd else None,
            prefecture=clean_text(region) if region else None,
            city=clean_text(data.get("Suburb") or data.get("suburb")),
            address_raw=clean_text(address) if address else None,
            land_sqm=parse_land_area_nz(str(data.get("LandArea", ""))),
            building_sqm=parse_area_sqm_nz(str(data.get("FloorArea", ""))),
            rooms=self._format_rooms(data),
            image_urls=self._extract_json_images(data),
            building_type="detached",
            raw_data={"country": self.country, "currency": self.currency,
                      "price_nzd": price_nzd},
        )

    def _parse_html_listing(self, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        """Fallback HTML parsing for Trade Me listing page."""
        # Title
        title_el = soup.select_one("h1") or soup.select_one("title")
        title = clean_text(title_el.get_text()) if title_el else None
        if not title:
            return None

        # Price
        price_el = (
            soup.select_one("[class*='price']")
            or soup.select_one("[data-testid='price']")
            or soup.select_one("h2")
        )
        price_raw = clean_text(price_el.get_text()) if price_el else None
        price_nzd = parse_price_nzd(price_raw) if price_raw else None

        # Address
        addr_el = (
            soup.select_one("[class*='address']")
            or soup.select_one("[data-testid='address']")
        )
        address = clean_text(addr_el.get_text()) if addr_el else None

        # Region from address
        region = self._extract_region_from_address(address) if address else None

        # Description
        desc_el = soup.select_one("[class*='description']") or soup.select_one("[class*='body']")
        description = clean_text(desc_el.get_text()) if desc_el else None

        # Images
        images = self._extract_html_images(soup)

        # Extract listing ID from URL
        listing_id = None
        id_match = re.search(r'/listing/(\d+)', url)
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
            prefecture=region,
            address_raw=address,
            image_urls=images,
            building_type="detached",
            raw_data={"country": self.country, "currency": self.currency,
                      "price_nzd": price_nzd},
        )

    def _format_rooms(self, data: dict) -> Optional[str]:
        """Format bedrooms/bathrooms from JSON data."""
        beds = data.get("Bedrooms") or data.get("bedrooms")
        baths = data.get("Bathrooms") or data.get("bathrooms")
        if beds or baths:
            parts = []
            if beds:
                parts.append(f"{beds}bed")
            if baths:
                parts.append(f"{baths}bath")
            return " / ".join(parts)
        return None

    def _extract_json_images(self, data: dict) -> list[str]:
        """Extract image URLs from JSON data."""
        images = []
        photo_urls = data.get("PhotoUrls") or data.get("photos") or data.get("images") or []
        if isinstance(photo_urls, list):
            for photo in photo_urls:
                if isinstance(photo, str):
                    images.append(photo)
                elif isinstance(photo, dict):
                    url = photo.get("url") or photo.get("FullSize") or photo.get("Large", "")
                    if url:
                        images.append(url)
        return images[:20]

    def _extract_html_images(self, soup: BeautifulSoup) -> list[str]:
        """Extract images from HTML."""
        images = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if not src or "logo" in src.lower() or "icon" in src.lower():
                continue
            if src.startswith("data:"):
                continue
            if any(kw in src.lower() for kw in ["photo", "image", "listing", "property"]):
                full = make_absolute_url(self.base_url, src)
                if full not in images:
                    images.append(full)
        return images[:20]

    def _extract_region_from_address(self, address: str) -> Optional[str]:
        """Try to extract NZ region from address text."""
        if not address:
            return None
        address_lower = address.lower()
        region_names = {
            "west coast": "West Coast", "southland": "Southland",
            "otago": "Otago", "canterbury": "Canterbury",
            "whanganui": "Whanganui", "manawatu": "Manawatu",
            "waikato": "Waikato", "bay of plenty": "Bay of Plenty",
            "gisborne": "Gisborne", "hawke": "Hawke's Bay",
            "taranaki": "Taranaki", "wellington": "Wellington",
            "nelson": "Nelson", "marlborough": "Marlborough",
        }
        for key, name in region_names.items():
            if key in address_lower:
                return name
        return None
