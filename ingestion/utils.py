"""
Shared parsing utilities for scraper adapters.
Price parsing, area conversion, text cleaning.
"""

from __future__ import annotations

import re
from typing import Optional

from ingestion.config import PREFECTURE_MAP


def parse_price_jpy(text: str) -> Optional[int]:
    """
    Parse a Japanese price string into integer JPY.

    Handles:
      - "480万円" → 4_800_000
      - "4,800,000円" → 4_800_000
      - "¥4,800,000" → 4_800_000
      - "$32,000" → None (foreign currency, skip)
      - "価格未定" / "negotiable" → None
      - "100万円～200万円" → takes the first number (100万 → 1_000_000)
    """
    if not text:
        return None

    text = text.strip()

    # Remove common noise
    text = text.replace("税込", "").replace("税別", "").replace("(税込)", "")

    # Skip non-JPY
    if "$" in text and "¥" not in text and "円" not in text:
        return None

    # Skip negotiable / undecided
    skip_patterns = ["未定", "相談", "negotiable", "ask", "inquiry"]
    if any(p in text.lower() for p in skip_patterns):
        return None

    # Try 万円 format: "480万円" or "480万"
    match = re.search(r"([\d,\.]+)\s*万", text)
    if match:
        num_str = match.group(1).replace(",", "")
        try:
            return int(float(num_str) * 10_000)
        except ValueError:
            pass

    # Try plain number with 円 or ¥: "4,800,000円" or "¥4,800,000"
    match = re.search(r"[¥￥]?\s*([\d,]+)\s*円?", text)
    if match:
        num_str = match.group(1).replace(",", "")
        try:
            val = int(num_str)
            # Sanity: if it's less than 10,000, probably in 万 units misread
            if val < 10_000 and "万" not in text:
                return val * 10_000  # assume 万 was implied
            return val
        except ValueError:
            pass

    return None


def parse_area_sqm(text: str) -> Optional[float]:
    """
    Parse area text into square meters.

    Handles:
      - "150.5㎡" → 150.5
      - "150.5m²" → 150.5
      - "45.5坪" → ~150.4 (1 tsubo = 3.306 sqm)
      - "150.5 sqm" → 150.5
    """
    if not text:
        return None

    text = text.strip()

    # Try 坪 (tsubo) first
    match = re.search(r"([\d,\.]+)\s*坪", text)
    if match:
        try:
            tsubo = float(match.group(1).replace(",", ""))
            return round(tsubo * 3.306, 1)
        except ValueError:
            pass

    # Try ㎡ / m² / sqm / m2
    match = re.search(r"([\d,\.]+)\s*(?:㎡|m²|m2|sqm)", text, re.IGNORECASE)
    if match:
        try:
            return round(float(match.group(1).replace(",", "")), 1)
        except ValueError:
            pass

    # Try bare number if text looks like an area context
    match = re.search(r"([\d,\.]+)", text)
    if match:
        try:
            val = float(match.group(1).replace(",", ""))
            if 1 <= val <= 100_000:  # reasonable sqm range
                return round(val, 1)
        except ValueError:
            pass

    return None


def normalize_prefecture(text: str) -> Optional[str]:
    """
    Normalize a prefecture name to canonical romanized form.
    Handles kanji, romaji (with or without 県/府/都), and common misspellings.
    """
    if not text:
        return None

    text = text.strip()

    # Direct kanji lookup
    if text in PREFECTURE_MAP:
        return PREFECTURE_MAP[text]

    # Case-insensitive romaji match
    text_lower = text.lower().replace("-", "").replace(" ", "")
    for pref in PREFECTURE_MAP.values():
        if text_lower == pref.lower():
            return pref

    # Partial match: "Nagano Prefecture" → "Nagano"
    for pref in PREFECTURE_MAP.values():
        if pref.lower() in text_lower:
            return pref

    return None


def clean_text(text: Optional[str]) -> Optional[str]:
    """Strip whitespace, collapse newlines, remove zero-width chars."""
    if not text:
        return None
    # Remove zero-width characters
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else None


def extract_year_built(text: str) -> Optional[int]:
    """
    Extract year built from text.

    Handles:
      - "1985年築" → 1985
      - "Built in 1985" → 1985
      - "昭和60年" → 1985
      - "平成5年" → 1993
      - "令和3年" → 2021
    """
    if not text:
        return None

    # Western year
    match = re.search(r"((?:19|20)\d{2})\s*年?", text)
    if match:
        year = int(match.group(1))
        if 1900 <= year <= 2030:
            return year

    # Japanese era: 昭和 (Showa), 平成 (Heisei), 令和 (Reiwa)
    era_map = {
        "昭和": 1925,  # Showa year + 1925 = Western year
        "平成": 1988,  # Heisei year + 1988
        "令和": 2018,  # Reiwa year + 2018
    }
    for era, offset in era_map.items():
        match = re.search(rf"{era}\s*(\d{{1,2}})\s*年", text)
        if match:
            era_year = int(match.group(1))
            return offset + era_year

    return None


def make_absolute_url(base_url: str, href: str) -> str:
    """Convert a possibly-relative URL to absolute."""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        # Strip trailing slash from base
        return base_url.rstrip("/") + href
    return base_url.rstrip("/") + "/" + href
