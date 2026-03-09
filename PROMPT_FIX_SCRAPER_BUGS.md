# PROMPT À COLLER DANS ANTIGRAVITY — Fix scraper bugs (bukkenfan + realestate.co.jp)

```
Auto-approve all changes and commands. Don't ask for permission.

Two scrapers have bugs from the first live run. Fix them both.

## Bug 1: bukkenfan adapter — price parsing crash

Error: `invalid literal for int() with base 10: '9280万円'`

The bukkenfan adapter is trying to convert a Japanese price string directly to int() instead of using the shared `parse_japanese_price()` helper from utils.py.

Fix in `ingestion/adapters/bukkenfan_jp.py`:
- Find ANY place where price is parsed with `int()` or `float()` directly
- Replace with `parse_japanese_price()` from `ingestion.utils`
- Make sure to `from ingestion.utils import parse_japanese_price` at the top
- Handle the case where price might be in format "9280万円", "980万", "1億2000万円", or plain "5000000"
- If parse_japanese_price returns None, try plain int conversion as fallback (for already-numeric strings)

Example fix pattern:
```python
# BEFORE (broken):
price_jpy = int(price_text)

# AFTER (correct):
from ingestion.utils import parse_japanese_price
price_jpy = parse_japanese_price(price_text)
if price_jpy is None:
    # Fallback: try as plain number
    try:
        price_jpy = int(price_text.replace(',', '').replace('円', ''))
    except (ValueError, AttributeError):
        price_jpy = None
```

Also check ALL other adapters for the same pattern — if any adapter does raw int() on price text, fix it the same way.

## Bug 2: realestate-co-jp adapter — 0 listings extracted

The realestate.co.jp adapter returned zero listings. This means either:
1. The search URL structure changed
2. The CSS selectors for listing links are wrong
3. The site is blocking our request

Debug steps:
1. Open https://realestate.co.jp/en/forsale/listing/?price_max=10000000&property_type=house in a browser
2. Inspect the actual HTML structure of the search results page
3. Find the correct CSS selectors for listing cards/links
4. Update the adapter's `get_listing_urls()` method with the correct selectors

Common issues:
- realestate.co.jp may use JavaScript rendering — if so, the static HTML from requests won't have the listings. In that case, try fetching the API endpoint directly (inspect Network tab in browser DevTools for XHR/fetch calls that return listing data as JSON).
- The URL structure may have changed — check what URL the site actually uses when you search for houses under ¥10M.
- They may have added anti-bot headers — make sure we send Accept, Accept-Language, and a realistic User-Agent.

If the site requires JavaScript rendering and cannot be scraped with simple HTTP requests, add a comment explaining this and mark the adapter as non-functional for now. We have enough sources without it.

## After fixing

Test both adapters:
```bash
cd ingestion
source venv/bin/activate
python run.py test-adapter bukkenfan --limit 3
python run.py test-adapter realestate-co-jp --limit 3
```

Both should extract listings without errors. Push to GitHub when done.
```
