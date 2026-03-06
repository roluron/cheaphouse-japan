# PROMPT À COLLER DANS ANTIGRAVITY — Ajouter 2 nouvelles sources de données

```
I need to add 2 new data source adapters to my ingestion pipeline. The pipeline is in /ingestion/ and already has working adapters for Old Houses Japan and All Akiyas. Look at the existing code to understand the patterns:

- base_adapter.py — BaseAdapter class all adapters extend
- models.py — RawListing dataclass (the common format)
- adapters/old_houses_japan.py — working reference adapter
- adapters/all_akiyas.py — another working reference adapter
- config.py — config, USER_AGENT, delays
- db.py — database helpers
- storage.py — storage helpers
- run.py — CLI entry point

I need TWO new adapters:

---

## ADAPTER 1: Akiya-Mart (akiya-mart.com)

I have a paid account on akiya-mart.com. When logged in, I can see full listing pages with price, photos, location, and property details.

The site returns 403 for unauthenticated requests, so this adapter needs to handle authentication.

### What to build:

Create ingestion/adapters/akiya_mart.py

1. Authentication approach — use one of these (try in order):
   a. Cookie-based: I'll provide my session cookies from the browser. Store them in .env as AKIYA_MART_COOKIES. Send them with every request.
   b. If cookies don't work: use login credentials (AKIYA_MART_EMAIL + AKIYA_MART_PASSWORD in .env) and do a POST login flow to get a session, then scrape with that session.

2. Add to .env.example:
   AKIYA_MART_COOKIES=    # Copy from browser DevTools > Application > Cookies
   AKIYA_MART_EMAIL=      # Fallback: login credentials
   AKIYA_MART_PASSWORD=   # Fallback: login credentials

3. Scraping strategy:
   - First, explore the site structure when logged in. Look for listing index pages, pagination patterns, category/prefecture browsing.
   - Extract all listing URLs from index/category pages
   - For each listing, extract: title, price (JPY), prefecture, city, address, land area (sqm), building area (sqm), year built, rooms, structure type, condition/notes, images, description
   - Map everything to the RawListing model (same as other adapters)

4. Important: respect rate limits. Use the same SCRAPE_DELAY_SECONDS (default 2s) as other adapters. We're logged in as a paying user — don't hammer the server.

5. Register the adapter in adapters/__init__.py and in run.py's ADAPTER_MAP.

6. Add to seed_sources.sql:
   INSERT INTO sources (name, slug, base_url, source_type, scrape_method, refresh_hours, is_active)
   VALUES ('Akiya Mart', 'akiya-mart', 'https://akiya-mart.com', 'website', 'http_authenticated', 24, true)
   ON CONFLICT (slug) DO NOTHING;

---

## ADAPTER 2: CheapHousesJapan Newsletter (cheaphousesjapan.com)

This site has no browsable listing pages — it only operates via email newsletter. But I receive their newsletters in my Gmail account.

### What to build:

Create ingestion/adapters/cheap_houses_newsletter.py

This adapter uses the Gmail API to fetch and parse newsletter emails.

1. Gmail API setup:
   - Use Google's gmail API via google-api-python-client + google-auth-oauthlib
   - Add these to requirements.txt
   - Create a setup script or instructions for OAuth2 flow (I'll need to authorize once and save the token)
   - Store credentials: GMAIL_CREDENTIALS_FILE path in .env, token saved as gmail_token.json

2. Email fetching strategy:
   - Search Gmail for emails from CheapHousesJapan (search query: "from:cheaphousesjapan.com" or whatever their sender address is — check the email headers)
   - Fetch emails from the last 7 days (configurable via NEWSLETTER_DAYS_BACK in .env, default 7)
   - Parse the HTML body of each email

3. Email parsing:
   - CheapHousesJapan newsletters typically contain multiple property listings in a single email
   - Each listing usually has: a title, a photo, a price, a location, a short description, and a link to the source
   - Parse the HTML to extract each property block
   - For each property: extract title, price, location, description, image URL, source link
   - If the source link points to another site (like a municipal akiya bank), store it as original_url

4. Map everything to RawListing model. Use source_slug = 'cheap-houses-newsletter'. Generate source_listing_id from a hash of (title + price + location) since newsletters don't have stable IDs.

5. Register the adapter in adapters/__init__.py and run.py.

6. Add to seed_sources.sql:
   INSERT INTO sources (name, slug, base_url, source_type, scrape_method, refresh_hours, is_active)
   VALUES ('CheapHousesJapan Newsletter', 'cheap-houses-newsletter', 'https://cheaphousesjapan.com', 'newsletter', 'gmail_api', 168, true)
   ON CONFLICT (slug) DO NOTHING;

---

## IMPORTANT NOTES

- Follow the EXACT same patterns as the existing adapters (extend BaseAdapter, use self.client for HTTP, return list of RawListing, etc.)
- Both adapters must be runnable via the CLI: `python -m ingestion.run scrape --source akiya-mart` and `python -m ingestion.run scrape --source cheap-houses-newsletter`
- Add good error handling — if auth fails, log clearly and stop (don't scrape unauthenticated)
- Add progress logging (every 25 listings)
- Update requirements.txt with any new dependencies
- Update the existing adapter in adapters/cheap_houses_japan.py — either replace it with the newsletter version or keep both and disable the old stub

For the Gmail adapter: also create a one-time setup script at ingestion/setup_gmail.py that handles the OAuth2 flow and saves the token. Document the steps in a comment at the top of the adapter file.
```
