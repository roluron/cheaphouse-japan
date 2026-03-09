"""
European price and text utilities.
Handles EUR/SEK price parsing, European area formats, and currency conversion.
"""

from __future__ import annotations

import re
from typing import Optional


def parse_price_eur(text: str) -> Optional[int]:
    """
    Parse European price formats into integer EUR cents → whole euros.

    Handles:
      - "85 000 €" or "85.000 €" (French/Italian)
      - "€85,000" (English portals)
      - "85000" (plain)
      - "85 000" (space-separated)
    """
    if not text:
        return None
    cleaned = re.sub(r'[^\d]', '', text.strip())
    if not cleaned:
        return None
    price = int(cleaned)
    # Sanity check: if > 100M, probably parsing error
    if price > 100_000_000:
        return None
    return price


def parse_price_sek(text: str) -> Optional[int]:
    """
    Parse Swedish krona prices.

    Handles:
      - "1 250 000 kr"
      - "1,250,000 SEK"
      - "1250000"
    """
    if not text:
        return None
    cleaned = re.sub(r'[^\d]', '', text.strip())
    if not cleaned:
        return None
    return int(cleaned)


def parse_area_sqm_europe(text: str) -> Optional[float]:
    """
    Parse area: "120 m²", "120 m2", "120 mq" (Italian), "120 kvm" (Swedish).
    """
    if not text:
        return None
    match = re.search(r'(\d+[\.,]?\d*)\s*(?:m²|m2|mq|kvm|sqm)', text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None


def extract_region(address: str, country: str) -> Optional[str]:
    """Extract region/department from address string."""
    # Each country has different admin divisions
    # France: département (e.g., "Creuse", "Dordogne")
    # Italy: provincia (e.g., "Toscana", "Calabria")
    # Portugal: distrito (e.g., "Bragança", "Alentejo")
    # Sweden: län (e.g., "Dalarna", "Jämtland")
    # For now, return raw address — LLM enrichment will normalize
    return address


def eur_to_jpy(eur: int) -> int:
    """Rough EUR→JPY for comparison (updated periodically)."""
    return int(eur * 162)  # ~162 JPY/EUR as of 2026


def sek_to_jpy(sek: int) -> int:
    """Rough SEK→JPY for comparison."""
    return int(sek * 14)  # ~14 JPY/SEK as of 2026
