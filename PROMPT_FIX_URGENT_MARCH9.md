# PROMPT À COLLER DANS ANTIGRAVITY — FIX URGENT 9 MARS

```
Auto-approve all changes and commands. Don't ask for permission.

## SITUATION

The pipeline ran overnight. Japan scraped 1120 listings but:
1. Dashboard shows "0 Active" because listing_status is NULL — the query only counts 'active'
2. Enrichment shows 0 — the enrich pipeline may not be working (check run.py pipeline command)
3. ALL EU/USA/NZ scrapers returned 0 listings — first run, never tested live, selectors wrong
4. Need to fix all of this NOW

## FIX 1: Dashboard query — NULL listing_status (CRITICAL)

The dashboard queries filter `WHERE listing_status = 'active'` but scraped listings have `listing_status = NULL`.

### Fix 1a: Update existing data
```sql
-- Set all NULL listing_status to 'active' (they ARE active, just not tagged)
UPDATE properties SET listing_status = 'active' WHERE listing_status IS NULL;
UPDATE raw_listings SET listing_status = 'active' WHERE listing_status IS NULL;
```

Run this SQL via psycopg2 in a quick script or add it to the pipeline startup.

### Fix 1b: Fix dashboard queries

In `ingestion/dashboard.py`, find ALL queries that filter on `listing_status = 'active'` and change them to:
```sql
WHERE (listing_status = 'active' OR listing_status IS NULL)
```

This applies to:
- `get_db_stats()`
- `get_country_stats()`
- Any other function that counts active listings

### Fix 1c: Fix adapters — set listing_status on insert

Make sure the scrapers set `listing_status = 'active'` when inserting new listings.

In `ingestion/storage.py`, in the `save_raw_listings()` function, ensure the INSERT statement includes:
```python
listing_status = 'active'
```

Or add a DEFAULT in the DB:
```sql
ALTER TABLE properties ALTER COLUMN listing_status SET DEFAULT 'active';
ALTER TABLE raw_listings ALTER COLUMN listing_status SET DEFAULT 'active';
```

## FIX 2: Enrichment pipeline — make sure it actually works

Check if `run.py pipeline` command exists and works:

```bash
cd "/Users/test/Documents/CheapHouse Japan/ingestion"
source venv/bin/activate
python run.py --help
```

If there's no `pipeline` command, check what enrichment commands exist. The enrichment should:
1. Take raw_listings with enrichment_status = 'pending' (or NULL)
2. Send title/description to Ollama for translation (Japanese → English)
3. Send to Ollama for lifestyle tags
4. Send to Ollama for "What to Know" report
5. Update enrichment_status = 'complete', set enriched_at = NOW()

If the `pipeline` command doesn't exist, create it in `run.py`:

```python
@cli.command("pipeline")
@click.option("--limit", default=500, help="Max listings to enrich")
@click.option("--skip-llm", is_flag=True, help="Skip LLM stages")
def run_pipeline(limit, skip_llm):
    """Run the full enrichment pipeline on pending listings."""
    from ingestion.db import execute, execute_write
    from ingestion.llm_client import llm_chat, check_ollama_available

    click.echo(f"Enrichment pipeline — limit {limit}")

    if not skip_llm:
        if not check_ollama_available():
            click.echo("WARNING: Ollama not available. Running with --skip-llm")
            skip_llm = True

    # Get pending listings
    pending = execute("""
        SELECT id, title, description, location, price_jpy, source_slug, country
        FROM properties
        WHERE (enrichment_status = 'pending' OR enrichment_status IS NULL)
        AND title IS NOT NULL
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))

    # Also check raw_listings if properties table is empty
    if not pending:
        pending = execute("""
            SELECT id, title, description, location, price_jpy, source_slug,
                   COALESCE(country, 'japan') as country
            FROM raw_listings
            WHERE (processing_status = 'pending' OR processing_status IS NULL)
            AND title IS NOT NULL
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))

    click.echo(f"Found {len(pending)} listings to enrich")

    if not pending:
        click.echo("Nothing to enrich.")
        return

    enriched_count = 0
    failed_count = 0

    for i, listing in enumerate(pending):
        listing_id = listing['id']
        title = listing.get('title', '')
        description = listing.get('description', '')
        country = listing.get('country', 'japan')

        click.echo(f"  [{i+1}/{len(pending)}] {title[:60]}...")

        if skip_llm:
            # Just mark as complete without LLM
            execute_write("""
                UPDATE properties SET
                    enrichment_status = 'complete',
                    enriched_at = NOW()
                WHERE id = %s
            """, (listing_id,))
            enriched_count += 1
            continue

        try:
            # Stage 1: Translate (if Japanese)
            title_en = title
            if country == 'japan' and _is_japanese(title):
                translate_prompt = f"""Translate this Japanese real estate listing to English.
Title: {title}
Description: {description[:500] if description else 'N/A'}

Return a JSON object:
{{"title_en": "English title", "description_en": "English description (brief)"}}"""

                resp = llm_chat(
                    messages=[{"role": "user", "content": translate_prompt}],
                    temperature=0.1,
                    json_mode=True,
                )
                try:
                    import json
                    data = json.loads(resp)
                    title_en = data.get('title_en', title)
                    desc_en = data.get('description_en', description)
                except:
                    title_en = title
                    desc_en = description
            else:
                title_en = title
                desc_en = description

            # Stage 2: Lifestyle tags
            tags_prompt = f"""Analyze this property listing and assign lifestyle tags.
Title: {title_en}
Location: {listing.get('location', 'Unknown')}
Price: {listing.get('price_jpy', 'Unknown')}
Country: {country}
Description: {desc_en[:300] if desc_en else 'N/A'}

Return a JSON array of 3-6 tags from these categories:
- Property type: "traditional", "modern", "renovation-needed", "move-in-ready", "historic"
- Lifestyle: "rural-retreat", "mountain-life", "coastal", "village-charm", "urban-access"
- Special: "garden", "farmland", "hot-spring-nearby", "ski-access", "wine-country"
- Value: "under-10k", "under-50k", "bargain", "auction"

Return ONLY a JSON array like: ["rural-retreat", "traditional", "renovation-needed"]"""

            tags_resp = llm_chat(
                messages=[{"role": "user", "content": tags_prompt}],
                temperature=0.1,
                json_mode=True,
            )
            try:
                import json
                tags = json.loads(tags_resp)
                if not isinstance(tags, list):
                    tags = []
            except:
                tags = []

            # Stage 3: What to Know
            wtk_prompt = f"""Write a brief "What to Know" section for a buyer considering this property.
Title: {title_en}
Location: {listing.get('location', 'Unknown')}
Country: {country}
Price: {listing.get('price_jpy', 'Unknown')}

Cover in 3-4 bullet points:
- Any red flags or concerns
- Renovation/condition assessment
- Location pros/cons
- Hidden costs or requirements for foreign buyers

Be honest and helpful. Max 150 words."""

            wtk_resp = llm_chat(
                messages=[{"role": "user", "content": wtk_prompt}],
                temperature=0.3,
            )

            # Save enrichment results
            execute_write("""
                UPDATE properties SET
                    title_en = %s,
                    lifestyle_tags = %s::jsonb,
                    what_to_know = %s,
                    enrichment_status = 'complete',
                    enriched_at = NOW()
                WHERE id = %s
            """, (title_en, json.dumps(tags), wtk_resp, listing_id))

            enriched_count += 1

        except Exception as e:
            click.echo(f"    ERROR: {e}")
            execute_write("""
                UPDATE properties SET
                    enrichment_status = 'failed',
                    enrichment_error = %s
                WHERE id = %s
            """, (str(e)[:500], listing_id))
            failed_count += 1

        # Small delay to not overload Ollama
        time.sleep(0.5)

    click.echo(f"\nDone: {enriched_count} enriched, {failed_count} failed")


