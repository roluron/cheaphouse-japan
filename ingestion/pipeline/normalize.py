"""
Pipeline Stage 1: Normalize raw listings into clean property records.

Reads from raw_listings (processing_status = 'pending'),
writes to properties table as 'draft' status.
"""

from __future__ import annotations

import logging
from typing import Optional

from ingestion.config import PREFECTURE_MAP, REGION_MAP
from ingestion.db import execute, get_cursor
from ingestion.utils import (
    clean_text,
    normalize_prefecture,
    parse_area_sqm,
    parse_price_jpy,
    extract_year_built,
)

logger = logging.getLogger(__name__)

# ── USD/JPY conversion rate (update periodically) ───────
USD_JPY_RATE = 150


def normalize_all(limit: int = 500) -> int:
    """
    Process all pending raw listings into normalized property records.
    Returns count of records processed.
    """
    rows = execute(
        """
        SELECT * FROM raw_listings
        WHERE processing_status = 'pending'
        ORDER BY created_at ASC
        LIMIT %s
        """,
        (limit,),
    )

    if not rows:
        logger.info("No pending raw listings to normalize.")
        return 0

    logger.info(f"Normalizing {len(rows)} raw listings...")
    processed = 0

    for row in rows:
        try:
            _normalize_one(row)
            processed += 1
        except Exception as e:
            logger.error(
                f"Error normalizing raw_listing {row['id']}: {e}"
            )
            _mark_raw_status(row["id"], "error")

    logger.info(f"Normalized {processed}/{len(rows)} raw listings.")
    return processed


