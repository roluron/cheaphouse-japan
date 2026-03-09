"""
LIFULL HOME'S (homes.co.jp) adapter.
Scrapes cheap detached houses from Japan's major real estate portal.

Target: 中古一戸建て (used detached houses) under ¥10M.

Strategy: Extract data from search result cards (not detail pages) since
homes.co.jp uses AWS WAF that blocks detail page access with 202 responses.
Search pages return rich card data when proper Japanese browser headers are sent.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from bs4 import BeautifulSoup, Tag

from ingestion.base_adapter import BaseAdapter
from ingestion.config import PREFECTURE_MAP
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


class HomesCoJpAdapter(BaseAdapter):
    """
    Adapter for LIFULL HOME'S — homes.co.jp.

    Uses card-based extraction from search results since detail pages
    are behind AWS WAF (return 202 empty body).
    """

    slug = "homes-co-jp"
    base_url = "https://www.homes.co.jp"

    SEARCH_URL = (
        "https://www.homes.co.jp/kodate/chuko/list/"
        "?priceMax=1000&sort=new"
    )

    MAX_PAGES = 30
    MAX_WAF_RETRIES = 3

    def __init__(self):
        super().__init__()
        self.delay = 3
        # homes.co.jp requires Japanese browser headers to bypass WAF.
        # Without Accept-Language: ja, it returns a 202 with empty body.
        self.client.headers.update({
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1",
        })

    # ── Override: extract from search cards ──

    def get_listing_urls(self) -> list[str]:
        """Not used — we extract directly from cards."""
        return []

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Not used — data extracted from search result cards."""
        return None

    def _fetch_with_waf_retry(self, url: str) -> Optional[str]:
        """Fetch a URL, retrying on WAF 202 responses."""
        for attempt in range(self.MAX_WAF_RETRIES):
            try:
                resp = self.client.get(url)
                if resp.status_code == 200 and len(resp.text) > 1000:
                    return resp.text
                if resp.status_code == 202:
                    logger.warning(
                        f"[{self.slug}] WAF 202 on attempt {attempt + 1}, "
                        f"retrying in {5 * (attempt + 1)}s..."
                    )
                    time.sleep(5 * (attempt + 1))
                    continue
                logger.warning(
                    f"[{self.slug}] HTTP {resp.status_code}, body {len(resp.text)} bytes"
                )
                return None
            except Exception as e:
                logger.error(f"[{self.slug}] Fetch error: {e}")
                return None
        logger.error(f"[{self.slug}] WAF blocked after {self.MAX_WAF_RETRIES} retries")
        return None

    def run(self) -> list[RawListing]:
        """Override BaseAdapter.run() to scrape search result pages."""
        logger.info(f"[{self.slug}] Starting card-based scrape run...")
        results: list[RawListing] = []
        seen_ids: set[str] = set()
        consecutive_failures = 0

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{self.SEARCH_URL}&page={page}"
            logger.info(f"[{self.slug}] Page {page}...")

            html = self._fetch_with_waf_retry(url)
            if not html:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    logger.error(f"[{self.slug}] 3 consecutive failures, stopping.")
                    break
                continue

            consecutive_failures = 0
            soup = BeautifulSoup(html, "lxml")

            # Find listing cards — look for links to detail pages
            cards = self._find_listing_cards(soup)
            if not cards:
                logger.info(f"[{self.slug}] No more cards on page {page}.")
                break

            new_on_page = 0
            for card_data in cards:
                listing = self._build_listing(card_data)
                if listing:
                    lid = listing.source_listing_id or listing.source_url
                    if lid not in seen_ids:
                        seen_ids.add(lid)
                        results.append(listing)
                        new_on_page += 1

            logger.info(
                f"[{self.slug}] Page {page}: +{new_on_page} ({len(results)} total)"
            )

            if new_on_page == 0:
                break

            time.sleep(self.delay)

        logger.info(f"[{self.slug}] Run complete: {len(results)} listings.")
        return results

    def _find_listing_cards(self, soup: BeautifulSoup) -> list[dict]:
        """
        Extract structured data from search result cards.
        homes.co.jp renders cards with links to /kodate/b-XXXXX/
        and nearby spec text.
        """
        cards_data: list[dict] = []

        # Find all detail links
        detail_links = soup.select('a[href*="/kodate/b-"]')

        # Group links by listing ID (multiple links can point to same listing)
        seen_listing_ids: set[str] = set()

        for link in detail_links:
            href = link.get("href", "")
            id_match = re.search(r'b-(\d+)', href)
            if not id_match:
                continue

            listing_id = id_match.group(1)
            if listing_id in seen_listing_ids:
                continue
            seen_listing_ids.add(listing_id)

            # Go up to find the card container
            card_el = link
            for _ in range(10):
                parent = card_el.parent
                if parent is None or parent.name in ("body", "html", "[document]"):
                    break
                card_el = parent
                # Check if this parent has enough content to be the card
                text = card_el.get_text()
                if "万円" in text and len(text) > 100:
                    break

            detail_url = make_absolute_url(
                self.base_url, href.split("?")[0]
            )

            # Extract data from the card area
            card_text = card_el.get_text(separator="\n")
            card_data = {
                "url": detail_url,
                "listing_id": listing_id,
                "element": card_el,
                "text": card_text,
            }
            cards_data.append(card_data)

        return cards_data

    def _build_listing(self, card: dict) -> Optional[RawListing]:
        """Build a RawListing from extracted card data."""
        el: Tag = card["element"]
        text: str = card["text"]

        # Title: usually the link text or prominent heading
        title = None
        for sel in ["h2", "h3", ".title", "[class*='name']"]:
            t = el.select_one(sel)
            if t and len(t.get_text(strip=True)) > 5:
                title = clean_text(t.get_text())
                break
        if not title:
            # Build from address/price info
            title = clean_text(text.split("\n")[0][:60])
        if not title:
            return None

        # Price
        price_jpy = None
        price_raw = None
        price_match = re.search(r'(\d[\d,]+)\s*万円', text)
        if price_match:
            price_raw = f"{price_match.group(1)}万円"
            price_jpy = parse_price_jpy(price_raw)

        # Address → prefecture + city
        prefecture = None
        city = None
        address = None
        for line in text.split("\n"):
            for kanji in PREFECTURE_MAP:
                if kanji in line:
                    address = clean_text(line)
                    prefecture = PREFECTURE_MAP[kanji]
                    city_match = re.search(
                        kanji + r'(.+?[市町村区郡])', line
                    )
                    if city_match:
                        city = clean_text(city_match.group(1))
                    break
            if prefecture:
                break

        # Areas
        building_sqm = None
        land_sqm = None
        bld_match = re.search(r'建物[面積:：\s]*(\d+[\d.]*)\s*m', text)
        if bld_match:
            building_sqm = float(bld_match.group(1))
        land_match = re.search(r'土地[面積:：\s]*(\d+[\d.]*)\s*m', text)
        if land_match:
            land_sqm = float(land_match.group(1))

        # Year built
        year_built = None
        year_match = re.search(r'(\d{4})年', text)
        if year_match:
            y = int(year_match.group(1))
            if 1900 <= y <= 2030:
                year_built = y

        # Layout
        rooms = None
        rooms_match = re.search(r'(\d+[SLDK]+)', text)
        if rooms_match:
            rooms = rooms_match.group(1)

        # Station
        station = None
        distance = None
        st_match = re.search(r'[「＜]?([^」＞\n]+駅)[」＞]?', text)
        if st_match:
            station = st_match.group(1)
        dist_match = re.search(r'徒歩\s*(\d+)\s*分', text)
        if dist_match:
            distance = f"{dist_match.group(1)} min walk"

        # Images
        images = []
        for img in el.select("img[src], img[data-src], img[data-original]"):
            src = img.get("data-original") or img.get("data-src") or img.get("src", "")
            if not src or src.startswith("data:") or "noimage" in src.lower():
                continue
            if "icon" in src.lower() or "logo" in src.lower():
                continue
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)

        return RawListing(
            source_slug=self.slug,
            source_url=card["url"],
            source_listing_id=card["listing_id"],
            title=title,
            price_jpy=price_jpy,
            price_raw=price_raw,
            prefecture=prefecture,
            city=city,
            address_raw=address,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            year_built=year_built,
            rooms=rooms,
            nearest_station=station,
            station_distance=distance,
            image_urls=images[:20],
            building_type="detached",
        )
