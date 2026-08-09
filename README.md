# CheapHouse Japan

Verified-first property research for international buyers considering Japanese homes.

## Open it on a Mac

Double-click `START_CHEAPHOUSE.command`. The first launch installs the web dependencies, starts the site, and opens [http://localhost:3000](http://localhost:3000).

Keep the Terminal window open while using the site. Press Control-C in that window to stop it.

## Trust rule

Only published Japan listings whose original source was confirmed active within the last 72 hours appear in browse results.

- `active`: source confirmed within 72 hours
- `uncertain`: source unavailable, check failed, or source says pending
- `sold`: source explicitly says sold
- `removed`: source returned 404 or 410

Uncertain, sold, and removed records stay in the database for provenance but are hidden from active browse results. A network error never proves a sale or removal.

## Production setup

Copy `web/.env.example` to `web/.env.local`, apply the SQL migrations in `ingestion/migrations` and `web/supabase`, then run the freshness checker before publishing listings.

```bash
cd web
npm install
npm run dev
```