def _normalize_one(raw: dict):
    """Normalize a single raw listing into a property record."""

    # ── Price normalization ───────────────────────────────
    price_jpy = raw.get("price_jpy")
    if not price_jpy and raw.get("price_raw"):
        price_jpy = parse_price_jpy(raw["price_raw"])

    price_usd = int(price_jpy / USD_JPY_RATE) if price_jpy else None
    price_display = None
    if price_jpy:
        if price_jpy >= 10_000:
            man = price_jpy / 10_000
            price_display = f"¥{price_jpy:,} ({man:.0f}万円, ~${price_usd:,})"
        else:
            price_display = f"¥{price_jpy:,} (~${price_usd:,})"

    # ── Location normalization ───────────────────────────
    prefecture = normalize_prefecture(raw.get("prefecture") or "")
    city = clean_text(raw.get("city"))
    region = REGION_MAP.get(prefecture) if prefecture else None

    # ── Area normalization ───────────────────────────────
    land_sqm = raw.get("land_sqm")
    building_sqm = raw.get("building_sqm")

    # ── Year built ───────────────────────────────────────
    year_built = raw.get("year_built")

    # ── Condition rating from notes ──────────────────────
    condition_notes = clean_text(raw.get("condition_notes"))
    condition_rating = _infer_condition(condition_notes, year_built)

    # ── Renovation estimate ──────────────────────────────
    renovation_estimate = _infer_renovation(condition_rating, year_built)

    # ── Images ───────────────────────────────────────────
    image_urls = raw.get("image_urls") or []
    images_json = [
        {"url": url, "caption": None, "order": i}
        for i, url in enumerate(image_urls)
    ]
    thumbnail_url = image_urls[0] if image_urls else None

    # ── Source attribution ────────────────────────────────
    source_listing_ids = [
        {
            "source": raw["source_slug"],
            "id": raw.get("source_listing_id"),
            "url": raw["source_url"],
        }
    ]

    # ── Country ──────────────────────────────────────────
    country = raw.get("country") or "japan"

    # ── Slug generation ──────────────────────────────────
    import re, uuid
    title_for_slug = raw.get("title") or f"property-{uuid.uuid4().hex[:8]}"
    slug = re.sub(r'[^a-z0-9\s-]', '', title_for_slug.lower())
    slug = re.sub(r'\s+', '-', slug).strip('-')[:80]
    slug = f"{slug}-{uuid.uuid4().hex[:8]}"

    # ── Insert into properties ───────────────────────────
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO properties (
                primary_source_slug, source_listing_ids, original_url,
                original_title, original_description,
                price_jpy, price_usd, price_display,
                prefecture, city, address_text,
                latitude, longitude, region,
                land_sqm, building_sqm, year_built,
                building_type, structure, floors, rooms,
                condition_rating, condition_notes,
                renovation_estimate,
                nearest_station, station_distance,
                images, thumbnail_url,
                listing_status, admin_status, is_published,
                first_seen_at, last_seen_at, last_checked_at,
                freshness_label, country, slug
            ) VALUES (
                %(source_slug)s, %(source_ids)s::jsonb, %(url)s,
                %(title)s, %(description)s,
                %(price_jpy)s, %(price_usd)s, %(price_display)s,
                %(prefecture)s, %(city)s, %(address)s,
                %(lat)s, %(lng)s, %(region)s,
                %(land)s, %(building)s, %(year)s,
                %(btype)s, %(structure)s, %(floors)s, %(rooms)s,
                %(condition_rating)s, %(condition_notes)s,
                %(renovation)s,
                %(station)s, %(station_dist)s,
                %(images)s::jsonb, %(thumb)s,
                'active', 'approved', true,
                %(fetched)s, %(fetched)s, %(fetched)s,
                'new', %(country)s, %(slug)s
            )
            ON CONFLICT DO NOTHING
            RETURNING id
            """,
            {
                "source_slug": raw["source_slug"],
                "source_ids": __import__("json").dumps(source_listing_ids),
                "url": raw["source_url"],
                "title": raw.get("title"),
                "description": raw.get("description"),
                "price_jpy": price_jpy,
                "price_usd": price_usd,
                "price_display": price_display,
                "prefecture": prefecture,
                "city": city,
                "address": clean_text(raw.get("address_raw")),
                "lat": raw.get("latitude"),
                "lng": raw.get("longitude"),
                "region": region,
                "land": land_sqm,
                "building": building_sqm,
                "year": year_built,
                "btype": raw.get("building_type"),
                "structure": raw.get("structure"),
                "floors": raw.get("floors"),
                "rooms": raw.get("rooms"),
                "condition_rating": condition_rating,
                "condition_notes": condition_notes,
                "renovation": renovation_estimate,
                "station": raw.get("nearest_station"),
                "station_dist": raw.get("station_distance"),
                "images": __import__("json").dumps(images_json),
                "thumb": thumbnail_url,
                "fetched": raw.get("fetched_at"),
                "country": country,
                "slug": slug,
            },
        )

    _mark_raw_status(raw["id"], "done")


def _infer_condition(
    notes: Optional[str], year_built: Optional[int]
) -> str:
    """Infer condition rating from notes and year built."""
    if notes:
        notes_lower = notes.lower()
        if any(w in notes_lower for w in ["excellent", "good condition", "well maintained", "renovated", "reform"]):
            return "good"
        if any(w in notes_lower for w in ["needs work", "repair", "damaged", "老朽"]):
            return "needs_work"
        if any(w in notes_lower for w in ["significant", "major", "rebuild", "demolish"]):
            return "significant_renovation"

    if year_built:
        if year_built >= 2000:
            return "fair"
        if year_built >= 1980:
            return "needs_work"
        return "significant_renovation"

    return "unknown"


def _infer_renovation(
    condition: str, year_built: Optional[int]
) -> str:
    """Infer renovation estimate category."""
    mapping = {
        "good": "light",
        "fair": "light",
        "needs_work": "moderate",
        "significant_renovation": "heavy",
        "unknown": "unknown",
    }
    return mapping.get(condition, "unknown")


def _mark_raw_status(raw_id: str, status: str):
    """Update processing_status on a raw_listing."""
    from ingestion.db import execute_write

    execute_write(
        "UPDATE raw_listings SET processing_status = %s, updated_at = now() WHERE id = %s",
        (status, raw_id),
    )
