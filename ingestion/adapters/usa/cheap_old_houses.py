"""
CheapOldHouses.com — curated historic/cheap houses across America.
This is THE perfect source: focuses specifically on cheap houses with character.
Easy to scrape, curated content, great photos.

Strategy: Scrape listing feed, extract each post with price, location, photos.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.adapters.usa.base_usa import USABaseAdapter
from ingestion.models import RawListing
from ingestion.utils_usa import parse_price_usd, parse_area_sqft, sqft_to_sqm, usd_to_jpy, parse_us_address
from ingestion.utils import clean_text, make_absolute_url

logger = logging.getLogger(__name__)


class CheapOldHousesAdapter(USABaseAdapter):
    """Adapter for CheapOldHouses.com — curated cheap historic houses."""

    slug = "cheap-old-houses-us"
    base_url = "https://cheapoldhouses.com"

    MAX_PAGES = 20
    REQUEST_DELAY = 2

    def __init__(self):
        super().__init__()
        self.delay = self.REQUEST_DELAY

    def get_listing_urls(self) -> list[str]:
        """Scrape listing URLs from the main feed pages."""
        urls: list[str] = []

        for page in range(1, self.MAX_PAGES + 1):
            if page == 1:
                page_url = self.base_url
            else:
                page_url = f"{self.base_url}/page/{page}"

            try:
                html = self.fetch_page(page_url)
            except Exception as e:
                logger.warning(f"[{self.slug}] Page {page} failed: {e}")
                break

            soup = BeautifulSoup(html, "lxml")
            found = 0

            # Look for article/post links
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                # Listing pages typically have a pattern like /listing/ or individual post URLs
                if not href or href == "#":
                    continue
                if any(skip in href for skip in [
                    "/category/", "/tag/", "/author/", "/about",
                    "/contact", "/privacy", "/terms", "facebook.com",
                    "instagram.com", "twitter.com", "/cart", "/shop",
                    "/page/", "#comment", "/feed",
                ]):
                    continue
                # Match listing-style URLs (posts with property details)
                if re.search(r'cheapoldhouses\.com/\d{4}/\d{2}/', href):
                    full = make_absolute_url(self.base_url, href)
                    if full not in urls:
                        urls.append(full)
                        found += 1
                elif re.search(r'cheapoldhouses\.com/listing/', href):
                    full = make_absolute_url(self.base_url, href)
                    if full not in urls:
                        urls.append(full)
                        found += 1

            logger.info(f"[{self.slug}] Page {page}: found {found} URLs (total: {len(urls)})")

            if found == 0:
                break  # No more pages

            import time
            time.sleep(self.delay)

        logger.info(f"[{self.slug}] Total: {len(urls)} listing URLs")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract listing data from a detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Title
        title_tag = soup.select_one("h1") or soup.select_one("title")
        title = clean_text(title_tag.get_text()) if title_tag else None
        if not title:
            return None

        # Extract the main content area
        content = soup.select_one("article") or soup.select_one(".entry-content") or soup
        content_text = content.get_text(" ", strip=True) if content else ""

        # Price — look for dollar amounts in title or content
        price_usd = None
        price_raw = None
        price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', title or "")
        if not price_match:
            price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', content_text[:500])
        if price_match:
            price_raw = price_match.group(0)
            price_usd = parse_price_usd(price_raw)

        # Location — look for "City, State" or "City, ST" patterns
        location_match = re.search(
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2})\b',
            title or ""
        )
        if not location_match:
            location_match = re.search(
                r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2})\b',
                content_text[:300]
            )

        city = location_match.group(1) if location_match else None
        state = location_match.group(2) if location_match else None
        address_raw = f"{city}, {state}" if city and state else None

        # Square footage
        sqft = parse_area_sqft(content_text)
        building_sqm = sqft_to_sqm(sqft) if sqft else None

        # Year built
        year_built = None
        year_match = re.search(r'\b(1[789]\d{2}|20[012]\d)\b', content_text[:500])
        if year_match:
            yr = int(year_match.group(1))
            if 1700 <= yr <= 2030:
                year_built = yr

        # Bedrooms/rooms
        rooms = None
        bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', content_text, re.IGNORECASE)
        bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba|bathroom)', content_text, re.IGNORECASE)
        if bed_match or bath_match:
            beds = bed_match.group(1) if bed_match else "?"
            baths = bath_match.group(1) if bath_match else "?"
            rooms = f"{beds}bd/{baths}ba"

        # Description — first paragraph or meta description
        description = None
        meta_desc = soup.select_one('meta[name="description"]')
        if meta_desc:
            description = clean_text(meta_desc.get("content", ""))
        if not description:
            first_p = content.select_one("p") if content else None
            if first_p:
                description = clean_text(first_p.get_text())

        # Images
        images = self._extract_images(soup)

        # Convert USD to JPY for pipeline compatibility
        price_jpy = usd_to_jpy(price_usd) if price_usd else None

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=url.rstrip("/").split("/")[-1],
            title=title,
            description=description,
            price_raw=price_raw,
            price_jpy=price_jpy,
            prefecture=state,  # Using state in place of prefecture
            city=city,
            address_raw=address_raw,
            building_sqm=building_sqm,
            year_built=year_built,
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
        """Extract property images, filtering out nav/logo images."""
        images: list[str] = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if not src or src.startswith("data:"):
                continue
            # Skip small icons/logos
            if any(skip in src.lower() for skip in [
                "logo", "icon", "avatar", "gravatar",
                "wp-includes", "emoji", "smilies",
            ]):
                continue
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)
        return images[:20]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with CheapOldHousesAdapter() as adapter:
        urls = adapter.get_listing_urls()
        print(f"Found {len(urls)} listings")
        if urls:
            listing = adapter.extract_listing(urls[0])
            if listing:
                print(f"  Title: {listing.title}")
                print(f"  Price: {listing.price_raw}")
                print(f"  Location: {listing.city}, {listing.prefecture}")
