# PROMPT À COLLER DANS ANTIGRAVITY — Complete Design Overhaul

```
Auto-approve all changes and commands. Don't ask for permission.

The current design of CheapHouse looks like a generic SaaS template. I want it to look like a premium, award-winning real estate platform — think the visual quality of lobelia.earth, victor-sin.com, cathydolle.com. Calm, confident, luxurious, minimal.

This is a MAJOR visual overhaul. You will touch almost every component and page. Keep all functionality — change only the visual presentation.

## THE CORE PROBLEMS TO FIX

1. **EMOJIS EVERYWHERE — REMOVE THEM ALL.** No more 🏠📍📐🌿📅🔎🌊🏷️⚖️📊🔄✨⚠✓🤖🗾. Zero emojis anywhere on the site. Replace with either nothing, simple SVG icons, or elegant text. Premium brands never use emojis.

2. **Logo "CheapHouse" with "Cheap" in gradient — rebrand visually.** Either:
   - Rename to just the logo mark without "Cheap" being highlighted
   - Or use a monogram/wordmark that doesn't scream "cheap"
   - Suggestion: Use "CH" monogram + "CheapHouse" in elegant serif, all one color (white or gold). No gradient on the word "Cheap".

3. **Remove the Quality Score bar from property cards.** It looks like an internal dashboard metric. Users don't need to see "Quality 73%". Just show good properties.

4. **Remove glassmorphism (backdrop-filter blur).** Replace glass-card with clean, simple cards: solid dark background, very subtle border, no blur effect. Modern and clean, not trendy.

5. **Reduce information density on property cards.** Show ONLY: image (large), price, title, location. That's it on the card. Tags, details, hazard — save for the detail page. Less is more.

6. **Remove pricing section from homepage.** Move it to a dedicated /pricing page. The homepage should sell the vision, not the price.

7. **Redesign "How it works" section.** Kill the 6-card emoji grid. Replace with 3 elegant full-width sections, each with a short headline, one sentence, and maybe a subtle visual/icon. Think Apple product page, not SaaS features grid.

## TYPOGRAPHY

Install a premium serif font for headlines:

```javascript
// In layout.js, add:
import { Playfair_Display } from 'next/font/google'
const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-serif',
  weight: ['400', '500', '600', '700'],
})
// Add to html className: playfair.variable
```

Typography rules:
- Hero h1: Use Playfair Display, 72-80px desktop, 36-40px mobile, font-weight 400 (light/elegant, NOT bold), letter-spacing -0.03em
- Section headings: Playfair Display, 48-56px, font-weight 400
- Body text: Inter, 16px, line-height 1.7
- Card titles: Inter or Outfit, 16-18px, font-weight 500
- Price on cards: Outfit, 24px, font-weight 600
- All uppercase labels: Inter, 11px, letter-spacing 0.1em, text-transform uppercase

## COLOR PALETTE REFINEMENT

Update globals.css variables:

```css
:root {
  --bg-primary: #060608;        /* Nearly black, not navy */
  --bg-secondary: #0c0c10;     /* Slightly lighter black */
  --bg-card: #111114;          /* Card background */
  --bg-card-hover: #18181c;    /* Card hover */

  --text-primary: #f5f5f7;     /* Apple-style off-white */
  --text-secondary: #8e8e93;   /* iOS gray */
  --text-muted: #48484a;       /* Subtle gray */

  --accent-gold: #C9A96E;      /* Warm gold — primary accent */
  --accent-blue: #5B9BD5;      /* Muted, sophisticated blue — secondary */
  --accent-green: #6BAF7A;     /* Muted green for positive */
  --accent-amber: #D4A04A;     /* Warm amber for warnings */
  --accent-rose: #C27070;      /* Muted rose for danger */

  --border-subtle: rgba(255, 255, 255, 0.06);  /* Very subtle */

  --gradient-accent: linear-gradient(135deg, #C9A96E, #5B9BD5);
  --gradient-hero: linear-gradient(180deg, #060608 0%, #0a0a12 50%, #060608 100%);

  --shadow-card: 0 2px 20px rgba(0,0,0,0.3);
  --shadow-glow: 0 0 40px rgba(201, 169, 110, 0.08); /* Gold glow, very subtle */
}
```

This gives a black + gold + muted blue palette. Think: luxury watch brand, not tech startup.

## SPACING

Everything needs more room to breathe:
- Section padding: 160px top/bottom on desktop, 80px mobile
- Container max-width: 1200px (slightly narrower for elegance)
- Container side padding: 64px desktop, 24px mobile
- Property grid gap: 32px
- Between elements inside sections: more margin (24-32px between text blocks)

## HOMEPAGE REDESIGN

### Hero section
- Remove the country selector from above the hero (move it to nav or below)
- Remove the "🌍 Now live in Japan" badge
- Headline: "Find your dream home. Anywhere." in Playfair Display, weight 400, very large
- The word "Anywhere." on its own line, in gold color (not gradient, just solid --accent-gold)
- Subheadline: one line only, max 60 chars. Clean, no fluff.
- TWO buttons only: "Explore Japan" (solid gold bg, dark text) and "How It Works" (text link with arrow, no border)
- Stats row: remove emojis. Just clean text: "340 Properties · 29 Prefectures · 3 Risk Layers" — small, uppercase, letter-spaced, --text-muted color
- Background: solid --bg-primary. No radial gradients, no patterns. Just clean dark.

### "How it works" section — complete redesign
Instead of 6 emoji cards, do 3 elegant horizontal sections stacked vertically:

Section 1: "Aggregated" — left-aligned number "01" in large faded text, headline "Every listing, one place", one sentence description. No icon, no emoji.

Section 2: "Analyzed" — same format with "02", headline "Risk data on every property", one sentence.

Section 3: "Decided" — same with "03", headline "Know what to keep, what to avoid", one sentence.

Each section separated by a very thin line (1px, var(--border-subtle)). Minimal. Elegant.

### Featured Properties section
- Headline: "Selected Properties" (not "Featured Properties")
- NO background color change for this section — keep same --bg-primary
- Show 3 property cards with the new minimal design
- "View all" link — simple text link with arrow, not a button

### Remove pricing section entirely from homepage
Add a simple one-liner before the footer CTA: "From $10/month" — small, elegant, no pricing cards.

### CTA section
- "Start exploring" — simple, one button, centered
- No background gradient. Just more dark space.

## PROPERTY CARD REDESIGN

The card should feel like a luxury real estate listing, not a dashboard widget.

```
┌─────────────────────────┐
│                         │
│      [Large Image]      │  ← 280px height, 16:10 ratio
│      No overlays        │
│                         │
├─────────────────────────┤
│                         │
│  ¥2,800,000             │  ← Price: Outfit 24px, gold color
│  Traditional Home in    │  ← Title: Inter 16px, white
│  Otaru, Hokkaido        │  ← Location: Inter 13px, muted
│                         │
└─────────────────────────┘
```

That's it. No badges on the image, no quality bar, no emoji meta row, no lifestyle tags, no hazard indicator. Just: image, price, title, location. The card should feel like a gallery thumbnail, not a data card.

On hover: subtle border brightens, very slight image zoom (already exists). No glow, no transform translateY.

The detail page is where all the rich data lives. The card is just the invitation.

## NAVIGATION REDESIGN

- Logo: "CheapHouse" in one color (white), serif font (Playfair), no gradient
- Links: "Properties" "Quiz" "Pricing" — uppercase, 11px, letter-spacing 0.1em, --text-muted, hover: white
- Right side: Currency selector (minimal, just the code like "USD") + Login/SignUp
- Remove "Browse Properties" — just "Properties"
- Remove "Take Quiz" — just "Quiz"
- The nav should feel invisible — thin, quiet, no visual noise

## FOOTER REDESIGN

- Minimal: logo, 3 columns of links, copyright
- No emojis
- Very muted colors
- Thin, doesn't call attention to itself

## PROPERTY DETAIL PAGE

- Keep all the data sections (What to Know, Hazard, Lifestyle, etc.)
- But replace all emojis with clean text labels or simple SVG line icons
- The "What to Know" cards: remove emoji icons (✅❓⚠️🔍), replace with clean text headers with colored dot or line
- Hazard section: no emoji, just clean colored indicators
- More whitespace between sections
- Image gallery: larger, full-width on the detail page

## BROWSE PAGE

- Remove emoji from filters
- Clean up filter bar: less visual noise, more spacing
- Property grid with the new minimal cards
- Result count: small, muted, "47 properties" not "47 results found!"

## ANIMATIONS (install GSAP + Lenis)

```bash
npm install gsap lenis
```

1. Smooth scroll via Lenis (wrap in layout.js)
2. Hero text: fade in on load (opacity 0→1, y: 20→0), staggered per line
3. Section headings: fade up on scroll enter (ScrollTrigger)
4. Property cards: stagger cascade on scroll (0.1s delay between cards)
5. Page transitions: simple fade (opacity)
6. Numbers in stats: countUp on scroll enter
7. NO custom cursor (it's gimmicky for a real estate site — save it for portfolios)

All animations should be SUBTLE. Duration 0.6-0.8s, easing: power2.out. Nothing flashy.

## FILES TO CHANGE

1. globals.css — new color palette, remove glassmorphism, update spacing
2. app/layout.js — add Playfair Display font, add Lenis smooth scroll
3. app/page.js — complete homepage redesign
4. app/components/Nav.js — minimal nav
5. app/components/Footer.js — minimal footer
6. app/components/PropertyCard.js — minimal card (image, price, title, location only)
7. app/properties/page.js — clean browse page, no emojis in filters
8. app/properties/[slug]/page.js — clean detail page, no emojis, more whitespace
9. All components — search and destroy every emoji character

## VERIFICATION

After changes:
- npm run build — must pass
- Check homepage looks premium and minimal
- Check property cards are clean
- Check no emojis remain anywhere in the codebase:
  ```bash
  grep -r "[\x{1F300}-\x{1F9FF}]" app/ --include="*.js" || echo "No emojis found ✓"
  ```
- Push to GitHub + deploy

## THE GOLDEN RULE

When in doubt, remove. Less is always more. If something feels like it belongs on a SaaS dashboard, it doesn't belong here. This is a luxury real estate platform. Every element should earn its place on the page.
```
