"""
Bukkenfan (bukkenfan.jp) adapter.
Scrapes curated, design-conscious properties from Japan's best property blog.

Bukkenfan features hand-picked properties with character — renovated machiya,
stylish apartments, unique rural homes. Think of it as the Instagram of
Japanese real estate.

API: GET /entries.json?for=list&limit=24
Returns JSON with entries containing: baika (price), menseki (area),
title, tags (location, type), url (original agency), image_url.

Note: Bukkenfan is a curated blog — the `url` field points to the
ORIGINAL real estate agency contact page. We use that as source_url.
Only scrape 売買 (for-sale) listings, skip 賃貸 (rentals).
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from ingestion.base_adapter import BaseAdapter
from ingestion.models import RawListing
from ingestion.utils import (
    parse_price_jpy,
    clean_text,
)

logger = logging.getLogger(__name__)

# Prefecture tags → canonical romanized
PREFECTURE_TAG_MAP = {
    "北海道": "Hokkaido", "青森": "Aomori", "岩手": "Iwate",
    "宮城": "Miyagi", "秋田": "Akita", "山形": "Yamagata",
    "福島": "Fukushima", "茨城": "Ibaraki", "栃木": "Tochigi",
    "群馬": "Gunma", "埼玉": "Saitama", "千葉": "Chiba",
    "東京": "Tokyo", "神奈川": "Kanagawa", "新潟": "Niigata",
    "富山": "Toyama", "石川": "Ishikawa", "福井": "Fukui",
    "山梨": "Yamanashi", "長野": "Nagano", "岐阜": "Gifu",
    "静岡": "Shizuoka", "愛知": "Aichi", "三重": "Mie",
    "滋賀": "Shiga", "京都": "Kyoto", "大阪": "Osaka",
    "兵庫": "Hyogo", "奈良": "Nara", "和歌山": "Wakayama",
    "鳥取": "Tottori", "島根": "Shimane", "岡山": "Okayama",
    "広島": "Hiroshima", "山口": "Yamaguchi", "徳島": "Tokushima",
    "香川": "Kagawa", "愛媛": "Ehime", "高知": "Kochi",
    "福岡": "Fukuoka", "佐賀": "Saga", "長崎": "Nagasaki",
    "熊本": "Kumamoto", "大分": "Oita", "宮崎": "Miyazaki",
    "鹿児島": "Kagoshima", "沖縄": "Okinawa",
}


class BukkenfanAdapter(BaseAdapter):
    """
    Adapter for Bukkenfan — bukkenfan.jp.

    Uses their JSON API to fetch curated property listings.
    Only scrapes 売買 (for-sale) listings, not rentals.
    source_url → the original agency URL, not bukkenfan.
    """

    slug = "bukkenfan"
    base_url = "https://bukkenfan.jp"
    API_URL = "https://bukkenfan.jp/entries.json"

    DEFAULT_LIMIT = 200  # Max entries per run
    PAGE_SIZE = 24

    def __init__(self):
        super().__init__()
        self.delay = 2
        self.client.headers.update({
            "Accept": "application/json",
            "Accept-Language": "ja,en-US;q=0.9",
        })

    def get_listing_urls(self) -> list[str]:
        """Not used — we use run() override with API pagination."""
        return []

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Not used."""
        return None

    def run(self) -> list[RawListing]:
        """Override: fetch from JSON API with pagination."""
        import time

        logger.info(f"[{self.slug}] Fetching from JSON API...")
        results: list[RawListing] = []
        seen_ids: set[str] = set()
        next_ref = None

        while len(results) < self.DEFAULT_LIMIT:
            params = f"?for=list&limit={self.PAGE_SIZE}"
            if next_ref:
                params += f"&ref={next_ref}"

            url = f"{self.API_URL}{params}"
            try:
                resp = self.client.get(url, follow_redirects=True)
                if resp.status_code != 200:
                    logger.warning(f"[{self.slug}] API {resp.status_code}")
                    break
                data = resp.json()
            except Exception as e:
                logger.error(f"[{self.slug}] API error: {e}")
                break

            entries = data.get("entries", [])
            next_ref = data.get("next_ref")

            if not entries:
                break

            for entry in entries:
                listing = self._parse_entry(entry)
                if listing:
                    eid = listing.source_listing_id or listing.source_url
                    if eid not in seen_ids:
                        seen_ids.add(eid)
                        results.append(listing)

            logger.info(
                f"[{self.slug}] Batch: +{len(entries)} entries, "
                f"{len(results)} for-sale total"
            )

            if not next_ref:
                break

            time.sleep(self.delay)

        logger.info(f"[{self.slug}] Done: {len(results)} for-sale listings")
        return results

    def _parse_entry(self, entry: dict) -> Optional[RawListing]:
        """Parse a single API entry into a RawListing."""
        entry_id = entry.get("entry_id", "")
        data = entry.get("data", {})

        tags = data.get("tags", [])

        # Only 売買 (for-sale), skip 賃貸 (rental)
        if "売買" not in tags:
            return None

        # Only 募集中 (currently listed), skip others
        if "募集中" not in tags:
            return None

        title = data.get("title", "")
        if not title:
            return None

        # Price (baika = 売価 = selling price)
        # Can be numeric (34800000) or Japanese ("9280万円", "980万")
        baika = data.get("baika")
        price_jpy = None
        if baika is not None:
            baika_str = str(baika)
            price_jpy = parse_price_jpy(baika_str)
            if price_jpy is None:
                # Fallback: try as plain number
                try:
                    price_jpy = int(float(baika_str.replace(",", "").replace("円", "")))
                except (ValueError, AttributeError):
                    price_jpy = None

        # Area parsing — menseki can be "土地79.33㎡／建物80.68㎡" or "84.2㎡"
        menseki = data.get("menseki", "")
        building_sqm = None
        land_sqm = None
        if menseki:
            land_m = re.search(r"土地\s*([\d.]+)\s*㎡", menseki)
            bld_m = re.search(r"建物\s*([\d.]+)\s*㎡", menseki)
            if land_m:
                try:
                    land_sqm = float(land_m.group(1))
                except ValueError:
                    pass
            if bld_m:
                try:
                    building_sqm = float(bld_m.group(1))
                except ValueError:
                    pass
            if not building_sqm and not land_sqm:
                single = re.search(r"([\d.]+)\s*㎡", menseki)
                if single:
                    try:
                        building_sqm = float(single.group(1))
                    except ValueError:
                        pass

        # Prefecture + city from tags
        prefecture, city = self._extract_location(tags)

        # Source URL — the original agency contact page
        source_url = data.get("url", "")
        if not source_url:
            # Fall back to bukkenfan entry page
            source_url = f"https://bukkenfan.jp/e/{entry_id}"

        # Images
        images = []
        for key in ["image_url", "thumbnail_image2_url", "thumbnail_image_url"]:
            img = data.get(key, "")
            if img and not img.startswith("data:"):
                # Strip fragment (#xywh=...)
                img = img.split("#")[0]
                if img not in images:
                    images.append(img)

        # Layout from tags (e.g., "3LDK")
        rooms = None
        for tag in tags:
            m = re.match(r"^\d+[SLDK]+$", tag)
            if m:
                rooms = m.group(0)
                break

        # Building type from tags
        building_type = "detached"
        if "マンション" in tags or "団地" in tags:
            building_type = "condo"

        return RawListing(
            source_slug=self.slug,
            source_url=source_url,
            source_listing_id=str(entry_id),
            title=clean_text(title),
            price_jpy=price_jpy,
            price_raw=f"¥{price_jpy:,}" if price_jpy else None,
            prefecture=prefecture,
            city=city,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            rooms=rooms,
            image_urls=images,
            building_type=building_type,
        )

    def _extract_location(self, tags: list[str]) -> tuple[Optional[str], Optional[str]]:
        """Extract prefecture and city from tags."""
        prefecture = None
        city = None

        for tag in tags:
            if tag in PREFECTURE_TAG_MAP:
                prefecture = PREFECTURE_TAG_MAP[tag]
            elif tag.endswith("市") or tag.endswith("区") or tag.endswith("町") or tag.endswith("村") or tag.endswith("郡"):
                if not city:
                    city = tag

        return prefecture, city
