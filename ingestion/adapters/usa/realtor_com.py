"""
Realtor.com — official site of the National Association of Realtors.
Medium scraping difficulty. Good coverage of cheap rural properties.

Strategy: Search by city with price filter, look for __NEXT_DATA__ JSON
in <script> tags (Next.js site) for structured data.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.adapters.usa.base_usa import USABaseAdapter
from ingestion.models import RawListing
from ingestion.utils_usa import parse_price_usd, sqft_to_sqm, usd_to_jpy
from ingestion.utils import clean_text, make_absolute_url

logger = logging.getLogger(__name__)


class RealtorComAdapter(USABaseAdapter):
    """Adapter for Realtor.com — major US real estate portal."""

    slug = "realtor-com"
    base_url = "https://www.realtor.com"

    # Search URL pattern:
    # realtor.com/realestateandhomes-search/Cleveland_OH/price-na-100000/type-single-family-home
    TARGET_CITIES = [
        # Ohio
        "Cleveland_OH", "Youngstown_OH", "Dayton_OH", "Akron_OH",
        # Michigan
        "Detroit_MI", "Flint_MI", "Saginaw_MI",
        # Pennsylvania
        "Pittsburgh_PA", "Scranton_PA",
        # Indiana
        "Indianapolis_IN", "Gary_IN",
        # Others
        "Memphis_TN", "Birmingham_AL", "Jackson_MS",
        "Little-Rock_AR", "St-Louis_MO",
    ]

    REQUEST_DELAY = 6
    MAX_PER_CITY = 200

    def __init__(self):
        super().__init__()
        self.delay = self.REQUEST_DELAY
        self.client.headers.update({
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def get_listing_urls(self) -> list[str]:
        """Collect listing URLs from search results pages for each target city."""
        urls: list[str] = []

        for city_state in self.TARGET_CITIES:
            search_url = (
                f"{self.base_url}/realestateandhomes-search/"
                f"{city_state}/price-na-100000/type-single-family-home"
            )

            try:
                html = self.fetch_page(search_url)
            except Exception as e:
                logger.warning(f"[{self.slug}] {city_state} failed: {e}")
                time.sleep(self.delay)
                continue

            soup = BeautifulSoup(html, "lxml")

            # Try to extract from __NEXT_DATA__ JSON first
            next_data_urls = self._extract_urls_from_next_data(soup)
            if next_data_urls:
                for u in next_data_urls:
                    if u not in urls:
                        urls.append(u)
                logger.info(
                    f"[{self.slug}] {city_state}: {len(next_data_urls)} URLs "
                    f"from __NEXT_DATA__ (total: {len(urls)})"
                )
            else:
                # Fallback: scrape links from HTML
                found = 0
                for a in soup.select("a[href*='/realestateandhomes-detail/']"):
                    href = a.get("href", "")
                    if href:
                        full = make_absolute_url(self.base_url, href)
                        if full not in urls:
                            urls.append(full)
                            found += 1
                logger.info(
                    f"[{self.slug}] {city_state}: {found} URLs "
                    f"from HTML (total: {len(urls)})"
                )

            time.sleep(self.delay)

        logger.info(f"[{self.slug}] Total: {len(urls)} listing URLs")
        return urls

    def _extract_urls_from_next_data(self, soup: BeautifulSoup) -> list[str]:
        """Extract listing URLs from Next.js __NEXT_DATA__ script tag."""
        script = soup.select_one("script#__NEXT_DATA__")
        if not script:
            return []

        try:
            data = json.loads(script.string)
            # Navigate the Next.js data structure for search results
            props = data.get("props", {}).get("pageProps", {})
            search_results = (
                props.get("searchResults", {})
                .get("home_search", {})
                .get("results", [])
            )

            urls = []
            for result in search_results:
                href = result.get("href")
                if href:
                    urls.append(make_absolute_url(self.base_url, href))
                # Also try permalink
                permalink = result.get("permalink")
                if permalink and not href:
                    url = f"{self.base_url}/realestateandhomes-detail/{permalink}"
                    urls.append(url)

            return urls
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.debug(f"[{self.slug}] __NEXT_DATA__ parse error: {e}")
            return []

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract listing data from a Realtor.com detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Try __NEXT_DATA__ first for structured data
        listing = self._extract_from_next_data(soup, url)
        if listing:
            return listing

        # Fallback: HTML scraping
        return self._extract_from_html(soup, url)

    def _extract_from_next_data(self, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        """Extract listing data from __NEXT_DATA__ JSON."""
        script = soup.select_one("script#__NEXT_DATA__")
        if not script:
            return None

        try:
            data = json.loads(script.string)
            props = data.get("props", {}).get("pageProps", {})
            listing_data = props.get("property", {}) or props.get("initialState", {})

            if not listing_data:
                return None

            # Extract fields
            address = listing_data.get("location", {}).get("address", {})
            description_data = listing_data.get("description", {})

            price_usd = listing_data.get("list_price") or description_data.get("list_price")
            if not price_usd:
                return None

            if isinstance(price_usd, str):
                price_usd = parse_price_usd(price_usd)
            else:
                price_usd = int(price_usd)

            if price_usd and price_usd > self.PRICE_THRESHOLD:
                return None

            city = address.get("city", "")
            state = address.get("state_code", "")
            street = address.get("line", "")
            zip_code = address.get("postal_code", "")

            title = f"{street}, {city}, {state}" if street else f"Property in {city}, {state}"

            sqft = description_data.get("sqft")
            building_sqm = sqft_to_sqm(float(sqft)) if sqft else None

            lot_sqft = description_data.get("lot_sqft")
            land_sqm = sqft_to_sqm(float(lot_sqft)) if lot_sqft else None

            beds = description_data.get("beds", "")
            baths = description_data.get("baths", "")
            rooms = f"{beds}bd/{baths}ba" if beds or baths else None

            year_built = description_data.get("year_built")

            # Images
            photos = listing_data.get("photos", [])
            image_urls = [p.get("href", "") for p in photos if p.get("href")][:20]

            lat = listing_data.get("location", {}).get("coordinate", {}).get("lat")
            lon = listing_data.get("location", {}).get("coordinate", {}).get("lon")

            price_jpy = usd_to_jpy(price_usd) if price_usd else None

            return RawListing(
                source_slug=self.slug,
                source_url=url,
                source_listing_id=listing_data.get("property_id", url.split("/")[-1]),
                title=title,
                description=description_data.get("text"),
                price_raw=f"${price_usd:,}" if price_usd else None,
                price_jpy=price_jpy,
                prefecture=state,
                city=city,
                address_raw=f"{street}, {city}, {state} {zip_code}".strip(", "),
                latitude=lat,
                longitude=lon,
                building_sqm=building_sqm,
                land_sqm=land_sqm,
                year_built=int(year_built) if year_built else None,
                rooms=rooms,
                image_urls=image_urls,
                building_type="detached",
                raw_data={
                    "country": "usa",
                    "price_usd": price_usd,
                    "currency": "USD",
                    "sqft": sqft,
                },
            )

        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.debug(f"[{self.slug}] __NEXT_DATA__ detail parse error: {e}")
            return None

    def _extract_from_html(self, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        """Fallback HTML extraction for Realtor.com."""
        title_tag = soup.select_one("h1")
        title = clean_text(title_tag.get_text()) if title_tag else None
        if not title:
            return None

        # Price
        price_usd = None
        price_raw = None
        price_el = soup.select_one("[data-testid='list-price']") or soup.select_one("[class*='price']")
        if price_el:
            price_raw = clean_text(price_el.get_text())
            price_usd = parse_price_usd(price_raw)

        if not price_usd:
            price_match = re.search(r'\$[\d,]+', soup.get_text()[:2000])
            if price_match:
                price_raw = price_match.group(0)
                price_usd = parse_price_usd(price_raw)

        if price_usd and price_usd > self.PRICE_THRESHOLD:
            return None

        # Location from title: "123 Main St, Cleveland, OH 44101"
        loc_match = re.search(
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2})\s*(\d{5})?',
            title or ""
        )
        city = loc_match.group(1) if loc_match else None
        state = loc_match.group(2) if loc_match else None

        # Images
        images = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if src and "rdcpix" in src and not src.startswith("data:"):
                if src not in images:
                    images.append(src)
        images = images[:20]

        price_jpy = usd_to_jpy(price_usd) if price_usd else None

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=url.rstrip("/").split("/")[-1],
            title=title,
            price_raw=price_raw,
            price_jpy=price_jpy,
            prefecture=state,
            city=city,
            address_raw=title,
            image_urls=images,
            building_type="detached",
            raw_data={
                "country": "usa",
                "price_usd": price_usd,
                "currency": "USD",
            },
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with RealtorComAdapter() as adapter:
        urls = adapter.get_listing_urls()
        print(f"Found {len(urls)} listings")
        if urls:
            listing = adapter.extract_listing(urls[0])
            if listing:
                print(f"  Title: {listing.title}")
                print(f"  Price: {listing.price_raw}")
