"""
Akiya Mart (akiya-mart.com) adapter.
Scrapes Japanese akiya listings via Akiya Mart's internal API.

IMPORTANT: Akiya Mart is an aggregator. Their listings come from major
Japanese portals (Suumo, athome, homes.co.jp, etc.). Each listing has
an original `url` field pointing to the source portal. We use THAT URL
as our source_url — we never redirect users to akiya-mart.com.

Discovery: XML sitemaps → listing IDs
Extraction: JSON API at /listings/id/{listing_id} — returns all data
including the original source URL, price, areas, coordinates, images.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from ingestion.base_adapter import BaseAdapter
from ingestion.models import RawListing
from ingestion.utils import clean_text

logger = logging.getLogger(__name__)


# English prefecture → canonical romanized
PREFECTURE_EN_MAP = {
    "hokkaido": "Hokkaido", "aomori": "Aomori", "iwate": "Iwate",
    "miyagi": "Miyagi", "akita": "Akita", "yamagata": "Yamagata",
    "fukushima": "Fukushima", "ibaraki": "Ibaraki", "tochigi": "Tochigi",
    "gunma": "Gunma", "saitama": "Saitama", "chiba": "Chiba",
    "tokyo": "Tokyo", "kanagawa": "Kanagawa", "niigata": "Niigata",
    "toyama": "Toyama", "ishikawa": "Ishikawa", "fukui": "Fukui",
    "yamanashi": "Yamanashi", "nagano": "Nagano", "gifu": "Gifu",
    "shizuoka": "Shizuoka", "aichi": "Aichi", "mie": "Mie",
    "shiga": "Shiga", "kyoto": "Kyoto", "osaka": "Osaka",
    "hyogo": "Hyogo", "nara": "Nara", "wakayama": "Wakayama",
    "tottori": "Tottori", "shimane": "Shimane", "okayama": "Okayama",
    "hiroshima": "Hiroshima", "yamaguchi": "Yamaguchi",
    "tokushima": "Tokushima", "kagawa": "Kagawa", "ehime": "Ehime",
    "kochi": "Kochi", "fukuoka": "Fukuoka", "saga": "Saga",
    "nagasaki": "Nagasaki", "kumamoto": "Kumamoto", "oita": "Oita",
    "miyazaki": "Miyazaki", "kagoshima": "Kagoshima", "okinawa": "Okinawa",
}


class AkiyaMartAdapter(BaseAdapter):
    """
    Adapter for Akiya Mart — akiya-mart.com.

    Uses the internal JSON API (/listings/id/{id}) instead of scraping HTML.
    The API returns all property data including the ORIGINAL source URL
    from the Japanese real estate portal (Suumo, athome, etc.).

    source_url → the ORIGINAL Japanese portal URL, NOT akiya-mart.
    """

    slug = "akiya-mart"
    base_url = "https://app.akiya-mart.com"

    SITEMAP_INDEX = "https://www.akiya-mart.com/sitemap.xml"
    API_URL = "https://app.akiya-mart.com/listings/id/{listing_id}"

    # Limit per run (680K total is way too many)
    DEFAULT_URL_LIMIT = 500
    MAX_SITEMAPS = 2  # Only process last 2 sitemaps (newest listings)

    def __init__(self):
        super().__init__()
        self.delay = 1  # API is fast, 1s delay is polite enough

    def get_listing_urls(self) -> list[str]:
        """Fetch listing IDs from sitemaps. Returns listing URLs."""
        logger.info(f"[{self.slug}] Fetching sitemap index...")

        try:
            index_html = self.fetch_page(self.SITEMAP_INDEX)
        except Exception as e:
            logger.error(f"[{self.slug}] Sitemap fetch failed: {e}")
            return []

        # Get listing sitemap URLs (they're numbered 01-17)
        sitemap_urls = re.findall(r"<loc>(.*?)</loc>", index_html)
        listing_sitemaps = sorted(
            [u for u in sitemap_urls if "sitemap-listings" in u]
        )
        logger.info(f"[{self.slug}] Found {len(listing_sitemaps)} listing sitemaps")

        # Take from the LAST sitemaps (newest listings)
        urls: list[str] = []
        for sitemap_url in listing_sitemaps[-self.MAX_SITEMAPS:]:
            try:
                sitemap_html = self.fetch_page(sitemap_url)
                batch = re.findall(r"<loc>(.*?)</loc>", sitemap_html)
                # Take from the END (newest)
                urls.extend(batch[-self.DEFAULT_URL_LIMIT:])
                logger.info(
                    f"[{self.slug}] {sitemap_url.split('/')[-1]}: "
                    f"{len(batch)} total, took last {min(len(batch), self.DEFAULT_URL_LIMIT)}"
                )
            except Exception as e:
                logger.warning(f"[{self.slug}] Sitemap error: {e}")

            if len(urls) >= self.DEFAULT_URL_LIMIT:
                break

        final = urls[-self.DEFAULT_URL_LIMIT:]
        logger.info(f"[{self.slug}] Collected {len(final)} listing URLs")
        return final

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """
        Extract listing data via the JSON API.
        Returns the ORIGINAL source URL from the Japanese portal, not akiya-mart.
        """
        # Extract listing ID from URL
        id_match = re.search(r"/listing/(\d+)", url)
        if not id_match:
            return None
        listing_id = id_match.group(1)

        # Fetch from JSON API
        api_url = self.API_URL.format(listing_id=listing_id)
        try:
            resp = self.client.get(api_url, follow_redirects=True)
            if resp.status_code != 200:
                logger.warning(f"[{self.slug}] API {resp.status_code} for {listing_id}")
                return None
            data = resp.json()
        except Exception as e:
            logger.error(f"[{self.slug}] API error for {listing_id}: {e}")
            return None

        results = data.get("results", {})
        if not results or not isinstance(results, dict):
            return None

        # Skip inactive/hidden listings
        if not results.get("is_active", True):
            return None

        # The ORIGINAL source URL from the Japanese portal
        source_url = results.get("url", "")
        if not source_url:
            # If no original URL, fall back to akiya-mart URL
            source_url = url

        # Price
        price_yen = results.get("price_yen")

        # Prefecture
        pref_raw = results.get("prefecture", "")
        prefecture = PREFECTURE_EN_MAP.get(
            pref_raw.lower(), pref_raw.capitalize() if pref_raw else None
        )

        # Address (Japanese)
        address = results.get("address", "")

        # City — extract from translated address or Japanese address
        city = self._extract_city(results.get("translated_address", ""), address)

        # Title — use translated address or build from data
        title = results.get("translated_address") or clean_text(address) or None
        if not title:
            return None

        # Areas
        building_sqm = results.get("building_area")
        land_sqm = results.get("land_area")
        if building_sqm:
            building_sqm = round(float(building_sqm), 1)
        if land_sqm:
            land_sqm = round(float(land_sqm), 1)

        # Year
        year_built = results.get("construction_year")
        if year_built:
            year_built = int(year_built)
            if year_built < 1900 or year_built > 2030:
                year_built = None

        # Layout (from madori fields)
        rooms = None
        room_count = results.get("madori_other_rooms_count")
        main_rank = results.get("madori_main_room_size_rank")
        if room_count:
            rooms = f"{room_count}+"

        # Station
        station = results.get("station_name")
        station_distance = None
        dist_m = results.get("station_distance")
        if dist_m:
            mins = round(int(dist_m) / 80)  # 80m/min walking speed
            station_distance = f"{mins} min walk"

        # Images — from the original portals (suumo CDN, etc.)
        image_urls = results.get("image_urls", []) or []
        # Also check CDN photos
        cdn_photos = results.get("cdn_photos", []) or []
        for cdn in cdn_photos:
            cdn_url = f"https://images.akiya-mart.com/{cdn}"
            if cdn_url not in image_urls:
                image_urls.append(cdn_url)

        # Description (already translated by their LLM)
        description = results.get("llm_description") or ""
        if isinstance(results.get("description"), list):
            jp_desc = " ".join(results["description"])
            if not description:
                description = jp_desc

        # Structure
        structure_code = results.get("building_structure_code")
        structure = {1: "wood", 2: "steel", 3: "rc", 4: "src"}.get(
            structure_code
        )

        # Coordinates
        lat = results.get("lat")
        lon = results.get("lon")

        return RawListing(
            source_slug=self.slug,
            source_url=source_url,  # ORIGINAL portal URL, NOT akiya-mart!
            source_listing_id=listing_id,
            title=title,
            description=description if description else None,
            price_jpy=int(price_yen) if price_yen else None,
            price_raw=f"¥{price_yen:,}" if price_yen else None,
            prefecture=prefecture,
            city=city,
            address_raw=clean_text(address) if address else None,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            year_built=year_built,
            rooms=rooms,
            nearest_station=station,
            station_distance=station_distance,
            image_urls=image_urls[:20],
            building_type="detached" if not results.get("is_condo") else "condo",
            structure=structure,
            latitude=lat,
            longitude=lon,
        )

    def _extract_city(self, translated: str, japanese: str) -> Optional[str]:
        """Extract city from address strings."""
        if translated:
            # "Shimonoseki City, Yamaguchi Prefecture"
            city_match = re.search(
                r"(\w+(?:\s\w+)?)\s+(?:City|Town|Village)", translated, re.IGNORECASE
            )
            if city_match:
                return city_match.group(1)

        if japanese:
            # Japanese: 山口県下関市大字内日下
            city_match = re.search(r"[都道府県](.+?[市町村区郡])", japanese)
            if city_match:
                return clean_text(city_match.group(1))

        return None
