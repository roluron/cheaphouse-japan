"""
USA adapter base class.
Extends BaseAdapter with USD price handling and US address parsing.
"""

from __future__ import annotations

from ingestion.base_adapter import BaseAdapter


class USABaseAdapter(BaseAdapter):
    """Base for all USA adapters."""

    country: str = "usa"
    currency: str = "USD"
    default_language: str = "en"

    PRICE_THRESHOLD = 100_000  # $100K max for "cheap" houses

    # Target states with cheap housing:
    # Midwest: Ohio, Michigan, Indiana, Kansas, Missouri
    # South: Mississippi, Alabama, Arkansas, West Virginia
    # Rust Belt: Pennsylvania, upstate New York
    TARGET_STATES = [
        "OH", "MI", "IN", "KS", "MO",
        "MS", "AL", "AR", "WV",
        "PA", "NY",
    ]
