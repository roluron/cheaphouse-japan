"""
Pipeline Stage 4: Hazard enrichment.

MVP approach — simplified lookup without PostGIS:
  - Pre-built hazard zone data stored as grid-cell lookups
  - For each property with coordinates, look up flood/landslide/tsunami risk
  - For properties without coordinates, mark as "unknown"

Data sources (manually prepared):
  - Flood: Disaportal (https://disaportal.gsi.go.jp/)
  - Landslide: Prefectural sediment disaster maps
  - Tsunami: Coastal proximity + elevation (simplified)

This module also supports a simulated/demo mode using rule-based heuristics
when actual GIS data hasn't been loaded yet.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from ingestion.db import execute, get_cursor

logger = logging.getLogger(__name__)

# ── When real GIS data is loaded, query the hazard_zones table.
#    Until then, use heuristic estimates for MVP demo. ────────


def enrich_hazard_all(limit: int = 500, use_heuristics: bool = True) -> int:
    """
    Attach hazard scores to all properties that don't have them.
    Returns count processed.
    """
    rows = execute(
        """
        SELECT id, latitude, longitude, prefecture, city, address_text
        FROM properties
        WHERE hazard_scores = '{}'::jsonb OR hazard_scores IS NULL
        LIMIT %s
        """,
        (limit,),
    )

    if not rows:
        logger.info("No properties need hazard enrichment.")
        return 0

    logger.info(f"Enriching hazard data for {len(rows)} properties...")
    count = 0

    # Check if we have real hazard zone data
    has_real_data = _has_hazard_zone_data()

    with get_cursor(commit=True) as cur:
        for row in rows:
            try:
                if has_real_data and row.get("latitude") and row.get("longitude"):
                    scores = _lookup_hazard_zones(
                        row["latitude"], row["longitude"]
                    )
                elif use_heuristics:
                    scores = _heuristic_hazard(row)
                else:
                    scores = _unknown_hazard()

                cur.execute(
                    "UPDATE properties SET hazard_scores = %s::jsonb, updated_at = now() WHERE id = %s",
                    (json.dumps(scores), row["id"]),
                )
                count += 1
            except Exception as e:
                logger.error(f"Error enriching hazard for {row['id']}: {e}")

    logger.info(f"Enriched hazard data for {count} properties.")
    return count


def _has_hazard_zone_data() -> bool:
    """Check if the hazard_zones table exists and has data."""
    try:
        result = execute(
            "SELECT count(*) as cnt FROM information_schema.tables WHERE table_name = 'hazard_zones'"
        )
        if result and result[0]["cnt"] > 0:
            data = execute("SELECT count(*) as cnt FROM hazard_zones")
            return data[0]["cnt"] > 0
    except Exception:
        pass
    return False


def _lookup_hazard_zones(lat: float, lng: float) -> dict:
    """
    Look up real hazard zone data for a coordinate.
    Uses a simplified grid-cell approach (no PostGIS required):
    Round coordinates to nearest 0.005 (~500m) and match.
    """
    grid_lat = round(lat / 0.005) * 0.005
    grid_lng = round(lng / 0.005) * 0.005

    scores = {}
    for hazard_type in ["flood", "landslide", "tsunami"]:
        result = execute(
            """
            SELECT risk_level, depth_info, source, source_url
            FROM hazard_zones
            WHERE hazard_type = %s
              AND ABS(grid_lat - %s) < 0.003
              AND ABS(grid_lng - %s) < 0.003
            ORDER BY risk_level DESC
            LIMIT 1
            """,
            (hazard_type, grid_lat, grid_lng),
        )

        if result:
            row = result[0]
            scores[hazard_type] = {
                "level": row["risk_level"],
                "depth_info": row.get("depth_info"),
                "confidence": "medium",
                "source": row.get("source", "hazard_zones_table"),
                "source_url": row.get("source_url"),
                "last_updated": None,
                "summary": _hazard_summary(hazard_type, row["risk_level"]),
            }
        else:
            scores[hazard_type] = _no_data_entry(hazard_type)

    return scores


def _heuristic_hazard(row: dict) -> dict:
    """
    Generate heuristic hazard estimates when real data isn't available.
    Based on prefecture-level generalizations — clearly marked as estimates.

    This is a placeholder to make the product functional before GIS data is loaded.
    """
    prefecture = (row.get("prefecture") or "").lower()

    # Coastal prefectures with higher tsunami risk
    coastal_high = {"okinawa", "miyagi", "iwate", "kochi", "wakayama", "mie", "shizuoka", "chiba"}
    # Mountainous prefectures with higher landslide risk
    mountain_high = {"nagano", "gifu", "nara", "wakayama", "ehime", "kochi", "shimane", "tottori"}
    # River-plain prefectures with higher flood risk
    flood_high = {"niigata", "akita", "saga", "kumamoto", "okayama", "hiroshima"}

    flood_level = "moderate" if prefecture in flood_high else "low"
    landslide_level = "moderate" if prefecture in mountain_high else "low"
    tsunami_level = "moderate" if prefecture in coastal_high else "none"

    return {
        "flood": {
            "level": flood_level,
            "depth_info": None,
            "confidence": "low",
            "source": "prefecture_heuristic",
            "source_url": None,
            "last_updated": None,
            "summary": f"Estimated {flood_level} flood risk based on prefecture-level data. Verify with local hazard maps before purchasing.",
        },
        "landslide": {
            "level": landslide_level,
            "depth_info": None,
            "confidence": "low",
            "source": "prefecture_heuristic",
            "source_url": None,
            "last_updated": None,
            "summary": f"Estimated {landslide_level} landslide risk based on prefecture-level data. Verify with local hazard maps.",
        },
        "tsunami": {
            "level": tsunami_level,
            "depth_info": None,
            "confidence": "low",
            "source": "prefecture_heuristic",
            "source_url": None,
            "last_updated": None,
            "summary": f"Estimated {tsunami_level} tsunami risk based on coastal proximity. Verify with local authorities.",
        },
    }


def _unknown_hazard() -> dict:
    """Return unknown hazard scores."""
    return {
        "flood": _no_data_entry("flood"),
        "landslide": _no_data_entry("landslide"),
        "tsunami": _no_data_entry("tsunami"),
    }


def _no_data_entry(hazard_type: str) -> dict:
    return {
        "level": "unknown",
        "depth_info": None,
        "confidence": "none",
        "source": None,
        "source_url": None,
        "last_updated": None,
        "summary": f"No {hazard_type} risk data available for this location. Check local hazard maps.",
    }


def _hazard_summary(hazard_type: str, level: str) -> str:
    """Generate user-facing summary text."""
    templates = {
        ("flood", "none"): "No flood risk zones identified near this property.",
        ("flood", "low"): "This property is outside major flood-predicted areas.",
        ("flood", "moderate"): "This property is in or near a flood-predicted area. Potential inundation during heavy rain events.",
        ("flood", "high"): "This property is in a high flood risk zone. Significant potential for inundation during heavy rain events.",
        ("landslide", "none"): "No landslide warning zones near this property.",
        ("landslide", "low"): "This property is outside designated landslide warning zones.",
        ("landslide", "moderate"): "This property is near a landslide caution zone. Terrain may be prone to slope failure.",
        ("landslide", "high"): "This property is in or very near a designated landslide special warning zone.",
        ("tsunami", "none"): "Property is inland — tsunami risk does not apply.",
        ("tsunami", "low"): "Low tsunami risk based on distance from coast and elevation.",
        ("tsunami", "moderate"): "This property is in a coastal area with moderate tsunami risk.",
        ("tsunami", "high"): "This property is in a high tsunami risk zone. Evacuation routes should be verified.",
    }
    return templates.get(
        (hazard_type, level),
        f"{hazard_type.title()} risk level: {level}. Verify with local authorities.",
    )
