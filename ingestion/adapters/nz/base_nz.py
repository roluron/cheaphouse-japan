"""
New Zealand adapter base class.
"""

from __future__ import annotations

from ingestion.base_adapter import BaseAdapter


class NZBaseAdapter(BaseAdapter):
    """Base for all NZ adapters."""

    country: str = "new-zealand"
    currency: str = "NZD"
    default_language: str = "en"

    # Price threshold: NZD 300K (~USD 180K) — NZ is expensive
    # For truly "cheap" NZ: under NZD 200K in rural areas
    PRICE_THRESHOLD = 300_000

    # Cheapest regions:
    # South Island: West Coast, Southland, Gore, Invercargill
    # North Island: Whanganui, Kawerau, South Waikato, Ōpōtiki
    TARGET_REGIONS = [
        # South Island (cheapest)
        "west-coast", "southland", "gore", "invercargill",
        "timaru", "oamaru", "greymouth",
        # North Island (affordable)
        "whanganui", "kawerau", "south-waikato",
        "opotiki", "tararua", "wairoa",
    ]
