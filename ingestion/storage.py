"""
Storage layer: writes RawListing records to the database.
Upserts on (source_slug, source_listing_id) to avoid duplicates from the same source.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from ingestion.db import get_cursor
from ingestion.models import RawListing

logger = logging.getLogger(__name__)


def save_raw_listings(listings: list[RawListing]) -> tuple[int, int]:
    """
    Save a batch of raw listings to the database.
    Upserts: if source_slug + source_listing_id already exists, update it.
    Returns (inserted_count, updated_count).
    """
    if not listings:
        return 0, 0

    inserted = 0
    updated = 0

    with get_cursor(commit=True) as cur:
        for listing in listings:
            # Build source_listing_id fallback from URL if not provided
            source_listing_id = listing.source_listing_id or listing.source_url

            cur.execute(
                """
                INSERT INTO raw_listings (
                    source_slug, source_listing_id, source_url,
                    country,
                    title, description,
                    price_raw, price_jpy,
                    prefecture, city, address_raw,
                    latitude, longitude,
                    land_sqm, building_sqm, year_built,
                    building_type, structure, rooms, floors,
                    condition_notes,
                    nearest_station, station_distance,
                    image_urls, raw_data,
                    fetched_at, processing_status
                ) VALUES (
                    %(source_slug)s, %(source_listing_id)s, %(source_url)s,
                    %(country)s,
                    %(title)s, %(description)s,
                    %(price_raw)s, %(price_jpy)s,
                    %(prefecture)s, %(city)s, %(address_raw)s,
                    %(latitude)s, %(longitude)s,
                    %(land_sqm)s, %(building_sqm)s, %(year_built)s,
                    %(building_type)s, %(structure)s, %(rooms)s, %(floors)s,
                    %(condition_notes)s,
                    %(nearest_station)s, %(station_distance)s,
                    %(image_urls)s, %(raw_data)s,
                    %(fetched_at)s, 'pending'
                )
                ON CONFLICT (source_slug, source_listing_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    price_raw = EXCLUDED.price_raw,
                    price_jpy = EXCLUDED.price_jpy,
                    prefecture = EXCLUDED.prefecture,
                    city = EXCLUDED.city,
                    address_raw = EXCLUDED.address_raw,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    land_sqm = EXCLUDED.land_sqm,
                    building_sqm = EXCLUDED.building_sqm,
                    year_built = EXCLUDED.year_built,
                    image_urls = EXCLUDED.image_urls,
                    raw_data = EXCLUDED.raw_data,
                    fetched_at = EXCLUDED.fetched_at,
                    processing_status = 'pending',
                    updated_at = now()
                RETURNING (xmax = 0) AS is_insert
                """,
                {
                    "source_slug": listing.source_slug,
                    "source_listing_id": source_listing_id,
                    "source_url": listing.source_url,
                    "country": listing.country,
                    "title": listing.title,
                    "description": listing.description,
                    "price_raw": listing.price_raw,
                    "price_jpy": listing.price_jpy,
                    "prefecture": listing.prefecture,
                    "city": listing.city,
                    "address_raw": listing.address_raw,
                    "latitude": listing.latitude,
                    "longitude": listing.longitude,
                    "land_sqm": listing.land_sqm,
                    "building_sqm": listing.building_sqm,
                    "year_built": listing.year_built,
                    "building_type": listing.building_type,
                    "structure": listing.structure,
                    "rooms": listing.rooms,
                    "floors": listing.floors,
                    "condition_notes": listing.condition_notes,
                    "nearest_station": listing.nearest_station,
                    "station_distance": listing.station_distance,
                    "image_urls": listing.image_urls,
                    "raw_data": json.dumps(listing.raw_data)
                    if listing.raw_data
                    else None,
                    "fetched_at": listing.fetched_at,
                },
            )
            row = cur.fetchone()
            if row and row["is_insert"]:
                inserted += 1
            else:
                updated += 1

    logger.info(f"Saved {inserted} new, {updated} updated raw listings.")
    return inserted, updated


def update_source_run(
    source_slug: str,
    status: str,
    listings_found: int,
    errors: int = 0,
    duration_ms: int = 0,
):
    """Record a scrape run result."""
    with get_cursor(commit=True) as cur:
        # Insert run record
        cur.execute(
            """
            INSERT INTO scrape_runs (
                source_slug, status, listings_found, errors, duration_ms, run_at
            ) VALUES (%(slug)s, %(status)s, %(found)s, %(errors)s, %(duration)s, now())
            """,
            {
                "slug": source_slug,
                "status": status,
                "found": listings_found,
                "errors": errors,
                "duration": duration_ms,
            },
        )
        # Update source last_run
        cur.execute(
            """
            UPDATE sources SET
                last_run_at = now(),
                last_run_status = %(status)s,
                last_run_count = %(count)s,
                updated_at = now()
            WHERE slug = %(slug)s
            """,
            {"slug": source_slug, "status": status, "count": listings_found},
        )
