"""
Pipeline Stage 6: Quality scoring and "What to know" generation.

Quality score: 0-1 based on data completeness.
"What to know": per-property honesty section (attractive / unclear / risky / verify).
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

from ingestion.config import LLM_MODEL, OPENAI_API_KEY
from ingestion.db import execute, get_cursor

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# QUALITY SCORING
# ══════════════════════════════════════════════════════════

def score_quality_all(limit: int = 500) -> int:
    """Compute quality scores for all properties that need it."""
    rows = execute(
        """
        SELECT id, price_jpy, prefecture, latitude, longitude,
               images, building_sqm, land_sqm, year_built,
               title_en, summary_en, hazard_scores, lifestyle_tags, rooms
        FROM properties
        WHERE quality_score = 0 OR quality_score IS NULL
        LIMIT %s
        """,
        (limit,),
    )

    if not rows:
        logger.info("No properties need quality scoring.")
        return 0

    logger.info(f"Scoring quality for {len(rows)} properties...")
    count = 0

    with get_cursor(commit=True) as cur:
        for row in rows:
            score = _compute_quality(row)
            cur.execute(
                "UPDATE properties SET quality_score = %s, updated_at = now() WHERE id = %s",
                (score, row["id"]),
            )
            count += 1

    logger.info(f"Scored {count} properties.")
    return count


def _compute_quality(row: dict) -> float:
    """
    Quality score based on data completeness.
    Each check is worth equal weight. Score = checks_passed / total_checks.
    """
    images = row.get("images")
    if isinstance(images, str):
        try:
            images = json.loads(images)
        except (json.JSONDecodeError, TypeError):
            images = []
    elif not isinstance(images, list):
        images = []

    hazard = row.get("hazard_scores")
    if isinstance(hazard, str):
        try:
            hazard = json.loads(hazard)
        except (json.JSONDecodeError, TypeError):
            hazard = {}
    elif not isinstance(hazard, dict):
        hazard = {}

    lifestyle = row.get("lifestyle_tags")
    if isinstance(lifestyle, str):
        try:
            lifestyle = json.loads(lifestyle)
        except (json.JSONDecodeError, TypeError):
            lifestyle = []
    elif not isinstance(lifestyle, list):
        lifestyle = []

    checks = [
        bool(row.get("price_jpy")),             # has price
        bool(row.get("prefecture")),            # has prefecture
        bool(row.get("latitude")),              # has coordinates
        len(images) >= 1,                        # has at least 1 image
        len(images) >= 3,                        # has 3+ images
        bool(row.get("building_sqm")),          # has building size
        bool(row.get("land_sqm")),              # has land size
        bool(row.get("year_built")),            # has year built
        bool(row.get("title_en")),              # has English title
        bool(row.get("summary_en")),            # has English summary
        bool(hazard),                            # has hazard data
        bool(lifestyle),                         # has lifestyle tags
        bool(row.get("rooms")),                 # has room layout
    ]

    return round(sum(checks) / len(checks), 2)


# ══════════════════════════════════════════════════════════
# "WHAT TO KNOW" GENERATION
# ══════════════════════════════════════════════════════════

WHAT_TO_KNOW_PROMPT = """You are an honest property analyst helping international buyers evaluate homes in Japan.

For this property, generate four lists of bullet points (2-4 items each):

1. **whats_attractive**: What genuinely looks good about this property (location, price, features)
2. **whats_unclear**: What information is missing or ambiguous from the listing
3. **whats_risky**: Real risks or concerns (hazards, condition, cost, access, legal)
4. **what_to_verify**: Specific things the buyer should check or verify before committing

Rules:
- Be specific, not generic. Reference actual property data.
- Do NOT sugar-coat. Buyers need honest assessments.
- If a property is in a hazard zone, say so clearly.
- If the year built suggests potential issues (pre-1981 earthquake code), mention it.
- If renovation seems needed, estimate the scale (light/moderate/heavy).
- Keep each bullet to one sentence.

Respond in JSON:
{
  "whats_attractive": ["...", "..."],
  "whats_unclear": ["...", "..."],
  "whats_risky": ["...", "..."],
  "what_to_verify": ["...", "..."]
}"""


def generate_what_to_know_all(limit: int = 50) -> int:
    """
    Generate "What to know" sections for properties that don't have them.
    Returns count processed.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set. Running rule-based What-to-Know only.")
        return _rule_based_what_to_know_all(limit)

    rows = execute(
        """
        SELECT id, title_en, original_title, summary_en, original_description,
               prefecture, city, price_jpy, price_display,
               building_sqm, land_sqm, year_built, rooms,
               building_type, condition_rating, renovation_estimate,
               nearest_station, station_distance,
               hazard_scores, lifestyle_tags
        FROM properties
        WHERE whats_attractive IS NULL
        LIMIT %s
        """,
        (limit,),
    )

    if not rows:
        logger.info("No properties need What-to-Know generation.")
        return 0

    logger.info(f"Generating What-to-Know for {len(rows)} properties...")
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    count = 0

    for i, row in enumerate(rows):
        try:
            result = _generate_wtk_llm(client, row)
            _save_wtk(row["id"], result)
            count += 1
        except Exception as e:
            logger.error(f"Error generating WTK for {row['id']}: {e}")
            # Fallback to rule-based
            try:
                result = _rule_based_wtk(row)
                _save_wtk(row["id"], result)
                count += 1
            except Exception:
                pass

        if (i + 1) % 10 == 0:
            logger.info(f"  Generated {i + 1}/{len(rows)}...")
            time.sleep(1)

    logger.info(f"Generated What-to-Know for {count} properties.")
    return count


