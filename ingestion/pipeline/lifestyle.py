"""
Pipeline Stage 5: Lifestyle tagging (Living Profiles).

Two-pass system:
  1. Rule pass: deterministic tags from property attributes
  2. LLM pass: contextual tags from description text

Tags are always stored with reasons so users understand why they were assigned.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

from ingestion.config import LLM_BATCH_SIZE, LLM_MODEL, OPENAI_API_KEY
from ingestion.db import execute, get_cursor

logger = logging.getLogger(__name__)

# ── Living Profile definitions ───────────────────────────
LIVING_PROFILES = {
    "pet-friendly": {
        "label": "🐕 Dog-Friendly Escape",
        "description": "Good for pet owners — outdoor space, detached, rural or suburban",
    },
    "artist-retreat": {
        "label": "🎨 Artist Retreat",
        "description": "Creative potential — large rooms, scenic location, quiet surroundings",
    },
    "remote-work": {
        "label": "💻 Remote Work Hideaway",
        "description": "Suitable for working remotely — multiple rooms, connected area",
    },
    "low-renovation": {
        "label": "🔧 Low-Stress Move-In",
        "description": "Relatively move-in ready — newer build or good condition",
    },
    "near-station": {
        "label": "🚉 Near Station",
        "description": "Walking distance to a train station",
    },
    "rural-retreat": {
        "label": "🏔️ Mountain / Rural Base",
        "description": "Secluded countryside or mountain setting",
    },
    "family-ready": {
        "label": "👨‍👩‍👧 Family Ready",
        "description": "Suitable for families — multiple bedrooms, near services",
    },
    "retirement": {
        "label": "🏖️ Retirement Pace",
        "description": "Calm, affordable, accessible for retirees",
    },
}

TAG_PROMPT = """You are analyzing a Japanese property listing to assign lifestyle tags.

Available tags (assign ONLY those that genuinely apply):
- pet-friendly: property has garden/yard, is detached, in quiet area
- artist-retreat: has large/interesting rooms, scenic surroundings, creative potential
- remote-work: has multiple rooms (one usable as office), in area with likely internet
- low-renovation: condition is good or fair, relatively recent build
- near-station: explicitly mentioned within walking distance of station
- rural-retreat: in countryside, mountain, or very quiet/remote area
- family-ready: 3+ bedrooms, near schools or hospitals, safe area
- retirement: calm, affordable, easy to manage, mild climate

For each tag you assign, provide ONE specific reason based on the listing data.
Do NOT assign a tag unless you have a concrete reason from the data.

