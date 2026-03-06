"""
Pipeline Stage 3: Deduplication.

Computes fingerprints for properties and flags duplicate candidates.
Does NOT auto-merge — outputs a report for manual review.
"""

from __future__ import annotations

import hashlib
import logging

from ingestion.db import execute, get_cursor

logger = logging.getLogger(__name__)


def compute_fingerprints() -> int:
    """
    Compute dedupe fingerprints for all properties that don't have one.
    Returns count updated.
    """
    rows = execute(
        """
        SELECT id, prefecture, city, latitude, longitude,
               land_sqm, building_sqm, price_jpy
        FROM properties
        WHERE dedupe_fingerprint IS NULL
        """
    )

    if not rows:
        logger.info("No properties need fingerprinting.")
        return 0

    logger.info(f"Computing fingerprints for {len(rows)} properties...")
    count = 0

    with get_cursor(commit=True) as cur:
        for row in rows:
            fp = _make_fingerprint(row)
            cur.execute(
                "UPDATE properties SET dedupe_fingerprint = %s WHERE id = %s",
                (fp, row["id"]),
            )
            count += 1

    logger.info(f"Fingerprinted {count} properties.")
    return count


def find_duplicates() -> list[dict]:
    """
    Find properties with matching fingerprints.
    Returns list of duplicate clusters: [{"fingerprint": "...", "properties": [...]}]
    """
    clusters = execute(
        """
        SELECT dedupe_fingerprint, count(*) as cnt,
               array_agg(id) as ids
        FROM properties
        WHERE dedupe_fingerprint IS NOT NULL
        GROUP BY dedupe_fingerprint
        HAVING count(*) > 1
        ORDER BY count(*) DESC
        """
    )

    if not clusters:
        logger.info("No duplicates found.")
        return []

    # Enrich with property details for the report
    result = []
    for cluster in clusters:
        props = execute(
            """
            SELECT id, original_title, title_en, prefecture, city,
                   price_jpy, price_display, building_sqm, land_sqm,
                   primary_source_slug, original_url
            FROM properties
            WHERE id = ANY(%s)
            """,
            (cluster["ids"],),
        )
        result.append(
            {
                "fingerprint": cluster["dedupe_fingerprint"],
                "count": cluster["cnt"],
                "properties": props,
            }
        )

    logger.info(f"Found {len(result)} duplicate clusters.")
    return result


def print_duplicate_report(clusters: list[dict]):
    """Print a human-readable duplicate report."""
    if not clusters:
        print("\n  No duplicates found. ✓")
        return

    print(f"\n  Found {len(clusters)} duplicate clusters:\n")
    for i, cluster in enumerate(clusters, 1):
        print(f"  ── Cluster {i} (fingerprint: {cluster['fingerprint'][:12]}...) ──")
        for p in cluster["properties"]:
            title = p.get("title_en") or p.get("original_title") or "Untitled"
            price = p.get("price_display") or "No price"
            source = p.get("primary_source_slug", "?")
            print(f"    [{source}] {title[:50]}")
            print(f"      Price: {price}  |  {p.get('prefecture', '?')}, {p.get('city', '?')}")
            print(f"      URL: {p.get('original_url', '?')}")
        print()


def _make_fingerprint(row: dict) -> str:
    """
    Generate a deduplication fingerprint from property attributes.

    Primary: coordinates + sizes (when coordinates available)
    Fallback: prefecture + city + price bucket + size bucket
    """
    lat = row.get("latitude")
    lng = row.get("longitude")
    land = row.get("land_sqm") or 0
    building = row.get("building_sqm") or 0
    prefecture = (row.get("prefecture") or "").lower().strip()
    city = (row.get("city") or "").lower().strip()
    price = row.get("price_jpy") or 0

    if lat and lng:
        # Coordinate-based fingerprint (more precise)
        components = [
            str(round(lat, 3)),
            str(round(lng, 3)),
            str(round(land / 10) * 10),      # bucket to nearest 10 sqm
            str(round(building / 10) * 10),
        ]
    else:
        # Fallback: location + price + size based
        price_bucket = str(round(price / 500_000) * 500_000)  # 500K yen buckets
        components = [
            prefecture,
            city,
            price_bucket,
            str(round(building / 10) * 10),
            str(round(land / 10) * 10),
        ]

    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