def _generate_wtk_llm(client, row: dict) -> dict:
    """Generate What-to-Know via LLM."""
    # Parse hazard scores for context
    hazard = row.get("hazard_scores")
    if isinstance(hazard, str):
        try:
            hazard = json.loads(hazard)
        except (json.JSONDecodeError, TypeError):
            hazard = {}

    listing_data = {
        "title": row.get("title_en") or row.get("original_title"),
        "description": (row.get("summary_en") or row.get("original_description") or "")[:1200],
        "prefecture": row.get("prefecture"),
        "city": row.get("city"),
        "price": row.get("price_display"),
        "building_sqm": row.get("building_sqm"),
        "land_sqm": row.get("land_sqm"),
        "year_built": row.get("year_built"),
        "rooms": row.get("rooms"),
        "condition": row.get("condition_rating"),
        "renovation_estimate": row.get("renovation_estimate"),
        "station": row.get("station_distance"),
        "flood_risk": hazard.get("flood", {}).get("level", "unknown"),
        "landslide_risk": hazard.get("landslide", {}).get("level", "unknown"),
        "tsunami_risk": hazard.get("tsunami", {}).get("level", "unknown"),
    }

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": WHAT_TO_KNOW_PROMPT},
            {"role": "user", "content": json.dumps(listing_data, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=600,
    )

    return json.loads(response.choices[0].message.content)


def _rule_based_wtk(row: dict) -> dict:
    """Generate basic What-to-Know from rules when LLM is unavailable."""
    attractive = []
    unclear = []
    risky = []
    verify = []

    price = row.get("price_jpy") or 0
    year = row.get("year_built")
    building = row.get("building_sqm")
    condition = row.get("condition_rating") or "unknown"

    # Attractive
    if price > 0 and price < 1_000_000:
        attractive.append(f"Very affordable at ¥{price:,}")
    if building and building > 100:
        attractive.append(f"Spacious at {building:.0f}sqm")
    if row.get("rooms"):
        attractive.append(f"{row['rooms']} layout")

    # Unclear
    if not building:
        unclear.append("Building size is not listed")
    if not year:
        unclear.append("Year built is not specified")
    if condition == "unknown":
        unclear.append("Property condition is not described")

    # Risky
    if year and year < 1981:
        risky.append(f"Built in {year} — before Japan's 1981 earthquake-resistance building code revision")
    if condition in ("needs_work", "significant_renovation"):
        risky.append(f"Condition rated as '{condition}' — renovation costs could be significant")

    # Verify
    verify.append("Verify the property is still available before making plans")
    if year and year < 1990:
        verify.append("Inspect for asbestos, structural integrity, and plumbing condition")
    verify.append("Check local hazard maps at the municipal office")

    return {
        "whats_attractive": attractive or ["Property data is limited — review source listing for details"],
        "whats_unclear": unclear or ["Most information is provided"],
        "whats_risky": risky or ["No major risks identified from available data"],
        "what_to_verify": verify,
    }


def _rule_based_what_to_know_all(limit: int) -> int:
    """Fallback: generate rule-based WTK for all properties."""
    rows = execute(
        """
        SELECT id, price_jpy, building_sqm, year_built, rooms,
               condition_rating
        FROM properties
        WHERE whats_attractive IS NULL
        LIMIT %s
        """,
        (limit,),
    )
    count = 0
    for row in rows:
        try:
            result = _rule_based_wtk(row)
            _save_wtk(row["id"], result)
            count += 1
        except Exception as e:
            logger.error(f"Error: {e}")
    return count


def _save_wtk(property_id: str, result: dict):
    """Save What-to-Know to the property."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE properties SET
                whats_attractive = %s,
                whats_unclear = %s,
                whats_risky = %s,
                what_to_verify = %s,
                updated_at = now()
            WHERE id = %s
            """,
            (
                result.get("whats_attractive", []),
                result.get("whats_unclear", []),
                result.get("whats_risky", []),
                result.get("what_to_verify", []),
                property_id,
            ),
        )
