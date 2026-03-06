# CheapHouse Japan — MVP Build Plan

## Document de référence pour la construction du produit

---

## 1. Ce qu'on construit

**Un decision platform pour acheter une maison au Japon.**

Pas un listing site. Pas un marketplace. Un outil qui agrège des annonces publiques, les normalise, les enrichit avec des données de risque et des filtres lifestyle, puis aide l'acheteur à savoir quoi garder, quoi éviter, et pourquoi.

**Proposition de valeur core :** clarté + confiance + aide à la décision.

---

## 2. État actuel du projet

### Ce qui existe (pipeline d'ingestion Python)

| Composant | État | Notes |
|---|---|---|
| Adapter OldHousesJapan | ✅ Fonctionnel | Scrape `/all` + pages détail |
| Adapter AllAkiyas | ✅ Fonctionnel | 25 préfectures rurales |
| Adapter CheapHousesJapan | ❌ Stub | Newsletter only, pas scrapable |
| Schema PostgreSQL (Supabase) | ✅ Prêt | 3 tables + vue admin |
| Normalisation | ✅ Fonctionnel | Prix, préfecture, condition, images |
| Traduction LLM | ✅ Fonctionnel | GPT-4o-mini, title_en + summary_en |
| Déduplication | ⚠️ Partiel | Fingerprint OK, pas d'auto-merge |
| Hazard enrichment | ⚠️ Heuristique | Prefecture-level seulement, pas de GIS réel |
| Lifestyle tagging | ✅ Fonctionnel | 8 tags, règles + LLM |
| Quality scoring | ✅ Fonctionnel | 13 critères, score 0-1 |
| What-to-know (red flags) | ✅ Fonctionnel | LLM + fallback règles |
| CLI orchestration | ✅ Complet | Toutes commandes implémentées |
| Front-end | ❌ N'existe pas | À construire from scratch |

### Ce qui manque pour le MVP

