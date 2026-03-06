"""
Data models for the ingestion pipeline.
RawListing is the intermediate format every adapter outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RawListing:
    """
    Common intermediate format produced by every scraper adapter.
    Only source_slug, source_url, and title are required.
    Everything else is optional — adapters extract what they can.
    """

    # ── Required ─────────────────────────────────────────
    source_slug: str
    source_url: str
    title: str

    # ── Source identification ────────────────────────────
    source_listing_id: Optional[str] = None

    # ── Description ──────────────────────────────────────
    description: Optional[str] = None

    # ── Price ────────────────────────────────────────────
    price_raw: Optional[str] = None  # original text: "480万円"
    price_jpy: Optional[int] = None  # normalized to integer yen

    # ── Location ─────────────────────────────────────────
    prefecture: Optional[str] = None
    city: Optional[str] = None
    address_raw: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # ── Property details ─────────────────────────────────
    land_sqm: Optional[float] = None
    building_sqm: Optional[float] = None
    year_built: Optional[int] = None
    building_type: Optional[str] = None  # detached, kominka, apartment, land_only
    structure: Optional[str] = None  # wood, rc, steel
    rooms: Optional[str] = None  # "4LDK"
    floors: Optional[int] = None

    # ── Condition ────────────────────────────────────────
    condition_notes: Optional[str] = None

    # ── Transport ────────────────────────────────────────
    nearest_station: Optional[str] = None
    station_distance: Optional[str] = None

    # ── Images ───────────────────────────────────────────
    image_urls: list[str] = field(default_factory=list)

    # ── Raw payload for debugging ────────────────────────
    raw_data: Optional[dict] = None

    # ── Timestamp ────────────────────────────────────────
    fetched_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        """Convert to a plain dict for DB insertion."""
        import json

        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
            elif isinstance(v, list):
                d[k] = v  # lists handled by psycopg2 or json
            elif isinstance(v, dict):
                d[k] = json.dumps(v)
            else:
                d[k] = v
        return d
