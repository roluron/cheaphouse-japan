"""
Placeholder adapter for cheaphousesjapan.com

NOTE: This site is primarily a newsletter with no individual listing pages.
The homepage shows featured listing images that link to the newsletter signup.
This adapter is a stub — it cannot scrape structured listings.

Options:
  1. Partner with the newsletter owner to get listing data
  2. Parse newsletter emails if subscribed
  3. Skip this source until they add individual listing pages
"""

from __future__ import annotations

import logging
from typing import Optional

from ingestion.base_adapter import BaseAdapter
from ingestion.models import RawListing

logger = logging.getLogger(__name__)


class CheapHousesJapanAdapter(BaseAdapter):
    slug = "cheap-houses-japan"
    base_url = "https://cheaphousesjapan.com"

    def get_listing_urls(self) -> list[str]:
        logger.warning(
            f"[{self.slug}] This source is a newsletter site with no "
            f"individual listing pages. Adapter is a stub."
        )
        return []

    def extract_listing(self, url: str) -> Optional[RawListing]:
        return None
