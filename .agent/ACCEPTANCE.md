# Acceptance

- Public browse results contain only published Japan listings verified active within the last 72 hours.
- A source error changes a listing to `uncertain`; it never proves that a listing is sold or removed.
- Sold and removed records remain in the database for provenance but disappear from active browse results.
- Listing cards and details show a plain-language availability state and the last source check.
- Missing hazard data is shown as unknown and cannot pass a safe-only filter.
- Database failures never fall back to sample listings.
- The primary journey is Home -> Verified listings or Check a listing; subscription, quiz, comparison, and other countries are absent from launch navigation.
- A Mac user can start the product by double-clicking one root-level launcher.
- Stripe webhooks fail closed when signature verification cannot run.
- The production dependency audit has no known high-severity advisory and lint/build/tests pass.

