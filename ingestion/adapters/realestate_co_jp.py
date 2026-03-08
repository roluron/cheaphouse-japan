"""
Real Estate Japan (realestate.co.jp) adapter.
Scrapes property listings from Japan's English-language real estate portal.

Target: Houses for sale under ¥10M.
This site is already in English — less translation needed.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.base_adapter import BaseAdapter
from ingestion.models import RawListing
from ingestion.utils import (
    parse_price_jpy,
    parse_area_sqm,
    extract_year_built,
    normalize_prefecture,
    clean_text,
    make_absolute_url,
)

logger = logging.getLogger(__name__)


class RealEstateCoJpAdapter(BaseAdapter):
    """Adapter for Real Estate Japan — realestate.co.jp (English)."""

    slug = "realestate-co-jp"
    base_url = "https://realestate.co.jp"

    # English-language search for houses under ¥10M
    # URL params updated 2026-03: price_max→max_price, property_type→building_type
    SEARCH_URL = (
        "https://realestate.co.jp/en/forsale/listing/"
        "?max_price=10000000&building_type=house&search=Search"
    )

    MAX_PAGES = 20

    def __init__(self):
        super().__init__()
        self.delay = 3
        # realestate.co.jp frequently times out; use longer timeout + Referer
        self.client.timeout = 60
        self.client.headers.update({
            "Referer": "https://www.google.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def get_listing_urls(self) -> list[str]:
        """Crawl paginated search results to collect listing detail URLs."""
        urls = []
        page = 1

        while page <= self.MAX_PAGES:
            search_url = f"{self.SEARCH_URL}&page={page}"
            logger.info(f"[{self.slug}] Fetching search page {page}...")

            try:
                html = self.fetch_page(search_url)
            except Exception as e:
                logger.warning(f"[{self.slug}] Search page {page} failed: {e}")
                if page == 1:
                    # First page timeout = site is down/blocking us
                    logger.error(f"[{self.slug}] Site unreachable. Aborting.")
                break

            soup = BeautifulSoup(html, "lxml")

            # realestate.co.jp listing links: /en/forsale/view/{id} or /forsale/listing/{id}
            found_on_page = 0
            for link in soup.select('a[href]'):
                href = link.get("href", "")
                if re.search(r'/forsale/(?:view|listing)/\d+', href):
                    full_url = make_absolute_url(self.base_url, href.split("?")[0])
                    if full_url not in urls:
                        urls.append(full_url)
                        found_on_page += 1

            logger.info(f"[{self.slug}] Page {page}: found {found_on_page} listings")

            if found_on_page == 0:
                break

            page += 1

        logger.info(f"[{self.slug}] Total listing URLs collected: {len(urls)}")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Parse a single listing detail page into a RawListing."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        id_match = re.search(r'/(?:view|listing)/(\d+)', url)
        listing_id = id_match.group(1) if id_match else None

        title = self._extract_title(soup)
        if not title:
            logger.warning(f"[{self.slug}] No title for {url}")
            return None

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=listing_id,
            title=title,
            description=self._extract_description(soup),
            price_jpy=self._extract_price(soup),
            price_raw=self._extract_price_raw(soup),
            prefecture=self._extract_prefecture(soup),
            city=self._extract_city(soup),
            address_raw=self._extract_address(soup),
            building_sqm=self._extract_area(soup, "building"),
            land_sqm=self._extract_area(soup, "land"),
            year_built=self._extract_year(soup),
            rooms=self._extract_layout(soup),
            nearest_station=self._extract_station(soup),
            station_distance=self._extract_station_distance(soup),
            image_urls=self._extract_images(soup),
            building_type="detached",
        )

    # ── Private extraction helpers ────────────────────────

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        h1 = soup.select_one("h1")
        if h1:
            return clean_text(h1.get_text())
        title_tag = soup.find("title")
        if title_tag:
            return clean_text(title_tag.get_text().split("|")[0].split("-")[0])
        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        for sel in [".listing-description", ".property-description",
                     ".description", '[class*="description"]']:
            el = soup.select_one(sel)
            if el and len(el.get_text(strip=True)) > 20:
                return clean_text(el.get_text())
        return None

    def _get_spec_value(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        """
        Extract from English spec tables.
        realestate.co.jp uses English labels like "Price", "Size", "Year Built".
        """
        label_lower = label.lower()
        # <th>/<td> pattern
        for th in soup.select("th, dt, .label, .spec-label"):
            if label_lower in th.get_text().lower():
                sibling = th.find_next("td") or th.find_next("dd") or th.find_next(".value")
                if sibling:
                    return clean_text(sibling.get_text())
        # <li> with label: value pattern
        for li in soup.select("li"):
            text = li.get_text()
            if label_lower in text.lower():
                # Try to get value after colon or in a child span
                val_el = li.select_one(".value, span:last-child")
                if val_el:
                    return clean_text(val_el.get_text())
                parts = text.split(":")
                if len(parts) > 1:
                    return clean_text(parts[1])
        return None

    def _extract_price(self, soup: BeautifulSoup) -> Optional[int]:
        # English price format: "¥4,800,000" or "4,800,000 JPY"
        price_text = self._get_spec_value(soup, "Price")
        if price_text:
            return parse_price_jpy(price_text)
        for sel in [".price", '[class*="price"]', '[class*="Price"]']:
            el = soup.select_one(sel)
            if el:
                return parse_price_jpy(el.get_text())
        return None

    def _extract_price_raw(self, soup: BeautifulSoup) -> Optional[str]:
        price_text = self._get_spec_value(soup, "Price")
        if price_text:
            return price_text
        for sel in [".price", '[class*="price"]']:
            el = soup.select_one(sel)
            if el:
                return clean_text(el.get_text())
        return None

    def _extract_prefecture(self, soup: BeautifulSoup) -> Optional[str]:
        # Try location/address fields
        for label in ["Prefecture", "Location", "Address"]:
            text = self._get_spec_value(soup, label)
            if text:
                pref = normalize_prefecture(text)
                if pref:
                    return pref
        # Try breadcrumbs
        for crumb in soup.select("li a, .breadcrumb a"):
            pref = normalize_prefecture(crumb.get_text())
            if pref:
                return pref
        return None

    def _extract_city(self, soup: BeautifulSoup) -> Optional[str]:
        for label in ["City", "Location", "Address"]:
            text = self._get_spec_value(soup, label)
            if text:
                # For English format: "Otaru, Hokkaido"
                parts = text.split(",")
                if len(parts) >= 2:
                    return clean_text(parts[0])
                return clean_text(text)
        return None

    def _extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        return self._get_spec_value(soup, "Address") or self._get_spec_value(soup, "Location")

    def _extract_area(self, soup: BeautifulSoup, area_type: str) -> Optional[float]:
        if area_type == "building":
            labels = ["Building Size", "Building Area", "Floor Area", "Size"]
        else:
            labels = ["Land Size", "Land Area", "Lot Size"]
        for label in labels:
            text = self._get_spec_value(soup, label)
            if text:
                return parse_area_sqm(text)
        return None

    def _extract_year(self, soup: BeautifulSoup) -> Optional[int]:
        text = self._get_spec_value(soup, "Year Built") or self._get_spec_value(soup, "Built")
        return extract_year_built(text) if text else None

    def _extract_layout(self, soup: BeautifulSoup) -> Optional[str]:
        text = self._get_spec_value(soup, "Layout") or self._get_spec_value(soup, "Rooms")
        if text:
            match = re.search(r'\d+[SLDK]+', text)
            return match.group(0) if match else clean_text(text)
        return None

    def _extract_station(self, soup: BeautifulSoup) -> Optional[str]:
        text = self._get_spec_value(soup, "Station") or self._get_spec_value(soup, "Access")
        if text:
            return clean_text(text.split(",")[0].split("(")[0].strip())
        return None

    def _extract_station_distance(self, soup: BeautifulSoup) -> Optional[str]:
        text = self._get_spec_value(soup, "Station") or self._get_spec_value(soup, "Access")
        if text:
            match = re.search(r'(\d+)\s*min', text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} min walk"
        return None

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        images = []
        for img in soup.select('img[src], img[data-src]'):
            src = img.get("data-src") or img.get("src", "")
            if not src or "noimage" in src.lower() or "icon" in src.lower() or "logo" in src.lower():
                continue
            if any(kw in src.lower() for kw in ["photo", "img", "image", "property", "listing", "upload"]):
                full = make_absolute_url(self.base_url, src)
                if full not in images:
                    images.append(full)
        return images[:20]