def _is_japanese(text: str) -> bool:
    """Check if text contains Japanese characters."""
    import re
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text or ''))
```

Make sure to add `import time` at the top of run.py if not already there.

## FIX 3: EU/USA/NZ scrapers — debug the first failures

Look at the scrape_runs table to see the actual errors:

```bash
cd "/Users/test/Documents/CheapHouse Japan/ingestion"
source venv/bin/activate

python3 -c "
from ingestion.db import execute
rows = execute('''
    SELECT source_slug, status, listings_found, error_message, run_at
    FROM scrape_runs
    WHERE listings_found = 0 OR status = 'error'
    ORDER BY run_at DESC
    LIMIT 30
''')
for r in rows:
    print(f\"{r['source_slug']:25} | {r['status']:8} | {r.get('error_message', 'no error')[:80]}\")
"
```

For EACH failed source, look at the actual error and fix the adapter.

Common fixes needed for first-run failures:

### USA — CheapOldHouses
Their site is WordPress-based. Check the actual HTML:
```bash
curl -s "https://cheapoldhouses.com/listings/" | head -200
```
Update CSS selectors in `adapters/usa/cheap_old_houses.py` to match.

### USA — Redfin CSV
The CSV download URL pattern might need updating. Test:
```bash
curl -sL "https://www.redfin.com/stingray/api/gis-csv?al=1&market=false&max_price=100000&num_homes=50&property_type=house&region_id=35&region_type=2&status=9&uipt=1&v=8" -o /tmp/redfin_test.csv
head -5 /tmp/redfin_test.csv
```
If it returns HTML or error, the API endpoint has changed. Check Redfin's current CSV export URL.

### Europe — Gate-Away.com
```bash
curl -s "https://www.gate-away.com/properties-for-sale-in-italy?price_max=100000" | grep -c "property-card\|listing-card\|property-item"
```
If 0, the CSS class names are wrong. Inspect the actual HTML.

### Sweden — Hemnet
Hemnet likely needs their internal GraphQL API or has strong anti-bot. May need to use their sitemap or a different approach.

### For each broken adapter:
1. Fetch the real HTML
2. Find the correct CSS selectors
3. Update the adapter
4. Test with `python run.py scrape --source {slug} --limit 3`

If a site is genuinely blocking or requires JS rendering, mark it as needs-playwright and skip for now:
```python
# In the adapter:
def get_listing_urls(self):
    logger.warning(f"{self.slug}: requires JS rendering — skipping until Playwright is set up")
    return []
```

## FIX 4: Run enrichment NOW on the 1120 pending listings

After fixing the pipeline command:

```bash
cd "/Users/test/Documents/CheapHouse Japan/ingestion"
source venv/bin/activate

# Make sure Ollama is running
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print([m['name'] for m in json.load(sys.stdin)['models']])"

# Run enrichment on first batch (100 to test)
python run.py pipeline --limit 100

# If it works, run the rest
python run.py pipeline --limit 1200
```

## FIX 5: Also install self_heal.py

The self-healing prompt was created (PROMPT_SELF_HEALING_PIPELINE.md). If not already built, also implement `ingestion/self_heal.py` from that prompt. This will auto-fix broken scrapers on future runs.

## After all fixes — verify

```bash
echo "=== VERIFICATION ==="
echo ""

# Check active listings
python3 -c "
from ingestion.db import execute
rows = execute('SELECT COUNT(*) as c FROM properties WHERE listing_status = %s OR listing_status IS NULL', ('active',))
print(f'Active listings: {rows[0][\"c\"]}')
rows = execute('SELECT COUNT(*) as c FROM properties WHERE enrichment_status = %s', ('complete',))
print(f'Enriched: {rows[0][\"c\"]}')
rows = execute('SELECT source_slug, COUNT(*) as c FROM properties GROUP BY source_slug ORDER BY c DESC')
for r in rows:
    print(f'  {r[\"source_slug\"]:25} {r[\"c\"]}')
"

# Check cron
echo ""
echo "Cron jobs:"
crontab -l | grep auto_pipeline

echo ""
echo "=== DONE ==="
```

Push everything to GitHub when done.
```
