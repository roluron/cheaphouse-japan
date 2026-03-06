"""
Base adapter class. Every source adapter extends this.
Handles the common run loop: get URLs, extract each, handle errors.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from ingestion.config import HTTP_TIMEOUT_SECONDS, SCRAPE_DELAY_SECONDS, USER_AGENT
from ingestion.models import RawListing

logger = logging.getLogger(__name__)


class BaseAdapter:
    """
    Abstract base for scraper adapters.

    Subclasses must set:
        slug: str — matches the source registry slug
        base_url: str — root URL of the source site

    Subclasses must implement:
        get_listing_urls() -> list[str]
        extract_listing(url: str) -> Optional[RawListing]
    """

    slug: str = ""
    base_url: str = ""

    def __init__(self):
        self.client = httpx.Client(
            timeout=HTTP_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        self.delay = SCRAPE_DELAY_SECONDS

    def get_listing_urls(self) -> list[str]:
        """
        Return all detail-page URLs to scrape.
        Typically: paginate through listing index pages, collect links.
        """
        raise NotImplementedError

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """
        Fetch one detail page and parse it into a RawListing.
        Return None if the page can't be parsed (deleted, broken, etc.)
        """
        raise NotImplementedError

    def fetch_page(self, url: str) -> str:
        """
        GET a URL with retry logic. Returns HTML text.
        Raises on persistent failure.
        """
        last_error = None
        for attempt in range(3):
            try:
                resp = self.client.get(url)
                resp.raise_for_status()
                return resp.text
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                last_error = e
                wait = (attempt + 1) * 2
                logger.warning(
                    f"[{self.slug}] Attempt {attempt + 1} failed for {url}: {e}. "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)
        raise last_error  # type: ignore[misc]

    def run(self) -> list[RawListing]:
        """
        Full scrape run: get listing URLs, extract each, return results.
        Skips individual listing failures without aborting the run.
        """
        logger.info(f"[{self.slug}] Starting scrape run...")

        urls = self.get_listing_urls()
        logger.info(f"[{self.slug}] Found {len(urls)} listing URLs.")

        results: list[RawListing] = []
        errors = 0

        for i, url in enumerate(urls):
            try:
                listing = self.extract_listing(url)
                if listing:
                    results.append(listing)
            except Exception as e:
                errors += 1
                logger.error(f"[{self.slug}] Error extracting {url}: {e}")

            # Rate limiting
            if i < len(urls) - 1:
                time.sleep(self.delay)

            # Progress log every 25 listings
            if (i + 1) % 25 == 0:
                logger.info(
                    f"[{self.slug}] Progress: {i + 1}/{len(urls)} "
                    f"({len(results)} ok, {errors} errors)"
                )

        logger.info(
            f"[{self.slug}] Run complete: {len(results)} listings extracted, "
            f"{errors} errors out of {len(urls)} URLs."
        )
        return results

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
