#!/usr/bin/env python3
"""
CLI runner for the CheapHouse Japan ingestion pipeline.

Usage:
    python run.py scrape --source old-houses-japan     # Scrape one source
    python run.py scrape --all                         # Scrape all active sources
    python run.py list-sources                         # Show registered sources
    python run.py stats                                # Show DB counts
"""

from __future__ import annotations

import logging
import sys
import time

import click

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cheaphouse")


@click.group()
def cli():
    """CheapHouse Japan — Ingestion Pipeline CLI"""
    pass


@cli.command()
@click.option("--source", "-s", help="Source slug to scrape (e.g. old-houses-japan)")
@click.option("--all-sources", "scrape_all", is_flag=True, help="Scrape all active sources")
@click.option("--dry-run", is_flag=True, help="Fetch URLs only, don't extract listings")
def scrape(source: str | None, scrape_all: bool, dry_run: bool):
    """Run scraper for one or all sources."""
    from ingestion.adapters import get_adapter, ADAPTER_MAP
    from ingestion.storage import save_raw_listings, update_source_run

    if not source and not scrape_all:
        click.echo("Error: specify --source <slug> or --all-sources")
        click.echo(f"Available adapters: {list(ADAPTER_MAP.keys())}")
        sys.exit(1)

    slugs = list(ADAPTER_MAP.keys()) if scrape_all else [source]

    for slug in slugs:
        click.echo(f"\n{'='*60}")
        click.echo(f"  Scraping: {slug}")
        click.echo(f"{'='*60}")

        start = time.time()
        try:
            adapter = get_adapter(slug)

            if dry_run:
                urls = adapter.get_listing_urls()
                click.echo(f"  Found {len(urls)} URLs (dry run, not extracting)")
                for url in urls[:10]:
                    click.echo(f"    → {url}")
                if len(urls) > 10:
                    click.echo(f"    ... and {len(urls) - 10} more")
                adapter.close()
                continue

            with adapter:
                listings = adapter.run()

            duration_ms = int((time.time() - start) * 1000)

            if listings:
                inserted, updated = save_raw_listings(listings)
                click.echo(
                    f"  ✓ {len(listings)} listings extracted "
                    f"({inserted} new, {updated} updated) "
                    f"in {duration_ms}ms"
                )
                update_source_run(slug, "success", len(listings), 0, duration_ms)
            else:
                click.echo(f"  ⚠ No listings extracted from {slug}")
                update_source_run(slug, "empty", 0, 0, duration_ms)

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            click.echo(f"  ✗ Error scraping {slug}: {e}")
            logger.exception(f"Scrape failed for {slug}")
            try:
                update_source_run(slug, "failed", 0, 1, duration_ms)
            except Exception:
                pass  # DB might not be set up yet


@cli.command("list-sources")
def list_sources():
    """List all registered source adapters."""
    from ingestion.adapters import ADAPTER_MAP

    click.echo("\nRegistered adapters:")
    for slug, cls in ADAPTER_MAP.items():
        click.echo(f"  {slug:25s} → {cls.__name__}")


@cli.command()
def stats():
    """Show database record counts."""
    from ingestion.db import execute

    try:
        raw = execute("SELECT count(*) as count FROM raw_listings")
        props = execute("SELECT count(*) as count FROM properties")
        pending = execute(
            "SELECT count(*) as count FROM properties WHERE admin_status = 'pending_review'"
        )
        published = execute(
            "SELECT count(*) as count FROM properties WHERE listing_status = 'published'"
        )

        click.echo("\nDatabase stats:")
        click.echo(f"  Raw listings:        {raw[0]['count']}")
        click.echo(f"  Properties:          {props[0]['count']}")
        click.echo(f"  Pending review:      {pending[0]['count']}")
        click.echo(f"  Published:           {published[0]['count']}")

        # Per-source breakdown
        by_source = execute(
            "SELECT source_slug, count(*) as count FROM raw_listings GROUP BY source_slug ORDER BY count DESC"
        )
        if by_source:
            click.echo("\n  By source:")
            for row in by_source:
                click.echo(f"    {row['source_slug']:25s} {row['count']}")

    except Exception as e:
        click.echo(f"  Error connecting to database: {e}")
        click.echo("  Have you run schema.sql and set DATABASE_URL in .env?")


