"""
Redfin — major US real estate portal.
BEST APPROACH: Redfin offers CSV data download from search results!
No scraping needed — just download the CSV.
Target: houses under $100K in target states.
"""

from __future__ import annotations

import csv
import io
import logging
import time
from typing import Optional

from ingestion.adapters.usa.base_usa import USABaseAdapter
from ingestion.models import RawListing
from ingestion.utils_usa import parse_price_usd, sqft_to_sqm, usd_to_jpy

logger = logging.getLogger(__name__)


class RedfinUSAdapter(USABaseAdapter):
    """Adapter for Redfin — CSV download of cheap US houses."""

    slug = "redfin-us"
    base_url = "https://www.redfin.com"

    # CSV download URL template
    CSV_URL_TEMPLATE = (
        "https://www.redfin.com/stingray/api/gis-csv"
        "?al=1&market=false&max_price=100000"
        "&num_homes=350&ord=redfin-recommended-asc"
        "&page_number=1&property_type=house"
        "&region_id={region_id}&region_type=2&status=9"
        "&uipt=1&v=8"
    )

    # Region IDs for target states (from Redfin)
    STATE_REGION_IDS = {
        "OH": 35,   # Ohio
        "MI": 23,   # Michigan
        "IN": 14,   # Indiana
        "PA": 39,   # Pennsylvania
        "WV": 49,   # West Virginia
        "MS": 25,   # Mississippi
        "AL": 1,    # Alabama
        "AR": 4,    # Arkansas
        "KS": 16,   # Kansas
        "MO": 26,   # Missouri
    }

    REQUEST_DELAY = 5

    def __init__(self):
        super().__init__()
        self.delay = self.REQUEST_DELAY
        # Redfin needs a browser-like user agent
        self.client.headers.update({
            "Accept": "text/csv,text/plain,*/*",
            "Referer": "https://www.redfin.com/",
        })

    def get_listing_urls(self) -> list[str]:
        """
        For Redfin CSV, we don't fetch individual URLs.
        Instead, we build CSV download URLs per state.
        Returns CSV URLs to process.
        """
        csv_urls = []
        for state, region_id in self.STATE_REGION_IDS.items():
            url = self.CSV_URL_TEMPLATE.format(region_id=region_id)
            csv_urls.append(url)
        logger.info(f"[{self.slug}] {len(csv_urls)} states to download CSVs from")
        return csv_urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """
        For Redfin, this is called with a CSV URL.
        We download and parse the CSV, returning listings one at a time.
        Since BaseAdapter.run() expects one listing per URL, we use
        a special approach here.
        """
        # This method won't be called in the normal flow.
        # Instead, we override run() to handle CSV batch processing.
        return None

    def run(self) -> list[RawListing]:
        """
        Override run() for CSV batch processing.
        Downloads one CSV per state, parses all rows into listings.
        """
        logger.info(f"[{self.slug}] Starting CSV download run...")
        results: list[RawListing] = []
        errors = 0

        for state, region_id in self.STATE_REGION_IDS.items():
            csv_url = self.CSV_URL_TEMPLATE.format(region_id=region_id)
            logger.info(f"[{self.slug}] Downloading CSV for {state} (region {region_id})...")

            try:
                resp = self.client.get(csv_url)
                resp.raise_for_status()
                csv_text = resp.text

                if not csv_text.strip() or "<!DOCTYPE" in csv_text[:100]:
                    logger.warning(f"[{self.slug}] {state}: got HTML instead of CSV, skipping")
                    errors += 1
                    continue

                listings = self._parse_csv(csv_text, state)
                results.extend(listings)
                logger.info(f"[{self.slug}] {state}: parsed {len(listings)} listings")

            except Exception as e:
                errors += 1
                logger.error(f"[{self.slug}] {state} CSV download failed: {e}")

            time.sleep(self.delay)

        logger.info(
            f"[{self.slug}] Run complete: {len(results)} listings from "
            f"{len(self.STATE_REGION_IDS)} states ({errors} errors)"
        )
        return results

    def _parse_csv(self, csv_text: str, state: str) -> list[RawListing]:
        """Parse a Redfin CSV into RawListing objects."""
        listings: list[RawListing] = []

        reader = csv.DictReader(io.StringIO(csv_text))

        for row in reader:
            try:
                listing = self._row_to_listing(row, state)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"[{self.slug}] Row parse error: {e}")
                continue

        return listings

    def _row_to_listing(self, row: dict, state: str) -> Optional[RawListing]:
        """Convert one CSV row to a RawListing."""
        # Price
        price_str = row.get("PRICE", "")
        price_usd = parse_price_usd(price_str) if price_str else None
        if not price_usd or price_usd > self.PRICE_THRESHOLD:
            return None

        # URL
        url = row.get("URL", "")
        if not url:
            return None
        if not url.startswith("http"):
            url = f"https://www.redfin.com{url}"

        # Address
        address = row.get("ADDRESS", "")
        city = row.get("CITY", "")
        state_col = row.get("STATE OR PROVINCE", state)
        zip_code = row.get("ZIP OR POSTAL CODE", "")
        address_raw = f"{address}, {city}, {state_col} {zip_code}".strip(", ")

        # Title
        title = f"{address}, {city}, {state_col}" if address else f"Property in {city}, {state_col}"

        # Property details
        sqft_str = row.get("SQUARE FEET", "")
        sqft = None
        if sqft_str:
            try:
                sqft = float(sqft_str)
            except (ValueError, TypeError):
                pass
        building_sqm = sqft_to_sqm(sqft) if sqft else None

        lot_str = row.get("LOT SIZE", "")
        land_sqm = None
        if lot_str:
            try:
                # Lot size in Redfin CSV is typically in sqft
                land_sqm = sqft_to_sqm(float(lot_str))
            except (ValueError, TypeError):
                pass

        year_built = None
        yb_str = row.get("YEAR BUILT", "")
        if yb_str:
            try:
                year_built = int(float(yb_str))
            except (ValueError, TypeError):
                pass

        # Beds/Baths
        beds = row.get("BEDS", "")
        baths = row.get("BATHS", "")
        rooms = None
        if beds or baths:
            rooms = f"{beds}bd/{baths}ba"

        # Lat/Lng
        lat = None
        lng = None
        try:
            lat = float(row.get("LATITUDE", ""))
            lng = float(row.get("LONGITUDE", ""))
        except (ValueError, TypeError):
            pass

        # HOA
        hoa_str = row.get("HOA/MONTH", "")
        hoa_monthly = None
        if hoa_str:
            try:
                hoa_monthly = int(float(hoa_str.replace("$", "").replace(",", "")))
            except (ValueError, TypeError):
                pass

        price_jpy = usd_to_jpy(price_usd)

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=url.rstrip("/").split("/")[-1],
            title=title,
            price_raw=f"${price_usd:,}",
            price_jpy=price_jpy,
            prefecture=state_col,
            city=city,
            address_raw=address_raw,
            latitude=lat,
            longitude=lng,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            year_built=year_built,
            rooms=rooms,
            building_type=row.get("PROPERTY TYPE", "house").lower(),
            image_urls=[],  # CSV doesn't include images
            raw_data={
                "country": "usa",
                "price_usd": price_usd,
                "currency": "USD",
                "sqft": sqft,
                "hoa_monthly": hoa_monthly,
                "days_on_market": row.get("DAYS ON MARKET", ""),
                "sale_type": row.get("SALE TYPE", ""),
                "status": row.get("STATUS", ""),
            },
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with RedfinUSAdapter() as adapter:
        listings = adapter.run()
        print(f"Found {len(listings)} listings")
        for l in listings[:3]:
            print(f"  {l.title} — ${l.raw_data.get('price_usd'):,}")
