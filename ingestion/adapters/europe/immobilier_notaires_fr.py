"""
Immobilier.notaires.fr adapter — official notary property database.
Direct-from-seller listings, often cheaper than agency listings.
Moderate anti-scraping. Target: houses under €100K in rural departments.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from ingestion.adapters.europe.base_europe import EuropeBaseAdapter
from ingestion.models import RawListing
from ingestion.utils import clean_text, make_absolute_url
from ingestion.utils_europe import parse_price_eur, parse_area_sqm_europe

logger = logging.getLogger(__name__)


class NotairesFrAdapter(EuropeBaseAdapter):
    """Adapter for Notaires de France — immobilier.notaires.fr."""

    slug = "notaires-fr"
    country = "france"
    currency = "EUR"
    default_language = "fr"
    base_url = "https://www.immobilier.notaires.fr"

    # Target cheap departments
    CHEAP_DEPARTMENTS = ["23", "87", "03", "58", "36", "18", "15", "19"]

    HEADERS = {
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
    }

    def __init__(self):
        super().__init__()
        self.delay = 3  # Respectful — government site
        self.client.headers.update(self.HEADERS)

    def get_listing_urls(self) -> list[str]:
        """Collect listing URLs across cheap departments."""
        urls: list[str] = []

        for dept in self.CHEAP_DEPARTMENTS:
            page = 1
            while page <= 5:
                search_url = (
                    f"{self.base_url}/annonces/immobilier-vente-maison"
                    f"?dep={dept}&price_max=100000&page={page}"
                )
                try:
                    html = self.fetch_page(search_url)
                except Exception as e:
                    logger.warning(f"[{self.slug}] Dept {dept} page {page} failed: {e}")
                    break

                soup = BeautifulSoup(html, "lxml")

                found_any = False
                for a in soup.select("a[href]"):
                    href = a.get("href", "")
                    if "/annonce/" in href or "/annonces/" in href and re.search(r'\d', href):
                        full = make_absolute_url(self.base_url, href)
                        if full not in urls:
                            urls.append(full)
                            found_any = True

                if not found_any:
                    break

                page += 1
                time.sleep(self.delay)

            time.sleep(self.delay)

        logger.info(f"[{self.slug}] Found {len(urls)} listing URLs")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract listing data from a detail page."""
        try:
            html = self.fetch_page(url)
        except Exception as e:
            logger.error(f"[{self.slug}] Failed: {url}: {e}")
            return None

        soup = BeautifulSoup(html, "lxml")

        # Title
        h1 = soup.select_one("h1")
        title = clean_text(h1.get_text()) if h1 else None
        if not title:
            return None

        # Listing ID
        id_match = re.search(r'/annonce[s]?/([^/]+)', url)
        listing_id = id_match.group(1) if id_match else url.split("/")[-1]

        # Price
        price_eur = None
        price_raw = None
        price_el = soup.select_one(".price, [class*='prix'], [class*='price']")
        if price_el:
            price_raw = clean_text(price_el.get_text())
            price_eur = parse_price_eur(price_raw)

        if not price_eur:
            # Fallback: search in text
            text = soup.get_text()
            m = re.search(r'(\d[\d\s.]+)\s*€', text)
            if m:
                price_raw = m.group(0).strip()
                price_eur = parse_price_eur(price_raw)

        price_jpy = self.price_to_jpy(price_eur) if price_eur else None

        # Location
        location_el = soup.select_one(
            ".location, [class*='localisation'], [class*='location']"
        )
        region = clean_text(location_el.get_text()) if location_el else None

        # Area
        building_sqm = None
        land_sqm = None
        text = soup.get_text()
        # Surface habitable
        m = re.search(r'(\d+[\.,]?\d*)\s*m²', text)
        if m:
            building_sqm = float(m.group(1).replace(',', '.'))
        # Terrain
        m = re.search(r'[Tt]errain[:\s]*(\d+[\.,]?\d*)\s*m²', text)
        if m:
            land_sqm = float(m.group(1).replace(',', '.'))

        # Rooms
        rooms = None
        m = re.search(r'(\d+)\s*(?:pièce|chambre|room)', text, re.IGNORECASE)
        if m:
            rooms = m.group(1)

        # Description
        desc_el = soup.select_one(
            ".description, [class*='description'], "
            "[class*='commentaire']"
        )
        description = clean_text(desc_el.get_text()[:2000]) if desc_el else None

        # Images
        images = self._extract_images(soup)

        return RawListing(
            source_slug=self.slug,
            source_url=url,
            source_listing_id=listing_id,
            country=self.country,
            title=title,
            price_jpy=price_jpy,
            price_raw=price_raw,
            prefecture=region,
            address_raw=region,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            rooms=rooms,
            description=description,
            image_urls=images,
            building_type="detached",
        )

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        """Extract property images."""
        images: list[str] = []
        for img in soup.select("img[src], img[data-src]"):
            src = img.get("data-src") or img.get("src", "")
            if not src or src.startswith("data:"):
                continue
            if any(
                skip in src.lower()
                for skip in ["logo", "icon", "avatar", "favicon", "placeholder"]
            ):
                continue
            full = make_absolute_url(self.base_url, src)
            if full not in images:
                images.append(full)
        return images[:20]
