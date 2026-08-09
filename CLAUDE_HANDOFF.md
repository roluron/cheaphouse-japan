# CheapHouse Japan — Claude handoff

Last verified: 2026-08-09 (Asia/Ho_Chi_Minh)

## Start here

Use this repository, not the space-named original:

```text
/Users/robinmahieux/CheapHouse-Japan
```

`/Users/robinmahieux/CheapHouse Japan` is owned by UID 505, is not writable, and Git rejects it as dubious ownership. Do not repair or modify that copy unless Robin explicitly asks.

## Current release state

- Product: Japan-only, verified-first cheap-house discovery and paid listing verification.
- Live site: https://cheaphouse-japan.vercel.app
- Vercel project: `from-anothers-projects/cheaphouse-japan`
- Supabase project ref: `ruwjtsgbqacefwndqcmb`
- Git remote: `https://github.com/roluron/cheaphouse-japan.git`
- Branch: `codex/verified-first-release`
- Commit: `09ffa2f Ship verified-first CheapHouse release`
- The branch is pushed but not merged to `main`.

Fresh live checks on 2026-08-09:

```text
GET /            -> 200
GET /properties  -> 200
GET /verify      -> 200
POST /api/verification-request with {} -> 503
{"error":"Request intake is temporarily unavailable."}
```

The `503` is intentional fail-closed behavior while the privileged Supabase server key is absent.

## What is already complete

- Supabase was restored and reported healthy on Nano compute.
- Both production migrations were executed successfully:
  - `ingestion/migrations/003_listing_trust.sql`
  - `web/supabase/migration_002_verification_requests.sql`
- A verification query returned both `public.properties` and `public.verification_requests`.
- Vercel production deployment built successfully with Next.js 16.3.0 and generated 23/23 pages.
- Public Vercel variables are configured for production, preview, and development:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_SITE_URL`
- No secret or credential is committed to Git.
- Local verification completed before deployment:
  - Next production build passed.
  - Python freshness tests passed: 5/5.
  - Dependency audit reported 0 vulnerabilities.
  - `git diff --check` passed.

Raw implementation evidence and acceptance state are in:

- `.agent/GOAL.md`
- `.agent/ACCEPTANCE.md`
- `.agent/STATE.md`
- `.agent/EVIDENCE.md`

## Product behavior to preserve

- Public pages show only listings with `listing_status = 'active'` checked within the last 72 hours.
- `uncertain` listings are hidden.
- `sold` and `removed` listings are retained in the database for history rather than deleted.
- Scraper or network errors must never mark a listing as removed.
- The paid offer is a one-time `$149` verification request, not a subscription.
- Stripe checkout and portal routes are disabled; the webhook fails closed until a real payment workflow is approved.

Key implementation files:

- `web/app/lib/availability.js`
- `web/app/api/verification-request/route.js`
- `web/app/verify/VerificationForm.js`
- `web/app/properties/page.js`
- `web/app/properties/[slug]/page.js`
- `ingestion/pipeline/freshness.py`
- `ingestion/tests/test_freshness.py`

## Only remaining production gate

The verification form needs a privileged Supabase server key in Vercel as:

```text
SUPABASE_SERVICE_ROLE_KEY
```

Robin has not yet explicitly authorized copying/storing that privileged key. Do not reveal, copy, log, or store it until he gives clear approval identifying the Vercel production project as the destination.

After approval:

1. In Supabase, open project `ruwjtsgbqacefwndqcmb` → Settings → API Keys.
2. Use the server-side secret key; never put it in a `NEXT_PUBLIC_*` variable or source file.
3. Add it only to Vercel production as the sensitive variable `SUPABASE_SERVICE_ROLE_KEY`.
4. Redeploy from `web/`:

   ```bash
   rtk vercel --prod --yes --scope from-anothers-projects
   ```

5. Verify the failure path first:

   ```bash
   curl -i -X POST \
     -H 'content-type: application/json' \
     --data '{}' \
     https://cheaphouse-japan.vercel.app/api/verification-request
   ```

   Expected after configuration: a validation response, not `503`.

6. Exercise one real test submission through `/verify`, confirm the row exists in `public.verification_requests`, then remove only that uniquely labelled QA row.
7. Recheck `/`, `/properties`, `/verify`, and the form in the browser before claiming completion.

## Domain

`cheaphouse.app` did not resolve in public DNS and was not registered in the Vercel workspace at the last check. The usable public address is currently:

```text
https://cheaphouse-japan.vercel.app
```

Do not claim or reconfigure `cheaphouse.app` without first confirming Robin owns it and authorizes the DNS/domain change.

## Useful commands

```bash
cd /Users/robinmahieux/CheapHouse-Japan
rtk git status --short --branch
cd web
rtk vercel whoami
rtk vercel project inspect cheaphouse-japan --scope from-anothers-projects
npm run build
```

Do not lower the freshness rules, expose unverified listings, revive subscriptions, or add credentials to files to make the final test pass.
