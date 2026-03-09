"""
Pipeline Stage: Geocode properties using Nominatim (OpenStreetMap).

Adds city-level lat/lng for properties missing coordinates.
Rate limited to 1 request/second per Nominatim requirements.
"""

from __future__ import annotations

import logging
import time

import httpx

from ingestion.db import execute, execute_write

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "CheapHouseJapan/1.0 (property geocoder)"
RATE_LIMIT_SECONDS = 1.1  # slightly over 1s to be safe


def geocode_all(limit: int = 500) -> int:
    """
    Geocode properties that have prefecture/city but no lat/lng.
    Returns count of properties geocoded.
    """
    rows = execute(
        """
        SELECT id, prefecture, city, address_text
        FROM properties
        WHERE latitude IS NULL
          AND (prefecture IS NOT NULL OR city IS NOT NULL)
        ORDER BY quality_score DESC NULLS LAST
        LIMIT %s
        """,
        (limit,),
    )

    if not rows:
        logger.info("No properties need geocoding.")
        return 0

    logger.info(f"Geocoding {len(rows)} properties...")
    geocoded = 0

    for i, row in enumerate(rows):
        try:
            lat, lng = _geocode_property(row)
            if lat and lng:
                execute_write(
                    "UPDATE properties SET latitude = %s, longitude = %s WHERE id = %s",
                    (lat, lng, row["id"]),
                )
                geocoded += 1

            if (i + 1) % 25 == 0:
                logger.info(f"  Geocoded {i + 1}/{len(rows)} ({geocoded} found)")

            time.sleep(RATE_LIMIT_SECONDS)

        except Exception as e:
            logger.warning(f"Geocode failed for {row['id']}: {e}")
            time.sleep(RATE_LIMIT_SECONDS)

    logger.info(f"Geocoded {geocoded}/{len(rows)} properties.")
    return geocoded


def _geocode_property(row: dict) -> tuple:
    """
    Try to geocode a property using Nominatim.
    Returns (latitude, longitude) or (None, None).
    """
    # Build search queries in order of specificity
    queries = []

    # Try address + city + prefecture
    if row.get("address_text") and row.get("prefecture"):
        queries.append(f"{row['address_text']}, {row['prefecture']}, Japan")

    # Try city + prefecture
    if row.get("city") and row.get("prefecture"):
        queries.append(f"{row['city']}, {row['prefecture']}, Japan")

    # Try just prefecture
    if row.get("prefecture"):
        queries.append(f"{row['prefecture']}, Japan")

    for query in queries:
        try:
            response = httpx.get(
                NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "jp",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=10,
            )

            if response.status_code == 200:
                results = response.json()
                if results:
                    lat = float(results[0]["lat"])
                    lng = float(results[0]["lon"])
                    return lat, lng

        except Exception:
            continue

    return None, None
