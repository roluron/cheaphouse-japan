"""
LandWatch.com — rural land and houses.
Good for finding cheap rural properties with land.
Target: houses with land under $100K.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.adapters.usa.base_usa import USABaseAdapter
from ingestion.models import RawListing
from ingestion.utils_usa import parse_price_usd, parse_area_sqft, sqft_to_sqm, usd_to_jpy
from ingestion.utils import clean_text, make_absolute_url

logger = logging.getLogger(__name__)


class LandWatchUSAdapter(USABaseAdapter):
    """Adapter for LandWatch.com — rural land and houses."""

    slug = "landwatch-us"
    base_url = "https://www.landwatch.com"

    # Search page pattern: /state/houses-for-sale?price-max=100000
    TARGET_STATES_URLS = {
        "OH": "ohio",
        "MI": "michigan",
        "IN": "indiana",
        "PA": "pennsylvania",
        "WV": "west-virginia",
        "MS": "mississippi",
        "AL": "alabama",
        "AR": "arkansas",
        "KS": "kansas",
        "MO": "missouri",
    }

    MAX_PAGES_PER_STATE = 5
    REQUEST_DELAY = 4

    def __init__(self):
        super().__init__()
        self.delay = self.REQUEST_DELAY

    def get_listing_urls(self) -> list[str]:
        """Scrape listing URLs from search results for each target state."""
        urls: list[str] = []

        for state_code, state_name in self.TARGET_STATES_URLS.items():
            for page in range(1, self.MAX_PAGES_PER_STATE + 1):
                search_url = (
                    f"{self.base_url}/{state_name}/houses-for-sale"
                    f"?price-max=100000"
                )
                if page > 1:
                    search_url += f"&page={page}"

                try:
                    html = self.fetch_page(search_url)
                except Exception as e:
                    logger.warning(f"[{self.slug}] {state_code} p{page} failed: {e}")
                    break

                soup = BeautifulSoup(html, "lxml")
                found = 0

                # LandWatch listing links typically have /property/ in the URL
                for a in soup.select("a[href*='/property/']"):
                    href = a.get("href", "")
                    if href:
                        full = make_absolute_url(self.base_url, href)
                        if full not in urls:
                            urls.append(full)
                            found += 1

                logger.info(
                    f"[{self.slug}] {state_code} p{page}: "
                    f"{found} URLs (total: {len(urls)})"
                )

                if found == 0:
                    break

                time.sleep(self.delay)

        logger.info(f"[{self.slug}] Total: {len(urls)} listing URLs")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract listing data from a LandWatch detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Title
        title_tag = soup.select_one("h1")
        title = clean_text(title_tag.get_text()) if title_tag else None
        if not title:
            return None

        # Price
        price_usd = None
        price_raw = None
        # Look for price in dedicated element or in page content
        price_el = soup.select_one("[class*='price']") or soup.select_one("[data-price]")
        if price_el:
            price_raw = clean_text(price_el.get_text())
            price_usd = parse_price_usd(price_raw)

        if not price_usd:
            price_match = re.search(r'\$[\d,]+', soup.get_text()[:1000])
            if price_match:
                price_raw = price_match.group(0)
                price_usd = parse_price_usd(price_raw)

        if price_usd and price_usd > self.PRICE_THRESHOLD:
            return None

        # Location
        city = None
        state = None
        address_raw = None

        # Try to parse location from title: "X Acres in City, State"
        loc_match = re.search(
            r'(?:in|near)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2})',
            title or ""
        )
        if loc_match:
            city = loc_match.group(1)
            state = loc_match.group(2)
            address_raw = f"{city}, {state}"

        # Acreage / lot size
        land_sqm = None
        acre_match = re.search(r'([\d,.]+)\s*(?:acres?|ac)\b', soup.get_text()[:2000], re.IGNORECASE)
        if acre_match:
            try:
                acres = float(acre_match.group(1).replace(',', ''))
                land_sqm = round(acres * 4046.86, 1)  # 1 acre = 4046.86 sqm
            except ValueError:
                pass

        # Building sqft
        sqft = parse_area_sqft(soup.get_text()[:2000])
        building_sqm = sqft_to_sqm(sqft) if sqft else None

        # Description
        description = None
        desc_el = soup.select_one("[class*='description']") or soup.select_one("article")
        if desc_el:
            description = clean_text(desc_el.get_text()[:500])

        # Images
        images = self._extract_images(soup)

        # Rooms
        rooms = None
        bed_match = re.search(r'(\d+)\s*(?:bed|br)', soup.get_text()[:2000], re.IGNORECASE)
        bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', soup.get_text()[:2000], re.IGNORECASE)
        if bed_match or bath_match:
            beds = bed_match.group(1) if bed_match else "?"
            baths = bath_match.group(1) if bath_match else "?"
            rooms = f"{beds}bd/{baths}ba"

        price_jpy = usd_to_jpy(price_usd) if price_usd else None

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=url.rstrip("/").split("/")[-1],
            title=title,
            description=description,
            price_raw=price_raw,
            price_jpy=price_jpy,
            prefecture=state,
            city=city,
            address_raw=address_raw,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            rooms=rooms,
            image_urls=images,
            building_type="detached",
            raw_data={
                "country": "usa",
                "price_usd": price_usd,
                "currency": "USD",
                "sqft": sqft,
            },
        )

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        """Extract property images."""
        images: list[str] = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if not src or src.startswith("data:"):
                continue
            if any(skip in src.lower() for skip in [
                "logo", "icon", "avatar", "pixel", "tracking",
                "sprite", "blank", "placeholder",
            ]):
                continue
            # Prefer larger images
            width = img.get("width", "")
            if width and width.isdigit() and int(width) < 50:
                continue
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)
        return images[:20]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with LandWatchUSAdapter() as adapter:
        urls = adapter.get_listing_urls()
        print(f"Found {len(urls)} listings")
        if urls:
            listing = adapter.extract_listing(urls[0])
            if listing:
                print(f"  Title: {listing.title}")
                print(f"  Price: {listing.price_raw}")
