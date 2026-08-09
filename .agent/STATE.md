# State

## Current

Local implementation and verification are complete. Public release is blocked by external configuration, not source code.

## Working copy

The original folder is owned by a different macOS account and is read-only for Robin. Implementation uses `/Users/robinmahieux/CheapHouse-Japan`; the original remains untouched.

## Writable scope

- `.agent/**`
- `web/**` except secrets, generated output, and installed dependencies
- `ingestion/**` except secrets and runtime logs
- Root launcher and README

## External blockers already observed

- The public domain does not currently resolve.
- The configured Supabase project is unreachable from the latest pipeline run.
- Vercel CLI is not authenticated in this environment.
- The new database migrations have not been applied to a live Supabase project.