Respond in JSON format:
{"tags": [{"tag": "...", "confidence": 0.0-1.0, "reason": "..."}]}"""


def tag_lifestyle_all(limit: int = 500) -> int:
    """
    Apply lifestyle tags to all properties that don't have them.
    Returns count processed.
    """
    rows = execute(
        """
        SELECT id, original_title, title_en, original_description, summary_en,
               prefecture, city, rooms, building_sqm, land_sqm,
               year_built, building_type, condition_rating,
               price_jpy, nearest_station, station_distance
        FROM properties
        WHERE lifestyle_tags = '[]'::jsonb OR lifestyle_tags IS NULL
        LIMIT %s
        """,
        (limit,),
    )

    if not rows:
        logger.info("No properties need lifestyle tagging.")
        return 0

    logger.info(f"Tagging {len(rows)} properties...")
    has_llm = bool(OPENAI_API_KEY)
    count = 0

    for i, row in enumerate(rows):
        try:
            # Pass 1: Rule-based tags
            tags = _rule_based_tags(row)

            # Pass 2: LLM-based tags (if available)
            if has_llm:
                llm_tags = _llm_tags(row)
                tags = _merge_tags(tags, llm_tags)

            _save_tags(row["id"], tags)
            count += 1
        except Exception as e:
            logger.error(f"Error tagging property {row['id']}: {e}")

        if has_llm and (i + 1) % LLM_BATCH_SIZE == 0:
            time.sleep(1)

    logger.info(f"Tagged {count} properties.")
    return count


def _rule_based_tags(row: dict) -> list[dict]:
    """Apply deterministic rules to assign tags."""
    tags = []
    rooms_str = row.get("rooms") or ""
    building = row.get("building_sqm") or 0
    land = row.get("land_sqm") or 0
    year = row.get("year_built")
    condition = row.get("condition_rating") or ""
    station = row.get("station_distance") or ""
    price = row.get("price_jpy") or 0
    prefecture = (row.get("prefecture") or "").lower()

    # Room count extraction
    import re
    room_match = re.search(r"(\d+)", rooms_str)
    room_count = int(room_match.group(1)) if room_match else 0

    # pet-friendly: has garden, detached, not tiny
    if land > building * 1.3 and land > 100 and row.get("building_type") == "detached":
        tags.append({
            "tag": "pet-friendly",
            "confidence": 0.7,
            "reason": f"Detached home with {land:.0f}sqm land (garden space likely)",
            "method": "rule",
        })

    # remote-work: 3+ rooms
    if room_count >= 3 and building > 60:
        tags.append({
            "tag": "remote-work",
            "confidence": 0.6,
            "reason": f"{rooms_str} layout — room available for home office",
            "method": "rule",
        })

    # low-renovation: good/fair condition or newer build
    if condition in ("good", "fair") or (year and year >= 2000):
        reason = f"Condition: {condition}" if condition in ("good", "fair") else f"Built in {year}"
        tags.append({
            "tag": "low-renovation",
            "confidence": 0.7,
            "reason": reason,
            "method": "rule",
        })

    # near-station
    if station:
        walk_match = re.search(r"(\d+)\s*min\s*walk", station, re.IGNORECASE)
        if walk_match and int(walk_match.group(1)) <= 15:
            tags.append({
                "tag": "near-station",
                "confidence": 0.9,
                "reason": f"{station}",
                "method": "rule",
            })

    # family-ready: 3+ bedrooms
    if room_count >= 3:
        tags.append({
            "tag": "family-ready",
            "confidence": 0.5,
            "reason": f"{rooms_str} layout with {room_count}+ rooms",
            "method": "rule",
        })

    # rural-retreat: certain prefectures, low price
    rural_prefectures = {
        "nagano", "niigata", "akita", "yamagata", "iwate", "aomori",
        "shimane", "tottori", "kochi", "ehime", "oita", "kumamoto",
        "miyazaki", "kagoshima",
    }
    if prefecture in rural_prefectures:
        tags.append({
            "tag": "rural-retreat",
            "confidence": 0.6,
            "reason": f"Located in {row.get('prefecture', 'rural')} prefecture",
            "method": "rule",
        })

    # retirement: affordable, calm area
    if price > 0 and price < 3_000_000 and room_count >= 2:
        tags.append({
            "tag": "retirement",
            "confidence": 0.5,
            "reason": f"Affordable at {price:,}¥ with {rooms_str} layout",
            "method": "rule",
        })

    return tags


def _llm_tags(row: dict) -> list[dict]:
    """Get contextual tags from LLM analysis."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    listing_context = {
        "title": row.get("title_en") or row.get("original_title"),
        "description": (row.get("summary_en") or row.get("original_description") or "")[:1000],
        "prefecture": row.get("prefecture"),
        "city": row.get("city"),
        "rooms": row.get("rooms"),
        "building_sqm": row.get("building_sqm"),
        "land_sqm": row.get("land_sqm"),
        "year_built": row.get("year_built"),
        "condition": row.get("condition_rating"),
        "price_jpy": row.get("price_jpy"),
        "station": row.get("station_distance"),
    }

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": TAG_PROMPT},
                {"role": "user", "content": json.dumps(listing_context, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=400,
        )

        result = json.loads(response.choices[0].message.content)
        llm_tags = []
        for t in result.get("tags", []):
            if t.get("tag") in LIVING_PROFILES:
                llm_tags.append({
                    "tag": t["tag"],
                    "confidence": min(float(t.get("confidence", 0.5)), 0.95),
                    "reason": t.get("reason", "LLM assessment"),
                    "method": "llm",
                })
        return llm_tags

    except Exception as e:
        logger.warning(f"LLM tagging failed: {e}")
        return []


def _merge_tags(rule_tags: list[dict], llm_tags: list[dict]) -> list[dict]:
    """Merge rule and LLM tags. When both assign same tag, keep higher confidence."""
    merged = {t["tag"]: t for t in rule_tags}

    for lt in llm_tags:
        tag_name = lt["tag"]
        if tag_name in merged:
            # Both agree — boost confidence, combine reasons
            existing = merged[tag_name]
            merged[tag_name] = {
                "tag": tag_name,
                "confidence": min(max(existing["confidence"], lt["confidence"]) + 0.1, 0.95),
                "reason": f"{existing['reason']}; {lt['reason']}",
                "method": "rule+llm",
            }
        else:
            merged[tag_name] = lt

    return list(merged.values())


def _save_tags(property_id: str, tags: list[dict]):
    """Save lifestyle tags to the property."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE properties SET lifestyle_tags = %s::jsonb, updated_at = now() WHERE id = %s",
            (json.dumps(tags), property_id),
        )
