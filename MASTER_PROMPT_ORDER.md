# CheapHouse Japan — Ordre des prompts Antigravity

## File d'attente complète — suivre cet ordre

### ✅ FAIT
- [x] Pipeline ingestion (scrapers + enrichment)
- [x] Frontend homepage + browse + detail (mock data)
- [x] Vercel deploy (build OK, en attente push GitHub)

### 🔴 MAINTENANT — Prompt 1
**Fichier :** `PROMPT_SUPABASE_TOUT_FAIRE.md`
**Ce que ça fait :** Connecte Supabase, run le pipeline, remplit la base, réécrit le front pour la vraie data, push + deploy
**Pré-requis :** Projet Supabase créé (✅ fait)
**Optionnel :** Clé OpenAI pour traductions + What-to-Know (sinon fallback règles)

### 🟡 ENSUITE — Prompt 2
**Fichier :** `PROMPT_FIXES_AND_FEATURES.md`
**Ce que ça fait :**
- Fix "What to Know pending" (avec ou sans OpenAI)
- Ajoute Google Maps / OpenStreetMap sur chaque propriété
- Ajoute geocoding pour les propriétés sans coordonnées
- Améliore l'attribution source
**Pré-requis :** Prompt 1 terminé

### 🟡 APRÈS — Prompt 3 (dans le Playbook)
**Fichier :** `ANTIGRAVITY_PLAYBOOK.md` → Prompt 7 (Auth)
**Ce que ça fait :** Login, signup, Supabase Auth, Google OAuth, Nav update

### 🟡 APRÈS — Prompt 4 (dans le Playbook)
**Fichier :** `ANTIGRAVITY_PLAYBOOK.md` → Prompt 8 (Quiz + Matching)
**Ce que ça fait :** Buyer questionnaire, matching algorithm, match scores

### 🟡 APRÈS — Prompt 5 (dans le Playbook)
**Fichier :** `ANTIGRAVITY_PLAYBOOK.md` → Prompt 9 (Saved + Compare)
**Ce que ça fait :** Save button, saved list, compare view

### 🟡 APRÈS — Prompt 6 (dans le Playbook)
**Fichier :** `ANTIGRAVITY_PLAYBOOK.md` → Prompt 10 (Stripe)
**Ce que ça fait :** Pricing page, checkout, webhooks, paywall

### 🟡 APRÈS — Prompt 7 (dans le Playbook)
**Fichier :** `ANTIGRAVITY_PLAYBOOK.md` → Prompt 11 (Admin)
**Ce que ça fait :** Admin dashboard, review queue, approve/reject

### 🟡 APRÈS — Prompt 8
**Fichier :** `PROMPT_NEW_SCRAPERS.md`
**Ce que ça fait :** Ajoute Akiya-Mart (login) + CheapHousesJapan (Gmail newsletters)

### 🟡 APRÈS — Prompt 9
**Fichier :** `DESIGN_DIRECTION.md` (prompt inclus à la fin du fichier)
**Ce que ça fait :** Polish design premium — GSAP, smooth scroll, curseur custom, animations

---

## Résumé d'effort estimé

| Prompt | Temps Antigravity | Priorité |
|--------|------------------|----------|
| Supabase tout faire | 30-45 min | 🔴 CRITIQUE |
| Fixes + Maps | 20-30 min | 🔴 HAUTE |
| Auth | 15-20 min | 🟡 MOYENNE |
| Quiz + Matching | 20-30 min | 🟡 MOYENNE |
| Saved + Compare | 20-30 min | 🟡 MOYENNE |
| Stripe | 20-30 min | 🟡 MOYENNE |
| Admin | 20-30 min | 🟢 BASSE |
| New Scrapers | 30-45 min | 🟢 BASSE |
| Design Polish | 30-45 min | 🟢 BASSE |

## Comptes à créer (si pas déjà fait)

- [x] Supabase → supabase.com
- [ ] OpenAI → platform.openai.com ($10 de crédits suffisent)
- [ ] Stripe → stripe.com (mode test d'abord)
- [ ] Google Maps API → console.cloud.google.com (optionnel, OpenStreetMap marche sans clé)
- [ ] Vercel → vercel.com (pour le deploy, peut-être déjà fait)
- [ ] GitHub → github.com (pour le repo)

## Notes

- Chaque prompt est autonome et référence le code existant
- Les prompts sont conçus pour qu'Antigravity fasse TOUT sans te poser de questions
- Si Antigravity bloque sur quelque chose (clé API, mot de passe), il te demandera juste la valeur
- Tu peux piloter tout ça depuis ton iPad via Chrome Remote Desktop
