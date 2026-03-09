"""
European adapter base class.
Extends BaseAdapter with EUR/SEK price handling and European address parsing.
"""

from __future__ import annotations

import logging
from typing import Optional

from ingestion.base_adapter import BaseAdapter
from ingestion.utils_europe import eur_to_jpy, sek_to_jpy

logger = logging.getLogger(__name__)


class EuropeBaseAdapter(BaseAdapter):
    """Base for all European adapters."""

    country: str = ""           # "france", "italy", "portugal", "sweden"
    currency: str = "EUR"       # EUR or SEK
    default_language: str = ""  # "fr", "it", "pt", "sv"

    # Price thresholds for "cheap" (in local currency)
    PRICE_THRESHOLDS = {
        "france": 150_000,      # €150K
        "italy": 100_000,       # €100K
        "portugal": 80_000,     # €80K
        "sweden": 1_500_000,    # 1.5M SEK (~€130K)
    }

    def price_to_jpy(self, price: int) -> int:
        """Convert local currency price to JPY for storage."""
        if self.currency == "SEK":
            return sek_to_jpy(price)
        return eur_to_jpy(price)  # Default EUR

    def is_cheap(self, price: int) -> bool:
        """Check if price is below the 'cheap' threshold for this country."""
        threshold = self.PRICE_THRESHOLDS.get(self.country, 150_000)
        return price <= threshold
