"""
Pipeline Stage 2: Translate and rewrite listings into clear English.

Uses LLM to generate:
  - title_en: clean English title (under 80 chars)
  - summary_en: 2-3 paragraph English summary

Processes properties where title_en IS NULL.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

from ingestion.config import LLM_BATCH_SIZE, LLM_PROVIDER
from ingestion.llm_client import llm_chat
from ingestion.db import execute, get_cursor

logger = logging.getLogger(__name__)

TRANSLATE_PROMPT = """You are a real estate copywriter specializing in Japanese properties for international buyers.

Given this property listing data, generate:

1. **title_en**: A clear, specific English title under 80 characters.
   Format: "[Type] in [City/Area], [Prefecture]" or "[Key Feature] [Type] in [Location]"
   Examples: "Spacious 3LDK Home in Otaru, Hokkaido" or "Renovated Kominka near Kyoto"
   Do NOT use generic superlatives. Be specific and honest.

2. **summary_en**: A 2-3 paragraph summary covering:
   - What the property is (type, size, layout, condition)
   - Location context (area character, access, surroundings)
   - Anything a buyer should notice (good or bad)

Rules:
- Do NOT invent features not in the source data
- If information is missing, say so clearly ("Building size is not listed")
- Do NOT use marketing fluff
- Be honest about condition and limitations
- Write for someone who has never been to Japan

Respond in JSON format:
{"title_en": "...", "summary_en": "..."}"""


def translate_all(limit: int = 50) -> int:
    """
    Translate all properties that don't have English titles yet.
    Returns count processed.
    """
    rows = execute(
        """
        SELECT id, original_title, original_description,
               prefecture, city, rooms, building_sqm, land_sqm,
               year_built, building_type, condition_rating,
               price_jpy, price_display, address_text,
               nearest_station, station_distance
        FROM properties
        WHERE title_en IS NULL
        ORDER BY created_at ASC
        LIMIT %s
        """,
        (limit,),
    )

    if not rows:
        logger.info("No properties need translation.")
        return 0

    logger.info(f"Translating {len(rows)} properties (provider: {LLM_PROVIDER})...")
    processed = 0

    for i, row in enumerate(rows):
        try:
            title_en, summary_en = _translate_one(row)
            _save_translation(row["id"], title_en, summary_en)
            processed += 1
        except Exception as e:
            logger.error(f"Error translating property {row['id']}: {e}")

        # Rate limiting between batches
        if (i + 1) % LLM_BATCH_SIZE == 0:
            logger.info(f"  Translated {i + 1}/{len(rows)}...")
            time.sleep(1)

    logger.info(f"Translated {processed}/{len(rows)} properties.")
    return processed


def _translate_one(row: dict) -> tuple[str, str]:
    """Generate English title and summary for one property."""

    # Build context for the LLM
    listing_data = {
        "original_title": row.get("original_title") or "Not provided",
        "original_description": (row.get("original_description") or "Not provided")[:1500],
        "prefecture": row.get("prefecture") or "Unknown",
        "city": row.get("city") or "Unknown",
        "rooms": row.get("rooms") or "Unknown",
        "building_sqm": row.get("building_sqm"),
        "land_sqm": row.get("land_sqm"),
        "year_built": row.get("year_built"),
        "building_type": row.get("building_type") or "Unknown",
        "condition": row.get("condition_rating") or "Unknown",
        "price": row.get("price_display") or "Unknown",
        "address": row.get("address_text") or "Not provided",
        "nearest_station": row.get("nearest_station"),
        "station_distance": row.get("station_distance"),
    }

    result = llm_chat(
        system_prompt=TRANSLATE_PROMPT,
        user_content=f"Property listing data:\n{json.dumps(listing_data, ensure_ascii=False, indent=2)}",
        temperature=0.3,
        max_tokens=800,
        json_mode=True,
    )

    title_en = result.get("title_en", row.get("original_title", "Untitled"))
    summary_en = result.get("summary_en", "No summary available.")

    return title_en, summary_en


def _save_translation(property_id: str, title_en: str, summary_en: str):
    """Save translated title and summary to the property."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE properties
            SET title_en = %s, summary_en = %s, updated_at = now()
            WHERE id = %s
            """,
            (title_en, summary_en, property_id),
        )
