# CheapHouse — Design Direction & References

## Vision

Le site doit donner l'impression d'un outil premium de décision immobilière, pas d'un site de petites annonces. Le design doit inspirer la confiance, le calme, et l'intelligence. Chaque pixel doit dire : "ces gens savent ce qu'ils font."

## Références

### 1. lobelia.earth — Données + Émotion
- **Ce qu'on prend :** Dark theme maîtrisé, palette noir + accent doré/chaud, animations GSAP au scroll (texte qui apparaît au scroll, sections qui se révèlent), data visualization élégante pour les données de risque/hazard, full-screen hero, espacement généreux
- **Palette :** noir (#000), blanc (#fff), doré/or (#ECD06F)
- **Tech :** Vue.js, GSAP, Awwwards Honorable Mention
- **Application CheapHouse :** Les sections hazard/risque doivent avoir cette qualité visuelle — pas des badges cheap mais des visualisations élégantes. Les cartes de risque flood/landslide/tsunami comme des data-viz premium. Les scroll animations pour révéler les propriétés et les insights.

### 2. victor-sin.com — Craft technique + Immersion
- **Ce qu'on prend :** Transitions fluides entre pages, effets WebGL subtils (pas over-the-top), curseur custom, textures/grain visuels, sens du mouvement, typographie expressive
- **Tech :** WebGL, WebGPU, GSAP
- **Application CheapHouse :** Transitions entre les pages (browse → detail), hover effects sur les property cards (pas juste un scale mais un vrai mouvement), possibilité d'un subtle shader/grain en background du hero. Curseur custom sur desktop.

### 3. cathydolle.com — Minimalisme luxe + Calme
- **Ce qu'on prend :** Espace négatif généreux (beaucoup de blanc/vide), typographie serif + sans-serif mix raffiné, animations micro (hover, reveal) douces et non-intrusives, navigation minimale, chaque élément a de la place pour respirer
- **Tech :** React, Awwwards SOTD
- **Application CheapHouse :** Le ton général du site. Pas d'UI encombrée. Les property cards doivent respirer. Les détails typographiques (tailles, weights, letter-spacing) doivent être travaillés au pixel. Le quiz doit être une expérience calme et élégante, pas un formulaire.

---

## Principes de design CheapHouse

### Typographie
- **Display/Headings :** Outfit (déjà installé) — gros, bold, letter-spacing négatif. Envisager un serif premium en V2 (comme un Playfair Display ou Fraunces pour les titres hero)
- **Body :** Inter (déjà installé) — clean, lisible
- **Tailles :** Aller grand. Hero h1 : 64-80px desktop, 36-44px mobile. Beaucoup de contraste entre les niveaux
- **Espacement :** Line-height 1.1-1.2 sur les titres, letter-spacing -0.03em sur les gros titres

### Palette (évolution de l'existant)
Le globals.css actuel est dark blue/navy. Options d'évolution :
- **Option A — Garder le dark bleu** mais ajouter un accent chaud (or/doré comme Lobelia) au lieu du bleu seul
- **Option B — Passer en noir pur** (#000 ou #050505) pour un look plus luxe, avec accents dorés/teal
- **Option C — Mode clair premium** pour un public plus large, fond crème/off-white, accents noirs + un accent couleur

Pour le MVP : garder le dark theme actuel. Pour le polish V2 : explorer Option B.

### Animations à implémenter
1. **Scroll reveal** — Les sections apparaissent en fadeUp au scroll (IntersectionObserver, déjà ébauché dans globals.css)
2. **Stagger animations** — Les property cards dans la grille apparaissent en cascade (card 1, puis 2, puis 3, etc.)
3. **Page transitions** — Smooth transition entre browse et detail (pas un hard page load)
4. **Hover states premium** — Property cards : image zoom subtil + léger shift de couleur du border + shadow glow (déjà en partie dans globals.css)
5. **Cursor custom** — Petit cercle qui suit le curseur, change de taille au hover sur les éléments cliquables (desktop only)
6. **Number animations** — Les stats (250+ properties, etc.) s'animent en comptant (countUp effect)
7. **Parallax subtil** — Le hero background bouge légèrement au scroll

### Librairies recommandées
- **GSAP** (GreenSock) — Pour les scroll animations, les staggers, les timelines complexes. C'est la ref (utilisé par Lobelia et Victor Sin)
- **Framer Motion** — Alternative React-native, plus simple que GSAP, bon pour les page transitions et les micro-interactions
- **Lenis** — Pour le smooth scroll (le scroll natif est saccadé, Lenis le rend butter-smooth)

### Espacement
- Sections : 120-160px de padding vertical (pas 80px comme actuellement — c'est trop serré pour un look premium)
- Entre les cards : 32-40px de gap
- Container max-width : 1200-1280px
- Margins latéraux : 40-64px desktop, 20-24px mobile

### Images
- Property photos : traitement uniforme (même ratio, même style de crop)
- Overlay gradient subtil sur les thumbnails pour lisibilité du texte
- Placeholder quand pas d'image : beau gradient ou pattern japonais subtil, pas un gris moche

### UI spécifiques à travailler
- **Property cards** — Plus d'espace, image plus grande (ratio 16:9 ou 4:3), prix et titre plus contrastés
- **Hazard visualization** — Pas des badges texte mais des petites barres/jauges visuelles avec couleur
- **What-to-Know section** — Cards avec left border coloré (déjà le cas), mais ajouter des icônes custom et plus d'espace
- **Quiz** — Une question par écran, transitions douces, progress bar élégante, illustrations ou icônes subtiles par question
- **Compare view** — Pas un tableau HTML brut mais des colonnes cards avec highlight visuel des différences

---

## Quand appliquer

Ce polish design est prévu pour APRÈS le MVP fonctionnel. L'ordre :
1. MVP fonctionnel avec Supabase (design actuel, c'est déjà bien)
2. Premiers utilisateurs / feedback
3. **Design polish pass** — appliquer ces principes
4. GSAP animations + smooth scroll + cursor custom
5. A/B test homepage messaging

Le design actuel dans globals.css est une bonne base. Le polish transformera "bon site" en "wow, ces gens sont sérieux."

---

## Prompt Antigravity pour le Design Polish (à utiliser plus tard)

```
I want to upgrade the CheapHouse Japan frontend to a premium, award-worthy design level. Read the DESIGN_DIRECTION.md file in the project root for the full design reference and guidelines.

Key changes needed:

1. Install and configure:
   - gsap (GreenSock) + @gsap/react for scroll animations
   - lenis for smooth scrolling

2. Typography upgrade:
   - Increase hero heading to 72px desktop / 40px mobile
   - Add letter-spacing: -0.03em on all headings
   - Increase section padding to 140px vertical
   - Increase property grid gap to 32px

3. Scroll animations (GSAP ScrollTrigger):
   - Hero text: staggered word-by-word reveal on load
   - Section headings: fadeUp + slight scale on scroll enter
   - Property cards: stagger cascade (0.1s delay between each card)
   - Stats numbers: countUp animation when section enters viewport
   - What-to-Know cards: stagger reveal with colored border growing in

4. Smooth scroll:
   - Initialize Lenis in layout.js for butter-smooth scrolling
   - Sync with GSAP ScrollTrigger

5. Custom cursor (desktop only):
   - Small circle (12px) following mouse with slight lag (lerp 0.1)
   - Grows to 40px on hover over clickable elements
   - Changes color to accent on interactive elements
   - Hide on mobile/touch devices

6. Property card upgrade:
   - Image ratio 16:9, taller (260px instead of 220px)
   - Subtle image zoom on hover (already exists, keep it)
   - Add a gradient overlay on the bottom of the image for text readability
   - Price and title slightly larger

7. Hazard visualization upgrade:
   - Replace text badges with small horizontal bar gauges
   - Green (low) → Amber (moderate) → Rose (high) fill
   - Animate fill on scroll enter

8. Page transitions:
   - Fade out current page, fade in new page
   - Use framer-motion AnimatePresence if easier than GSAP for this

Keep ALL existing functionality. This is a VISUAL upgrade only — no data changes, no new features. Keep the dark theme. Make it feel like an Awwwards site.
```
