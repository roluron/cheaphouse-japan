"""
New Zealand price and property utilities.
"""

from __future__ import annotations

import re
from typing import Optional


def parse_price_nzd(text: str) -> Optional[int]:
    """
    Parse NZD price formats:
    - "$350,000" or "NZ$350,000"
    - "$350K"
    - "Asking price: $280,000"
    - "By Negotiation" → None
    - "Tender" → None
    - "Auction" → None (but flag it)
    """
    if not text:
        return None

    text_upper = text.strip().upper()

    # Non-price listings
    if any(kw in text_upper for kw in ["NEGOTIATION", "TENDER", "AUCTION",
                                         "DEADLINE", "BY NEG", "PBN"]):
        return None  # Price not disclosed

    # Handle K shorthand
    k_match = re.search(r'[\$NZ]*\s*([\d,.]+)\s*K', text_upper)
    if k_match:
        return int(float(k_match.group(1).replace(',', '')) * 1000)

    # Standard price
    cleaned = re.sub(r'[^\d]', '', text)
    if not cleaned:
        return None
    price = int(cleaned)
    return price if price < 10_000_000 else None  # Sanity cap


def parse_area_sqm_nz(text: str) -> Optional[float]:
    """Parse area: '120m²', '120 sqm', '120m2'."""
    if not text:
        return None
    match = re.search(r'([\d,]+\.?\d*)\s*(?:m²|m2|sqm)', text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', ''))
    return None


def parse_land_area_nz(text: str) -> Optional[float]:
    """
    Parse NZ land area (often in m² or hectares):
    - "809m²" → 809.0
    - "2.5 hectares" → 25000.0
    - "1 acre" → 4047.0
    """
    if not text:
        return None

    # Hectares
    ha_match = re.search(r'([\d,.]+)\s*(?:hectares?|ha)', text, re.IGNORECASE)
    if ha_match:
        return float(ha_match.group(1).replace(',', '')) * 10_000

    # Acres
    acre_match = re.search(r'([\d,.]+)\s*(?:acres?|ac)', text, re.IGNORECASE)
    if acre_match:
        return float(acre_match.group(1).replace(',', '')) * 4_047

    # Square meters
    sqm_match = re.search(r'([\d,]+)\s*(?:m²|m2|sqm)', text, re.IGNORECASE)
    if sqm_match:
        return float(sqm_match.group(1).replace(',', ''))

    return None


def nzd_to_jpy(nzd: int) -> int:
    """Rough NZD→JPY for cross-country comparison."""
    return int(nzd * 90)  # ~90 JPY/NZD as of 2026