@cli.command("test-adapter")
@click.argument("slug")
@click.option("--limit", "-n", default=3, help="Number of listings to extract")
def test_adapter(slug: str, limit: int):
    """Test an adapter by extracting a few listings without saving to DB."""
    from ingestion.adapters import get_adapter
    import json

    click.echo(f"\nTesting adapter: {slug}")

    adapter = get_adapter(slug)

    click.echo("Fetching listing URLs...")
    urls = adapter.get_listing_urls()
    click.echo(f"Found {len(urls)} URLs.\n")

    if not urls:
        click.echo("No URLs found. Check the adapter.")
        return

    for i, url in enumerate(urls[:limit]):
        click.echo(f"--- Listing {i+1}: {url} ---")
        try:
            listing = adapter.extract_listing(url)
            if listing:
                click.echo(f"  Title:      {listing.title}")
                click.echo(f"  Price:      {listing.price_raw} (¥{listing.price_jpy:,})" if listing.price_jpy else f"  Price:      {listing.price_raw}")
                click.echo(f"  Prefecture: {listing.prefecture}")
                click.echo(f"  City:       {listing.city}")
                click.echo(f"  Rooms:      {listing.rooms}")
                click.echo(f"  Year Built: {listing.year_built}")
                click.echo(f"  Size:       {listing.building_sqm} sqm")
                click.echo(f"  Images:     {len(listing.image_urls)}")
                if listing.image_urls:
                    click.echo(f"    First:    {listing.image_urls[0][:80]}...")
                click.echo(f"  Desc:       {(listing.description or '')[:120]}...")
                click.echo()
            else:
                click.echo("  (returned None)")
        except Exception as e:
            click.echo(f"  Error: {e}")
            logger.exception(f"Error extracting {url}")

        if i < limit - 1:
            time.sleep(2)

    adapter.close()


@cli.command()
@click.option("--skip-translate", is_flag=True, help="Skip LLM translation step")
@click.option("--skip-llm", is_flag=True, help="Skip all LLM-dependent steps")
@click.option("--limit", "-n", default=500, help="Max records per stage")
def pipeline(skip_translate: bool, skip_llm: bool, limit: int):
    """Run the full enrichment pipeline (normalize → translate → dedupe → hazard → lifestyle → quality → WTK)."""
    from ingestion.pipeline.orchestrate import run_full_pipeline

    click.echo("\n🚀 Running full enrichment pipeline...\n")
    results = run_full_pipeline(
        skip_translate=skip_translate or skip_llm,
        skip_llm=skip_llm,
        limit=limit,
    )

    click.echo("\n📊 Pipeline Results:")
    for stage, count in results.items():
        click.echo(f"  {stage:25s} {count}")


@cli.command()
@click.option("--limit", "-n", default=500)
def normalize(limit: int):
    """Run normalization: raw_listings → properties."""
    from ingestion.pipeline.normalize import normalize_all
    count = normalize_all(limit=limit)
    click.echo(f"  Normalized {count} listings.")


@cli.command()
@click.option("--limit", "-n", default=50)
def translate(limit: int):
    """Run LLM translation on untranslated properties."""
    from ingestion.pipeline.translate import translate_all
    count = translate_all(limit=limit)
    click.echo(f"  Translated {count} properties.")


@cli.command()
def dedupe():
    """Compute dedupe fingerprints and report duplicates."""
    from ingestion.pipeline.dedupe import (
        compute_fingerprints,
        find_duplicates,
        print_duplicate_report,
    )
    compute_fingerprints()
    clusters = find_duplicates()
    print_duplicate_report(clusters)


@cli.command()
@click.option("--limit", "-n", default=500)
def hazard(limit: int):
    """Run hazard enrichment on properties."""
    from ingestion.pipeline.hazard import enrich_hazard_all
    count = enrich_hazard_all(limit=limit)
    click.echo(f"  Enriched hazard data for {count} properties.")


@cli.command()
@click.option("--limit", "-n", default=500)
def lifestyle(limit: int):
    """Run lifestyle tagging on properties."""
    from ingestion.pipeline.lifestyle import tag_lifestyle_all
    count = tag_lifestyle_all(limit=limit)
    click.echo(f"  Tagged {count} properties.")


@cli.command()
@click.option("--limit", "-n", default=500)
def quality(limit: int):
    """Run quality scoring and What-to-Know generation."""
    from ingestion.pipeline.quality import score_quality_all, generate_what_to_know_all
    scored = score_quality_all(limit=limit)
    wtk = generate_what_to_know_all(limit=min(limit, 50))
    click.echo(f"  Scored {scored}, generated WTK for {wtk} properties.")


@cli.command("review-queue")
@click.option("--limit", "-n", default=20)
def review_queue(limit: int):
    """Show properties pending admin review, sorted by quality score."""
    from ingestion.db import execute

    try:
        rows = execute(
            """
            SELECT id, title_en, original_title, prefecture, city,
                   price_display, quality_score, admin_status,
                   freshness_label, original_url
            FROM properties
            WHERE admin_status = 'pending_review'
            ORDER BY quality_score DESC
            LIMIT %s
            """,
            (limit,),
        )

        if not rows:
            click.echo("\n  No properties pending review. ✓")
            return

        click.echo(f"\n  📋 Admin Review Queue ({len(rows)} properties):\n")
        for i, row in enumerate(rows, 1):
            title = row.get("title_en") or row.get("original_title") or "Untitled"
            price = row.get("price_display") or "No price"
            q = row.get("quality_score") or 0
            click.echo(f"  {i:3d}. [{q:.0%}] {title[:55]}")
            click.echo(f"       {row.get('prefecture', '?')}, {row.get('city', '?')} | {price}")
            click.echo(f"       {row.get('original_url', '')}")
            click.echo()

    except Exception as e:
        click.echo(f"  Error: {e}")


if __name__ == "__main__":
    cli()
