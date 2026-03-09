"""
Listing Freshness Checker
Checks original source URLs to detect sold/removed properties.
Run periodically (daily or every 2 days) via cron or manual CLI command.
"""

import asyncio
import aiohttp
import re
from datetime import datetime, timezone


# Patterns that indicate a property is SOLD or REMOVED on source sites
SOLD_PATTERNS = [
    r'sold',
    r'販売済',        # "sold" in Japanese
    r'成約済',        # "contract completed" in Japanese
    r'契約済',        # "contracted"
    r'商談中',        # "under negotiation"
    r'取り下げ',      # "withdrawn"
    r'this listing (has been|was) removed',
    r'no longer available',
    r'page not found',
    r'404',
    r'listing.*expired',
    r'under contract',
    r'pending',
]

SOLD_REGEX = re.compile('|'.join(SOLD_PATTERNS), re.IGNORECASE)


async def check_listing(session, url, timeout=15):
    """Check a single URL. Returns status: 'active', 'sold', 'dead', or 'error'."""
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=timeout),
            allow_redirects=True,
        ) as resp:
            if resp.status == 404 or resp.status == 410:
                return 'dead'
            if resp.status >= 400:
                return 'error'
            # Read first 50KB of page to check for sold patterns
            body = await resp.text(encoding='utf-8', errors='ignore')
            body_sample = body[:50000]
            if SOLD_REGEX.search(body_sample):
                return 'sold'
            return 'active'
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return 'error'


async def check_all_listings(supabase_client, batch_size=20):
    """Check all active listings for freshness."""
    # Fetch all active (non-sold) properties with source URLs
    result = supabase_client.table('properties') \
        .select('id, source_url, listing_status, check_error_count') \
        .neq('listing_status', 'sold') \
        .neq('listing_status', 'removed') \
        .not_.is_('source_url', 'null') \
        .execute()

    properties = result.data
    print(f"Checking {len(properties)} active listings...")

    sold_count = 0
    dead_count = 0
    error_count = 0

    connector = aiohttp.TCPConnector(limit=batch_size)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i in range(0, len(properties), batch_size):
            batch = properties[i:i + batch_size]
            tasks = [check_listing(session, p['source_url']) for p in batch]
            results = await asyncio.gather(*tasks)

            for prop, status in zip(batch, results):
                if status == 'sold':
                    supabase_client.table('properties').update({
                        'listing_status': 'sold',
                        'status_checked_at': datetime.now(timezone.utc).isoformat(),
                    }).eq('id', prop['id']).execute()
                    sold_count += 1
                    print(f"  SOLD: {prop['source_url']}")

                elif status == 'dead':
                    supabase_client.table('properties').update({
                        'listing_status': 'removed',
                        'status_checked_at': datetime.now(timezone.utc).isoformat(),
                    }).eq('id', prop['id']).execute()
                    dead_count += 1
                    print(f"  DEAD: {prop['source_url']}")

                elif status == 'error':
                    # Don't mark as removed on error — might be temporary
                    # After 3 consecutive errors, mark for review
                    error_ct = (prop.get('check_error_count') or 0) + 1
                    updates = {
                        'status_checked_at': datetime.now(timezone.utc).isoformat(),
                        'check_error_count': error_ct,
                    }
                    if error_ct >= 3:
                        updates['listing_status'] = 'removed'
                        print(f"  REMOVED (3+ errors): {prop['source_url']}")
                    supabase_client.table('properties').update(updates).eq('id', prop['id']).execute()
                    error_count += 1

                else:
                    # Active — reset error count
                    supabase_client.table('properties').update({
                        'status_checked_at': datetime.now(timezone.utc).isoformat(),
                        'check_error_count': 0,
                    }).eq('id', prop['id']).execute()

            # Be polite to source servers
            await asyncio.sleep(1)

    print(f"\nDone. Sold: {sold_count}, Dead: {dead_count}, Errors: {error_count}")
    return {'sold': sold_count, 'dead': dead_count, 'errors': error_count}
