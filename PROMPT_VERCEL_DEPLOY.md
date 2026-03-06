# PROMPT À COLLER DANS ANTIGRAVITY — Deploy sur Vercel

```
I need to deploy this Next.js app to Vercel. The project is in the /web folder of my repo.

## Step 1 — Prepare for production

1. Make sure next.config.mjs has output configuration for Vercel (it should work by default, but verify there are no issues).

2. Create a .env.example file at the web root listing all required environment variables with descriptions:

NEXT_PUBLIC_SUPABASE_URL=        # Your Supabase project URL (https://xxx.supabase.co)
NEXT_PUBLIC_SUPABASE_ANON_KEY=   # Supabase anon/public key
SUPABASE_SERVICE_ROLE_KEY=       # Supabase service role key (server-side only, never exposed to client)
NEXT_PUBLIC_SITE_URL=            # Your production URL (https://cheaphouse-japan.vercel.app or custom domain)

3. Make sure .gitignore includes:
   - .env.local
   - .env
   - node_modules/
   - .next/
   - out/

4. Run `npm run build` and fix any build errors. The app must build cleanly with zero errors before deploying.

## Step 2 — Initialize Git repo and push to GitHub

If not already a git repo:

```bash
cd web
git init
git add -A
git commit -m "Initial commit: CheapHouse Japan MVP"
```

Create the GitHub repo and push:

```bash
gh repo create cheaphouse-japan --public --source=. --remote=origin --push
```

If `gh` CLI is not available, use:

```bash
git remote add origin https://github.com/YOUR_USERNAME/cheaphouse-japan.git
git branch -M main
git push -u origin main
```

## Step 3 — Deploy to Vercel

Use the Vercel CLI:

```bash
npm i -g vercel
vercel login
```

Then deploy:

```bash
cd web
vercel
```

When prompted:
- Set up and deploy: YES
- Which scope: select your account
- Link to existing project: NO (create new)
- Project name: cheaphouse-japan
- Directory where code is located: ./ (since we're already in /web)
- Override settings: NO

After first deploy, set environment variables:

```bash
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
vercel env add NEXT_PUBLIC_SITE_URL production
```

Paste the values when prompted. Then redeploy with the env vars active:

```bash
vercel --prod
```

## Step 4 — Verify

1. Open the deployed URL (shown in terminal output)
2. Check that the homepage loads correctly
3. Check that /properties loads (it may show empty if Supabase isn't connected yet — that's fine, just make sure it doesn't crash)
4. Check the browser console for errors

## Step 5 — Set up auto-deploy

After the initial Vercel deploy, go to vercel.com, find the project, and connect it to the GitHub repo if not already connected. This way every `git push` auto-deploys.

Or via CLI:
```bash
vercel git connect
```

## IMPORTANT

- The root directory in Vercel project settings should be `web` if the GitHub repo contains both `ingestion/` and `web/` at the top level. If we only pushed the `web/` folder, the root is `.`
- Do NOT commit .env.local or any file containing real API keys
- If the build fails, read the error log carefully — most common issues are missing dependencies or import errors
- Preview deploys happen on every PR, production deploy happens on push to main
```
