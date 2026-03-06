"""
Scraper adapter for oldhousesjapan.com

Site structure (Webflow-hosted):
  - /all — lists all properties as linked cards
  - /properties-2/{slug} — detail page per property
  - English-language content
  - Prices in USD
  - Images on cdn.prod.website-files.com

Strategy:
  1. Parse the /all page to get listing URLs + card-level data
     (prefecture, title extracted from headings and link text)
  2. Fetch each detail page for: description, images, price,
     property specs, and location
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

from ingestion.base_adapter import BaseAdapter
from ingestion.models import RawListing
from ingestion.utils import clean_text, make_absolute_url, normalize_prefecture

logger = logging.getLogger(__name__)


class OldHousesJapanAdapter(BaseAdapter):
    slug = "old-houses-japan"
    base_url = "https://oldhousesjapan.com"

    def get_listing_urls(self) -> list[str]:
        """Get all property detail page URLs from the /all page."""
        html = self.fetch_page(f"{self.base_url}/all")
        soup = BeautifulSoup(html, "lxml")

        urls = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/properties-2/" not in href:
                continue
            full_url = make_absolute_url(self.base_url, href)
            # Normalize to avoid duplicates from www vs non-www
            canonical = full_url.replace("https://www.", "https://")
            if canonical not in seen:
                seen.add(canonical)
                urls.append(full_url)

        logger.info(f"[{self.slug}] Found {len(urls)} property URLs on /all page.")
        return urls

    def extract_listing(self, url: str) -> Optional[RawListing]:
        """Extract property data from a detail page."""
        html = self.fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        # ── Slug-based ID ────────────────────────────────
        slug = url.rstrip("/").split("/")[-1]

        # ── Title ────────────────────────────────────────
        title = self._extract_title(soup, slug)

        # ── Description ─────────────────────────────────
        description = self._extract_description(soup)

        # ── Location (from sub-heading below h1) ─────────
        prefecture, city, address_raw = self._extract_location(soup)

        # ── Price ────────────────────────────────────────
        price_usd, price_jpy = self._extract_price(soup)

        # ── Property specs from body text ────────────────
        rooms = self._extract_rooms(soup)
        year_built = self._extract_year_built(soup)
        building_sqm, land_sqm = self._extract_areas(soup)
        floors = self._extract_floors(soup)

        # ── Images (gallery only, not nearby homes) ──────
        image_urls = self._extract_images(soup)

        return RawListing(
            source_slug=self.slug,
            source_listing_id=slug,
            source_url=url,
            title=title,
            description=description,
            price_raw=f"${price_usd:,}" if price_usd else None,
            price_jpy=price_jpy,
            prefecture=prefecture,
            city=city,
            address_raw=address_raw,
            building_sqm=building_sqm,
            land_sqm=land_sqm,
            year_built=year_built,
            rooms=rooms,
            floors=floors,
            image_urls=image_urls,
            building_type="detached",
        )

    # ── Private extraction methods ───────────────────────

    def _extract_title(self, soup: BeautifulSoup, slug: str) -> str:
        """Get title from og:title or h1."""
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            raw = og["content"]
            # Strip suffixes like " - Real Estate Listing in English..."
            return raw.split(" - ")[0].strip() if " - " in raw else raw.strip()
        h1 = soup.find("h1")
        if h1:
            return clean_text(h1.get_text()) or slug.replace("-", " ").title()
        return slug.replace("-", " ").title()

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Get the main property description from rich text blocks."""
        # Look for rich text content blocks (Webflow class)
        for block in soup.select(".w-richtext"):
            # Skip blocks that are inside property cards (nearby homes)
            if block.find_parent(class_="property-card"):
                continue
            text = clean_text(block.get_text())
            if text and len(text) > 80:
                # Strip leading heading text that leaks into content
                for prefix in [
                    "Property Overview",
                    "Key Features",
                    "Location & Surroundings",
                ]:
                    if text.startswith(prefix):
                        text = text[len(prefix) :].strip()
                return text

        # Fallback: og:description
        og = soup.find("meta", property="og:description")
        if og and og.get("content"):
            return clean_text(og["content"])

        return None

    def _extract_location(
        self, soup: BeautifulSoup
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract location from page.
        Strategy:
          1. Look for structured location element below h1
          2. Parse description text for city/prefecture mentions
          3. Search the full page for prefecture names
        """
        from ingestion.config import PREFECTURES

        prefecture = None
        city = None
        address_raw = None

        h1 = soup.find("h1")

        # Strategy 1: Look for location text in elements near h1
        if h1:
            for sibling in h1.find_next_siblings():
                text = clean_text(sibling.get_text())
                if not text or len(text) < 3:
                    continue
                if len(text) > 200:
                    break

                # Check for prefecture in this element
                for pref_name in PREFECTURES:
                    if pref_name.lower() in text.lower():
                        prefecture = pref_name
                        parts = [p.strip() for p in text.replace(" ,", ",").split(",")]
                        if len(parts) >= 2:
                            city = parts[0].strip()
                            address_raw = text
                        break
                if prefecture:
                    break

        # Strategy 2: Parse description and title text for location
        if not prefecture:
            # Gather text from description + title
            desc = ""
            for block in soup.select(".w-richtext"):
                if block.find_parent(class_="property-card"):
                    continue
                desc = block.get_text()
                break

            title_text = ""
            if h1:
                title_text = h1.get_text()

            search_text = f"{title_text} {desc}"

            # Look for "in CityName, Prefecture" patterns
            for pref_name in PREFECTURES:
                if pref_name in search_text:
                    prefecture = pref_name
                    # Try to find city near the prefecture mention
                    city_pattern = rf"in\s+([A-Z][a-zA-Zō-]+(?:\s+[A-Z][a-zA-Zō-]+)*).*?{pref_name}"
                    city_match = re.search(city_pattern, search_text)
                    if city_match:
                        city = city_match.group(1).strip()
                    break

        # Strategy 3: Check OG description for prefecture
        if not prefecture:
            og = soup.find("meta", property="og:description")
            if og:
                og_text = og.get("content", "")
                for pref_name in PREFECTURES:
                    if pref_name in og_text:
                        prefecture = pref_name
                        break

        return prefecture, city, address_raw

    def _extract_price(
        self, soup: BeautifulSoup
    ) -> tuple[Optional[int], Optional[int]]:
        """
        Extract price. Look for JPY first (more accurate), fall back to USD.
        Avoid grabbing unrelated numbers from page chrome.
        """
        full_text = soup.get_text()

        # Try JPY price: "¥100,000" or "Price: ¥100,000"
        jpy_match = re.search(r"[¥￥]\s*([\d,]+)", full_text)
        if jpy_match:
            try:
                jpy = int(jpy_match.group(1).replace(",", ""))
                if jpy >= 1:  # some are literally 1 yen
                    usd = int(jpy / 150) if jpy > 0 else 0
                    return usd, jpy
            except ValueError:
                pass

        # Try USD price from structured card-like elements
        # Look for price near the top of the page, not in footer/nav
        # The h1 and its siblings contain the property header info
        h1 = soup.find("h1")
        if h1:
            # Search within the header section (h1's parent and siblings)
            header_parent = h1.parent
            if header_parent:
                header_text = header_parent.get_text()
                usd_match = re.search(r"\$\s*([\d,]+)", header_text)
                if usd_match:
                    try:
                        usd = int(usd_match.group(1).replace(",", ""))
                        if 1 <= usd <= 10_000_000:
                            return usd, int(usd * 150)
                    except ValueError:
                        pass

        # Broader USD search but with tighter constraints
        # Only match prices that look reasonable for houses
        usd_matches = re.findall(r"\$\s*([\d,]+)", full_text)
        for match in usd_matches:
            try:
                val = int(match.replace(",", ""))
                if 1 <= val <= 5_000_000:
                    return val, int(val * 150)
            except ValueError:
                continue

        return None, None

    def _extract_rooms(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract room layout like 3LDK, 6DK, 10K etc."""
        # Only search in the main property content, not recommendations
        main_section = self._get_main_content(soup)
        text = main_section.get_text() if main_section else soup.get_text()

        # Japanese room layout pattern
        match = re.search(r"\b(\d{1,2}[LDKS]{1,4}(?:\+\w+)?)\b", text)
        return match.group(1) if match else None

    def _extract_year_built(self, soup: BeautifulSoup) -> Optional[int]:
        """
        Extract year built from property description.
        Avoid matching copyright years, current year, etc.
        """
        main_section = self._get_main_content(soup)
        text = main_section.get_text() if main_section else ""

        # Look for explicit "built in XXXX" patterns first
        built_match = re.search(
            r"built\s+in\s+(19[0-9]{2}|20[0-1][0-9])", text, re.IGNORECASE
        )
        if built_match:
            return int(built_match.group(1))

        # Look for "XXXX年" (Japanese year) in the content
        year_jp_match = re.search(r"(19[0-9]{2}|20[0-1][0-9])年", text)
        if year_jp_match:
            return int(year_jp_match.group(1))

        # Look for "Year Built: XXXX" or similar
        yb_match = re.search(
            r"(?:year\s*built|constructed|建築)\s*:?\s*(19[0-9]{2}|20[0-1][0-9])",
            text,
            re.IGNORECASE,
        )
        if yb_match:
            return int(yb_match.group(1))

        return None

    def _extract_areas(
        self, soup: BeautifulSoup
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Extract building and land areas.
        Patterns: "184.83 m² home", "425.52 m² lot", "XX sqm", "XX sq ft"
        """
        main_section = self._get_main_content(soup)
        text = main_section.get_text() if main_section else ""

        building_sqm = None
        land_sqm = None

        # m² patterns
        m2_matches = re.findall(
            r"([\d,]+\.?\d*)\s*(?:m²|㎡|sqm)\s*(\w*)", text, re.IGNORECASE
        )
        for val_str, context in m2_matches:
            try:
                val = float(val_str.replace(",", ""))
                if val < 0.1 or val > 100_000:
                    continue
                ctx = context.lower()
                if ctx in ("home", "house", "building", "floor"):
                    building_sqm = val
                elif ctx in ("lot", "land", "site", "plot"):
                    land_sqm = val
                elif building_sqm is None:
                    building_sqm = val  # first match
                elif land_sqm is None:
                    land_sqm = val
            except ValueError:
                continue

        # sq ft pattern (convert to sqm)
        if not building_sqm:
            sqft_matches = re.findall(
                r"([\d,]+\.?\d*)\s*(?:sq\.?\s*ft|square\s*feet)", text, re.IGNORECASE
            )
            for val_str in sqft_matches:
                try:
                    sqft = float(val_str.replace(",", ""))
                    if 10 <= sqft <= 1_000_000:
                        sqm = round(sqft * 0.0929, 1)
                        if building_sqm is None:
                            building_sqm = sqm
                        elif land_sqm is None:
                            land_sqm = sqm
                except ValueError:
                    continue

        # 坪 (tsubo) pattern
        tsubo_matches = re.findall(r"([\d,]+\.?\d*)\s*坪", text)
        for val_str in tsubo_matches:
            try:
                val = float(val_str.replace(",", "")) * 3.306
                if building_sqm is None:
                    building_sqm = round(val, 1)
                elif land_sqm is None:
                    land_sqm = round(val, 1)
            except ValueError:
                continue

        return building_sqm, land_sqm

    def _extract_floors(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract number of floors/stories."""
        main_section = self._get_main_content(soup)
        text = main_section.get_text() if main_section else ""

        match = re.search(
            r"(\d)\s*(?:-?\s*stor(?:y|ies)|floors?|階建)", text, re.IGNORECASE
        )
        if match:
            val = int(match.group(1))
            if 1 <= val <= 5:
                return val
        return None

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        """
        Extract gallery images only. Exclude:
        - Images inside .property-card (nearby homes section)
        - Very small images (icons, logos)
        - Duplicate URLs
        """
        images = []
        seen = set()

        # Look for lightbox gallery images first (most reliable)
        for el in soup.select(".w-lightbox img, .w-lightbox [style*='background-image']"):
            # Skip if inside a property-card (recommendations)
            if el.find_parent(class_="property-card"):
                continue
            url = self._get_image_url(el)
            if url and url not in seen:
                seen.add(url)
                images.append(url)

        # Also check for gallery images with Webflow CDN URLs
        if not images:
            for img in soup.find_all("img"):
                if img.find_parent(class_="property-card"):
                    continue
                src = img.get("src", "") or img.get("data-src", "")
                if "cdn.prod.website-files.com" not in src:
                    continue
                # Skip small icons
                width = img.get("width")
                if width and str(width).isdigit() and int(width) < 200:
                    continue
                full_url = make_absolute_url(self.base_url, src)
                if full_url not in seen:
                    seen.add(full_url)
                    images.append(full_url)

        return images

    def _get_image_url(self, el: Tag) -> Optional[str]:
        """Get image URL from an img tag or background-image style."""
        if el.name == "img":
            return el.get("src") or el.get("data-src")
        style = el.get("style", "")
        match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
        return match.group(1) if match else None

    def _get_main_content(self, soup: BeautifulSoup) -> Optional[Tag]:
        """
        Get the main property content area, excluding
        footer, nav, and 'nearby similar homes' sections.
        Returns the main content section or the body as fallback.
        """
        # Try to find the section containing "Property Overview" or "Key Features"
        for heading_text in ["Property Overview", "Key Features", "Location"]:
            heading = soup.find(
                ["h1", "h2", "h3"], string=re.compile(heading_text, re.IGNORECASE)
            )
            if heading:
                # Return the parent section/div
                parent = heading.find_parent(["section", "div"])
                if parent:
                    return parent

        # Fallback: return body but try to exclude footer and nav
        body = soup.find("body")
        return body
