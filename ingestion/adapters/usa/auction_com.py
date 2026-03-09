"""
Auction.com — foreclosure and bank-owned properties.
Cheapest US properties but require quick action.
Target: houses under $50K.
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


class AuctionComAdapter(USABaseAdapter):
    """Adapter for Auction.com — foreclosure properties."""

    slug = "auction-com"
    base_url = "https://www.auction.com"

    # Lower price threshold for foreclosures
    PRICE_THRESHOLD = 50_000

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

    MAX_PAGES_PER_STATE = 3
    REQUEST_DELAY = 4

    def __init__(self):
        super().__init__()
        self.delay = self.REQUEST_DELAY
        self.client.headers.update({
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def get_listing_urls(self) -> list[str]:
        """Collect listing URLs from Auction.com search pages."""
        urls: list[str] = []

        for state_code, state_name in self.TARGET_STATES_URLS.items():
            for page in range(1, self.MAX_PAGES_PER_STATE + 1):
                search_url = (
                    f"{self.base_url}/residential/{state_name}/"
                    f"?propertyType=SF&maxPrice=50000"
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

                # Look for property detail links
                for a in soup.select("a[href*='/details/']"):
                    href = a.get("href", "")
                    if href:
                        full = make_absolute_url(self.base_url, href)
                        if full not in urls:
                            urls.append(full)
                            found += 1

                # Also try JSON-LD or data attributes
                if found == 0:
                    for a in soup.select("a[href]"):
                        href = a.get("href", "")
                        if "/residential/" in href and re.search(r'/\d+$', href):
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
        """Extract listing data from an Auction.com detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Try JSON-LD structured data first
        listing = self._extract_from_json_ld(soup, url)
        if listing:
            return listing

        # Fallback: HTML parsing
        return self._extract_from_html(soup, url)

    def _extract_from_json_ld(self, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        """Extract from JSON-LD structured data if present."""
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                if data.get("@type") not in ("Product", "RealEstateListing", "SingleFamilyResidence"):
                    continue

                name = data.get("name", "")
                price = data.get("offers", {}).get("price")
                if not price:
                    continue

                price_usd = int(float(str(price).replace(",", "")))
                if price_usd > self.PRICE_THRESHOLD:
                    return None

                address = data.get("address", {})
                city = address.get("addressLocality", "")
                state = address.get("addressRegion", "")

                price_jpy = usd_to_jpy(price_usd)

                return RawListing(
                    source_slug=self.slug,
                    source_url=url,
                    source_listing_id=url.rstrip("/").split("/")[-1],
                    title=name or f"Foreclosure in {city}, {state}",
                    description=data.get("description"),
                    price_raw=f"${price_usd:,}",
                    price_jpy=price_jpy,
                    prefecture=state,
                    city=city,
                    address_raw=f"{city}, {state}",
                    image_urls=[data.get("image", "")] if data.get("image") else [],
                    building_type="detached",
                    condition_notes="Foreclosure/auction property. Sold as-is. Cash preferred.",
                    raw_data={
                        "country": "usa",
                        "price_usd": price_usd,
                        "currency": "USD",
                        "listing_type": "auction",
                        "foreclosure": True,
                    },
                )
            except (json.JSONDecodeError, ValueError, TypeError):
                continue

        return None

    def _extract_from_html(self, soup: BeautifulSoup, url: str) -> Optional[RawListing]:
        """Fallback HTML extraction for Auction.com."""
        title_tag = soup.select_one("h1")
        title = clean_text(title_tag.get_text()) if title_tag else None
        if not title:
            return None

        # Price — look for current bid or starting bid
        price_usd = None
        price_raw = None
        for selector in [
            "[class*='bid']", "[class*='price']",
            "[data-testid*='price']", "[class*='amount']",
        ]:
            el = soup.select_one(selector)
            if el:
                text = clean_text(el.get_text())
                if text and "$" in text:
                    price_raw = text
                    price_usd = parse_price_usd(text)
                    break

        if not price_usd:
            price_match = re.search(r'\$[\d,]+', soup.get_text()[:3000])
            if price_match:
                price_raw = price_match.group(0)
                price_usd = parse_price_usd(price_raw)

        if price_usd and price_usd > self.PRICE_THRESHOLD:
            return None

        # Location
        loc_match = re.search(
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2})\s*(\d{5})?',
            title or ""
        )
        city = loc_match.group(1) if loc_match else None
        state = loc_match.group(2) if loc_match else None

        # Auction date
        auction_date = None
        date_match = re.search(
            r'(?:auction|bid)\s*(?:date|ends?)?\s*:?\s*(\w+ \d{1,2},?\s*\d{4})',
            soup.get_text()[:3000], re.IGNORECASE
        )
        if date_match:
            auction_date = date_match.group(1)

        # Sqft
        sqft_match = re.search(r'([\d,]+)\s*(?:sq\s*ft|sqft|sf)', soup.get_text()[:3000], re.IGNORECASE)
        sqft = None
        if sqft_match:
            try:
                sqft = float(sqft_match.group(1).replace(',', ''))
            except ValueError:
                pass
        building_sqm = sqft_to_sqm(sqft) if sqft else None

        # Images
        images = []
        for img in soup.select("img[src]"):
            src = img.get("src", "")
            if src and not src.startswith("data:"):
                if any(skip in src.lower() for skip in ["logo", "icon", "sprite"]):
                    continue
                full = make_absolute_url(self.base_url, src)
                if full not in images:
                    images.append(full)
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
            address_raw=f"{city}, {state}" if city and state else None,
            building_sqm=building_sqm,
            image_urls=images,
            building_type="detached",
            condition_notes="Foreclosure/auction property. Sold as-is. Cash preferred.",
            raw_data={
                "country": "usa",
                "price_usd": price_usd,
                "currency": "USD",
                "listing_type": "auction",
                "foreclosure": True,
                "auction_date": auction_date,
                "sqft": sqft,
            },
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with AuctionComAdapter() as adapter:
        urls = adapter.get_listing_urls()
        print(f"Found {len(urls)} listings")
        if urls:
            listing = adapter.extract_listing(urls[0])
            if listing:
                print(f"  Title: {listing.title}")
                print(f"  Price: {listing.price_raw}")