1. **Front-end complet** (Next.js)
2. **API layer** entre Supabase et le front
3. **Auth + abonnement** (Supabase Auth + Stripe)
4. **Admin review UI** (la vue SQL existe, pas l'interface)
5. **Hazard data réel** (au moins flood + landslide)
6. **Buyer quiz / matching**
7. **Freshness tracking** (re-check si l'annonce est encore live)
8. **Geocoding** (beaucoup de propriétés n'ont pas de coordonnées)

---

## 3. Scope MVP strict

### Dans le MVP (Phase 1 — lancement)

- Homepage avec positionnement clair
- Browse properties avec filtres (prix, préfecture, lifestyle tags, hazard level)
- Property detail page avec : photos, description EN, hazard summary, lifestyle tags, what's attractive / unclear / risky / to verify
- Buyer quiz simple (5-7 questions) → match score basique
- Saved properties (auth required)
- Compare view (2-3 propriétés côte à côte)
- Abonnement Stripe (~$10/mois) pour accès complet
- Free tier : browse limité (10 propriétés/jour, pas de save, pas de compare)
- Admin dashboard minimaliste pour review/approve/reject

### Hors MVP (Phase 2+)

- Deep-dive reports payants
- Referral agents / inspecteurs
- App mobile
- Forum / communauté
- Chatbot immobilier
- Plus de 3 sources de données
- Hazard GIS haute résolution
- Image similarity dedup
- Notifications / alertes nouvelles propriétés
- Multi-langue (FR, etc.)

---

## 4. Architecture technique

```
┌─────────────────────────────────────────────────┐
│                    FRONT-END                     │
│              Next.js 14+ (App Router)            │
│              Tailwind CSS + shadcn/ui            │
│              Deployed on Vercel                  │
├─────────────────────────────────────────────────┤
│                    API LAYER                     │
│         Next.js API Routes / Server Actions      │
│         + Supabase JS Client (direct)            │
├─────────────────────────────────────────────────┤
│                   SUPABASE                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Postgres │  │   Auth   │  │   Storage    │  │
│  │ (data)   │  │ (users)  │  │  (images?)   │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
├─────────────────────────────────────────────────┤
│              INGESTION PIPELINE                  │
│          Python (existant) — cron job            │
│    Scrape → Normalize → Translate → Enrich      │
│         Runs on schedule (daily/weekly)          │
├─────────────────────────────────────────────────┤
│                   STRIPE                         │
│        Checkout + Webhook → subscription         │
└─────────────────────────────────────────────────┘
```

### Stack détaillé

| Couche | Techno | Pourquoi |
|---|---|---|
| Front-end | Next.js 14+ (App Router) | SSR, SEO, React Server Components, rapide |
| Style | Tailwind CSS + shadcn/ui | Premium, composable, pas de CSS custom à maintenir |
| Data | Supabase (Postgres) | Déjà en place, Auth + Realtime + Storage inclus |
| Auth | Supabase Auth | Email/password, Google OAuth, intégré |
| Paiement | Stripe Checkout + Webhooks | Standard, fiable, subscription billing |
| Deploy front | Vercel | Intégration Next.js native, preview deploys |
| Ingestion | Python (existant) | Cron via GitHub Actions ou Railway ou Supabase Edge Functions |
| LLM | OpenAI GPT-4o-mini | Déjà intégré, cheap, bon pour traduction/tagging |
| Images | Supabase Storage ou liens directs sources | MVP : liens directs. Plus tard : cache propre |

---

## 5. Schema base de données — Compléments MVP

Le schema existant (`sources`, `raw_listings`, `properties`, `scrape_runs`) est bon. Voici ce qu'il faut ajouter :

### Table `users` (gérée par Supabase Auth)

Supabase Auth crée automatiquement `auth.users`. On ajoute une table profil :

```sql
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    subscription_status TEXT DEFAULT 'free'
        CHECK (subscription_status IN ('free', 'active', 'cancelled', 'past_due')),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    quiz_answers JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table `saved_properties`

```sql
CREATE TABLE public.saved_properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    notes TEXT,
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, property_id)
);
```

### Table `quiz_templates`

```sql
CREATE TABLE public.quiz_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version INT NOT NULL DEFAULT 1,
    questions JSONB NOT NULL,
    -- JSONB structure: [{
    --   "key": "budget",
    --   "label": "What's your budget?",
    --   "type": "range",
    --   "options": {"min": 0, "max": 50000000, "step": 1000000, "unit": "JPY"}
    -- }, ...]
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table `match_scores` (calculé côté serveur)

```sql
CREATE TABLE public.match_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    score NUMERIC(4,2) NOT NULL, -- 0.00 à 1.00
    breakdown JSONB NOT NULL,
    -- JSONB: {"budget_fit": 0.9, "lifestyle_match": 0.7, "risk_tolerance": 0.8, ...}
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, property_id)
);
```

### Modifications table `properties` existante

Ajouter si pas déjà présent :

```sql
ALTER TABLE properties ADD COLUMN IF NOT EXISTS
    slug TEXT UNIQUE; -- pour URLs propres : /property/charming-3ldk-otaru

ALTER TABLE properties ADD COLUMN IF NOT EXISTS
    is_published BOOLEAN DEFAULT false; -- ne montre que les approved + published

ALTER TABLE properties ADD COLUMN IF NOT EXISTS
    view_count INT DEFAULT 0;

ALTER TABLE properties ADD COLUMN IF NOT EXISTS
    save_count INT DEFAULT 0;
```

### Row Level Security (RLS) — Important Supabase

```sql
-- Properties : lecture publique pour les published
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read published" ON properties
    FOR SELECT USING (is_published = true AND admin_status = 'approved');

-- Saved properties : chaque user voit les siens
ALTER TABLE saved_properties ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own saves" ON saved_properties
    FOR ALL USING (auth.uid() = user_id);

-- User profiles : chaque user voit le sien
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own profile" ON user_profiles
    FOR ALL USING (auth.uid() = id);

-- Match scores : chaque user voit les siens
ALTER TABLE match_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own scores" ON match_scores
    FOR ALL USING (auth.uid() = user_id);
```

---

## 6. Structure front-end Next.js

### Arborescence fichiers

```
app/
├── layout.tsx                    # Root layout, fonts, providers
├── page.tsx                      # Homepage
├── globals.css                   # Tailwind base
│
├── (marketing)/
│   ├── about/page.tsx
│   └── pricing/page.tsx
│
├── (app)/
│   ├── layout.tsx                # App layout (nav, sidebar)
│   ├── browse/
│   │   └── page.tsx              # Browse properties + filtres
│   ├── property/
│   │   └── [slug]/page.tsx       # Property detail
│   ├── quiz/
│   │   └── page.tsx              # Buyer questionnaire
│   ├── saved/
│   │   └── page.tsx              # Saved properties (auth required)
│   ├── compare/
│   │   └── page.tsx              # Compare view (auth required)
│   └── account/
│       ├── page.tsx              # Account settings
│       └── subscription/page.tsx # Manage subscription
│
├── (auth)/
│   ├── login/page.tsx
│   └── signup/page.tsx
│
├── admin/
│   ├── layout.tsx                # Admin layout
│   ├── page.tsx                  # Dashboard
│   ├── review/page.tsx           # Review queue
│   └── sources/page.tsx          # Source status
│
├── api/
│   ├── webhooks/
│   │   └── stripe/route.ts       # Stripe webhook
│   ├── match/
│   │   └── route.ts              # Compute match scores
│   └── properties/
│       └── route.ts              # Property queries (si besoin custom)
│
components/
├── ui/                           # shadcn/ui components
├── property-card.tsx
├── property-detail.tsx
├── hazard-badge.tsx
├── lifestyle-tag.tsx
├── match-score.tsx
├── what-to-know.tsx
├── filter-bar.tsx
├── quiz-form.tsx
├── compare-table.tsx
├── save-button.tsx
└── navigation.tsx

lib/
├── supabase/
│   ├── client.ts                 # Browser client
│   ├── server.ts                 # Server client
│   └── middleware.ts             # Auth middleware
├── stripe.ts                     # Stripe helpers
├── matching.ts                   # Match score computation
├── types.ts                      # TypeScript types
└── utils.ts
```

---

## 7. Pages MVP — Détail UX

### 7.1 Homepage

**Objectif :** Faire comprendre la valeur en 5 secondes.

**Contenu :**
- Hero : "Find the right house in Japan. Avoid the wrong one." + CTA → Browse / Take the Quiz
- 3 blocs valeur : (1) Aggregated listings, (2) Risk & hazard data, (3) Lifestyle matching
- Stats : X properties, X prefectures, X sources
- Exemples de propriétés (3-4 cards)
- CTA pricing

**Ton :** Premium, calme, intelligent. Pas de "FREE AKIYA!!!" ni de "10,000 listings!!!".

### 7.2 Browse Properties

**Objectif :** Filtrer et scanner rapidement.

**Filtres :**
- Prix (range slider JPY, avec équivalent USD)
- Préfecture (dropdown groupé par région)
- Lifestyle tags (multi-select chips)
- Hazard level max (low / moderate / high / any)
- Condition (good / fair / needs work / any)
- Min surface bâtiment
- Min surface terrain
- Tri : match score (si quiz fait), prix asc/desc, quality score, newest

**Affichage :**
- Grid de property cards
- Chaque card : photo, titre EN, prix JPY (USD), préfecture, surface, 2-3 lifestyle tags, hazard indicator (vert/orange/rouge), match % si quiz fait
- Pagination ou infinite scroll

**Paywall :** Free users voient les 10 premières. Au-delà : "Subscribe to see all X properties."

### 7.3 Property Detail

**Objectif :** Tout savoir pour décider sans quitter la page.

**Sections :**
1. **Gallery** (images, plein écran possible)
2. **Key facts** (prix, surface, année, rooms, condition, préfecture/ville)
3. **Summary** (title_en + summary_en — la réécriture LLM)
4. **Match score** (si quiz fait — barre + breakdown)
5. **What to know** — LA section différenciante :
   - ✅ What's attractive (vert)
   - ❓ What's unclear (jaune)
   - ⚠️ What's risky (rouge)
   - 🔍 What to verify (bleu)
6. **Hazard assessment** (flood, landslide, tsunami — niveau + confidence + source)
7. **Lifestyle fit** (tags avec confiance + explication)
8. **Source** (lien vers l'annonce originale — transparence)
9. **Actions** : Save, Compare, Share link

### 7.4 Buyer Quiz

**Objectif :** Personnaliser l'expérience en 2 minutes.

**Questions MVP (7 questions) :**

1. **Budget** — Slider ou brackets : <¥1M / ¥1-3M / ¥3-5M / ¥5-10M / ¥10-20M / >¥20M
2. **Usage principal** — Choix unique : Résidence principale / Résidence secondaire / Retreat/vacances / Investissement locatif / Projet créatif (atelier, studio)
3. **Tolérance rénovation** — Prêt à rénover beaucoup / Un peu / Le moins possible
4. **Animaux** — Oui, j'ai ou prévois des animaux / Non
5. **Transport** — Besoin d'être près d'une gare / Voiture OK / Isolement total OK
6. **Risques naturels** — Tolérance faible (je veux du safe) / Modérée / Ça ne me dérange pas
7. **Environnement** — Ville / Suburb / Campagne / Montagne / Bord de mer

**Après quiz :** Redirect vers Browse avec match scores activés + tri par match.

### 7.5 Saved Properties

Liste des propriétés sauvegardées. Notes optionnelles par propriété. Quick actions : remove, compare, voir détail.

### 7.6 Compare View

Tableau côte à côte de 2-3 propriétés sélectionnées. Colonnes : photo, prix, surface, condition, hazard levels, lifestyle tags, match score, what's risky. Highlight des différences.

### 7.7 Admin Review

Table des propriétés en `pending_review`. Pour chaque : preview, données brutes, actions (approve / reject / edit / flag for re-enrichment). Filtres : source, quality score, date. Pas besoin d'être beau au MVP — fonctionnel suffit.

---

## 8. Logique de matching

### Algorithme MVP (simple, explicable)

Le match score est un weighted average de sous-scores, chacun entre 0 et 1.

```
match_score = Σ (weight_i × sub_score_i) / Σ weight_i
```

| Dimension | Poids | Calcul |
|---|---|---|
| Budget fit | 3 | 1.0 si dans le bracket choisi, 0.7 si bracket ±1, 0.3 si ±2, 0 au-delà |
| Lifestyle match | 2 | (nombre de lifestyle tags de la propriété qui matchent les réponses quiz) / (nombre de tags attendus) |
| Risk tolerance | 2 | Si user veut "safe" : 1.0 si tous hazards low, 0.5 si moderate, 0 si high. Si "ça ne me dérange pas" : toujours 0.8+ |
| Condition fit | 2 | Si user veut "peu de rénovation" : 1.0 si good/fair, 0.3 si needs_work, 0 si significant. Si "prêt à rénover" : toujours 0.7+ |
| Transport fit | 1 | Si user veut "near station" : 1.0 si near-station tag, 0.3 sinon. Si "isolement OK" : toujours 0.8 |

**Breakdown visible à l'utilisateur :** chaque sous-score affiché avec une barre + label.

Le score ne doit jamais paraître "magique". Chaque composante est explicable.

---

## 9. Modèle économique MVP

### Tiers

| | Free | Pro ($10/mois) |
|---|---|---|
| Browse | 10 propriétés/jour | Illimité |
| Property detail | Limité (pas de what-to-know) | Complet |
| Save | ❌ | ✅ |
| Compare | ❌ | ✅ |
| Quiz + matching | Quiz seulement | Quiz + scores sur toutes propriétés |
| Filtres | Basiques (prix, préfecture) | Tous (lifestyle, hazard, condition) |

### Stripe flow

1. User clique "Subscribe" → Stripe Checkout (hosted)
2. Paiement réussi → webhook `checkout.session.completed`
3. Webhook met à jour `user_profiles.subscription_status = 'active'`
4. Accès Pro activé via middleware Next.js
5. Annulation → webhook `customer.subscription.deleted` → status = 'cancelled'

---

## 10. Build order — Phases concrètes

### Phase 0 : Fix pipeline (1-2 jours)

**Avant de toucher au front, solidifier ce qui existe.**

- [ ] Ajouter `slug` generation dans le normalize (slugify du title_en)
- [ ] Ajouter `is_published` flag, default false
- [ ] Créer un script d'admin pour bulk-approve les propriétés avec quality_score > 0.6
- [ ] Fix freshness : ajouter logique `last_seen_at` update lors du re-scrape
- [ ] Ajouter geocoding basique (Nominatim gratuit) pour les propriétés sans coordonnées
- [ ] Run le pipeline complet une fois et vérifier la data en base

### Phase 1 : Foundation front (2-3 jours)

- [ ] Init Next.js 14 projet (App Router, TypeScript, Tailwind, shadcn/ui)
- [ ] Setup Supabase client (browser + server)
- [ ] Auth flow (login, signup, middleware)
- [ ] Layout principal (navigation, footer)
- [ ] Types TypeScript générés depuis le schema Supabase
- [ ] Homepage (hero, value props, CTA)
- [ ] Deploy sur Vercel (même vide, avoir le pipeline CI)

### Phase 2 : Core product (3-5 jours)

- [ ] Browse page avec filtres + property cards
- [ ] Property detail page complète
- [ ] Component `what-to-know` (la section différenciante)
- [ ] Hazard badges
- [ ] Lifestyle tags
- [ ] Paywall logic (middleware + UI gates)
- [ ] Pagination / infinite scroll

### Phase 3 : Personnalisation (2-3 jours)

- [ ] Quiz page + stockage réponses dans `user_profiles.quiz_answers`
- [ ] Matching algorithm (server-side computation)
- [ ] Match score display dans browse + detail
- [ ] Save property
- [ ] Compare view

### Phase 4 : Monétisation (1-2 jours)

- [ ] Stripe Checkout intégration
- [ ] Webhook handler
- [ ] Gating logic (free vs pro)
- [ ] Account page + manage subscription
- [ ] Pricing page

### Phase 5 : Admin (1-2 jours)

- [ ] Admin layout (protected route, hardcoded admin emails)
- [ ] Review queue page
- [ ] Approve / reject / edit actions
- [ ] Source health dashboard (dernière run, nombre de listings, erreurs)

### Phase 6 : Polish (2-3 jours)

- [ ] SEO (meta tags, OG images, sitemap)
- [ ] Performance (image optimization, caching)
- [ ] Error handling (404, empty states, loading states)
- [ ] Mobile responsive
- [ ] Analytics (Plausible ou Vercel Analytics)
- [ ] Feedback mechanism (simple form ou mailto)

**Total estimé : 12-18 jours de travail effectif** pour un solo builder assisté par Antigravity et Claude.

---

## 11. Compromis intelligents pour le MVP

### Ce qu'on simplifie volontairement

| Aspect | Approche MVP (acceptable) | Version future (idéale) |
|---|---|---|
| Hazard data | Heuristique par préfecture | GIS réel (Disaportal grid cells) |
| Geocoding | Nominatim batch (gratuit) | Google Geocoding API |
| Images | Liens directs vers les sources | Cache/proxy via Supabase Storage |
| Dedup | Fingerprint + rapport, merge manuel | Auto-merge avec confidence threshold |
| Match score | Weighted average simple | ML-based recommendation |
| Admin | Table HTML basique | Dashboard riche avec analytics |
| Freshness | Re-scrape hebdo | Monitoring continu + alertes |
| Traduction | GPT-4o-mini batch | Fine-tuned model immobilier JP |
| Abonnement | Stripe Checkout hosted | Embedded billing + facturation |
| Sources | 2 (OHJ + AllAkiyas) | 5-10 sources |

### Ce qu'on ne simplifie PAS

- La section "What to Know" — c'est le moat, elle doit être bonne dès le début
- Le design — premium et calme, pas de raccourci esthétique
- La transparence — toujours montrer la source, le niveau de confiance, les limites
- Le paywall — bien implémenté dès le départ pour valider la willingness-to-pay

---

## 12. Données de risque — Plan d'amélioration post-MVP

### Sources gratuites exploitables

1. **Disaportal (国土交通省ハザードマップポータル)**
   - Flood risk maps (洪水浸水想定区域)
   - Sediment disaster risk (土砂災害警戒区域)
   - Tsunami inundation (津波浸水想定区域)
   - Format : tuiles images ou WMS
   - Approche : grid-cell lookup par lat/lng sans PostGIS

2. **J-SHIS (地震ハザードステーション)**
   - Probabilité sismique par zone
   - Données de sol / liquéfaction
   - API disponible

3. **Données municipales**
   - Certaines villes publient des données ouvertes
   - Variable selon la municipalité

### Approche technique sans PostGIS

Pour chaque source :
1. Pré-calculer une grille de cellules (ex: 0.01° × 0.01° ≈ 1km)
2. Stocker les niveaux de risque par cellule dans une table `hazard_zones`
3. Lookup par arrondi des coordonnées de la propriété
4. Pas besoin de PostGIS, juste des index sur lat/lng arrondis

---

## 13. SEO & Acquisition — Notes MVP

### Pages qui rankent naturellement

- `/property/[slug]` — chaque propriété = une page indexable
- `/browse?prefecture=nagano` — pages par préfecture
- Blog/guides (phase 2) : "How to buy an akiya in Japan", "Best prefectures for remote workers", etc.

### Distribution initiale

- Reddit (r/movingtojapan, r/japanlife, r/digitalnomad)
- Twitter/X (communauté Japan real estate)
- Hacker News (Show HN: je construis le meilleur outil de recherche akiya)
- Newsletter propre (phase 2)

---

## 14. Environnement de développement

### Pour Antigravity / développement local

```bash
# Front-end
cd cheaphouse-web
npm install
cp .env.example .env.local
# Remplir : NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, STRIPE_SECRET_KEY, etc.
npm run dev

# Ingestion (existant)
cd ingestion
source venv/bin/activate
cp .env.example .env
# Remplir : DATABASE_URL, OPENAI_API_KEY
python run.py scrape --source old-houses-japan
python run.py pipeline
```

### Variables d'environnement nécessaires

```
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx

# Stripe
STRIPE_SECRET_KEY=sk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_PRICE_ID=price_xxx

# OpenAI (pour le pipeline)
OPENAI_API_KEY=sk-xxx

# DB (pour le pipeline Python)
DATABASE_URL=postgresql://xxx
```

---

## 15. Checklist pré-lancement

- [ ] Au moins 50 propriétés approved + published en base
- [ ] Pipeline testé end-to-end (scrape → normalize → translate → enrich → publish)
- [ ] Auth flow fonctionnel (signup, login, logout)
- [ ] Stripe fonctionnel (subscribe, cancel, webhook)
- [ ] Toutes les pages responsive mobile
- [ ] Temps de chargement < 3s
- [ ] Meta tags / OG images pour sharing
- [ ] Legal : Terms of Service, Privacy Policy (peut être générique MVP)
- [ ] robots.txt respectueux des sources scrapées
- [ ] Error tracking (Sentry ou similaire)
- [ ] Un ami/testeur a fait le parcours complet sans aide

---

## 16. Ce document est vivant

Ce plan est un point de départ exécutable, pas un document figé. Au fur et à mesure de la construction, les priorités vont shifter, des problèmes vont émerger, et des raccourcis plus malins vont apparaître.

La règle : toujours se demander "est-ce que ça rapproche du lancement, ou est-ce que c'est du perfectionnisme prématuré ?"

Si la réponse est la deuxième, on skip et on note pour plus tard.
