"""Check source listings and persist an honest availability state."""

import asyncio
import re
from datetime import datetime, timezone

SOLD_REGEX = re.compile(
    "|".join(
        [
            r"\bsold\b",
            r"販売済",
            r"成約済",
            r"契約済",
            r"取り下げ",
            r"this listing (has been|was) removed",
            r"no longer available",
            r"page not found",
            r"listing.{0,20}expired",
        ]
    ),
    re.IGNORECASE,
)

PENDING_REGEX = re.compile(
    "|".join([r"商談中", r"\bunder contract\b", r"\bpending\b"]),
    re.IGNORECASE,
)


async def check_listing(session, url, timeout=15):
    """Return active, pending, sold, dead, or error for one source URL."""
    import aiohttp

    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=timeout),
            allow_redirects=True,
        ) as response:
            if response.status in (404, 410):
                return "dead"
            if response.status >= 400:
                return "error"

            body = await response.text(encoding="utf-8", errors="ignore")
            sample = body[:100_000]
            if SOLD_REGEX.search(sample):
                return "sold"
            if PENDING_REGEX.search(sample):
                return "pending"
            return "active"
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        return "error"


def state_updates(check_result, previous_errors=0, checked_at=None):
    """Map an observed source result to database updates without guessing."""
    checked_at = checked_at or datetime.now(timezone.utc).isoformat()
    base = {
        "last_checked_at": checked_at,
        "status_checked_at": checked_at,
    }

    if check_result == "active":
        return {
            **base,
            "listing_status": "active",
            "freshness_label": "verified",
            "status_reason": "source_confirmed_active",
            "check_error_count": 0,
            "last_seen_at": checked_at,
            "gone_since": None,
        }

    if check_result == "sold":
        return {
            **base,
            "listing_status": "sold",
            "freshness_label": "unavailable",
            "status_reason": "source_indicates_sold",
            "check_error_count": 0,
            "gone_since": checked_at,
        }

    if check_result == "dead":
        return {
            **base,
            "listing_status": "removed",
            "freshness_label": "unavailable",
            "status_reason": "source_page_removed",
            "check_error_count": 0,
            "gone_since": checked_at,
        }

    if check_result == "pending":
        return {
            **base,
            "listing_status": "uncertain",
            "freshness_label": "unconfirmed",
            "status_reason": "source_indicates_pending",
            "check_error_count": 0,
        }

    return {
        **base,
        "listing_status": "uncertain",
        "freshness_label": "unconfirmed",
        "status_reason": "source_check_failed",
        "check_error_count": previous_errors + 1,
    }


async def check_all_listings(supabase_client, batch_size=20):
    """Check all browse-eligible listings and retain unavailable records."""
    import aiohttp

    result = (
        supabase_client.table("properties")
        .select("id, original_url, listing_status, check_error_count")
        .in_("listing_status", ["active", "uncertain"])
        .not_.is_("original_url", "null")
        .execute()
    )

    properties = result.data or []
    print(f"Checking {len(properties)} listings...")
    counts = {"active": 0, "pending": 0, "sold": 0, "dead": 0, "error": 0}

    connector = aiohttp.TCPConnector(limit=batch_size)
    async with aiohttp.ClientSession(connector=connector) as session:
        for index in range(0, len(properties), batch_size):
            batch = properties[index : index + batch_size]
            results = await asyncio.gather(
                *[check_listing(session, item["original_url"]) for item in batch]
            )
            checked_at = datetime.now(timezone.utc).isoformat()

            for property_record, check_result in zip(batch, results):
                updates = state_updates(
                    check_result,
                    property_record.get("check_error_count") or 0,
                    checked_at,
                )
                (
                    supabase_client.table("properties")
                    .update(updates)
                    .eq("id", property_record["id"])
                    .execute()
                )
                counts[check_result] += 1
                print(
                    f"  {updates['listing_status'].upper()}: "
                    f"{property_record['original_url']}"
                )

            await asyncio.sleep(1)

    print(
        "Done. "
        + ", ".join(f"{name}: {count}" for name, count in counts.items())
    )
    return counts
