"""
USA price and address utilities.
Handles USD price parsing, square footage, and US address decomposition.
"""

from __future__ import annotations

import re
from typing import Optional


def parse_price_usd(text: str) -> Optional[int]:
    """
    Parse USD price formats:
    - "$85,000"
    - "$85K"
    - "85000"
    - "$1.2M" (filter out — too expensive)
    """
    if not text:
        return None

    text = text.strip().upper()

    # Handle K shorthand: "$85K" → 85000
    k_match = re.search(r'\$?([\d,.]+)\s*K', text)
    if k_match:
        return int(float(k_match.group(1).replace(',', '')) * 1000)

    # Handle M shorthand: "$1.2M" → 1200000
    m_match = re.search(r'\$?([\d,.]+)\s*M', text)
    if m_match:
        val = int(float(m_match.group(1).replace(',', '')) * 1_000_000)
        return val if val <= 200_000 else None  # Skip expensive ones

    # Standard: "$85,000" or "85000"
    cleaned = re.sub(r'[^\d]', '', text)
    if not cleaned:
        return None
    price = int(cleaned)
    return price if price <= 500_000 else None  # Sanity cap


def parse_area_sqft(text: str) -> Optional[float]:
    """Parse area in sq ft: '1,200 sqft', '1200 sq ft'."""
    if not text:
        return None
    match = re.search(r'([\d,]+)\s*(?:sqft|sq\.?\s*ft|sf)', text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', ''))
    return None


def sqft_to_sqm(sqft: float) -> float:
    """Convert square feet to square meters."""
    return round(sqft * 0.0929, 1)


def usd_to_jpy(usd: int) -> int:
    """Rough USD→JPY for cross-country comparison."""
    return int(usd * 150)  # ~150 JPY/USD as of 2026


def parse_us_address(address: str) -> dict:
    """
    Parse US address into components.
    '123 Main St, Cleveland, OH 44101' →
    {'street': '123 Main St', 'city': 'Cleveland', 'state': 'OH', 'zip': '44101'}
    """
    if not address:
        return {'street': '', 'city': '', 'state': '', 'zip': ''}

    parts = [p.strip() for p in address.split(',')]
    result = {'street': '', 'city': '', 'state': '', 'zip': ''}

    if len(parts) >= 1:
        result['street'] = parts[0]
    if len(parts) >= 2:
        result['city'] = parts[1]
    if len(parts) >= 3:
        # "OH 44101" or "OH"
        state_zip = parts[2].strip().split()
        result['state'] = state_zip[0] if state_zip else ''
        result['zip'] = state_zip[1] if len(state_zip) > 1 else ''

    return result
