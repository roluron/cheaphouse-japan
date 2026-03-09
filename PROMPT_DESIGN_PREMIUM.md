# PROMPT À COLLER DANS ANTIGRAVITY — Design Premium Overhaul

```
I want to upgrade the CheapHouse Japan frontend to a premium, award-worthy design level. The current dark theme works but it needs to feel like a high-end product — think Awwwards-level quality.

Here are 3 reference sites that define the direction I want:

## Design References

1. **lobelia.earth** — Climate data platform, dark theme
   - Massive typography with tight letter-spacing (-0.03em)
   - GSAP scroll-triggered animations (text reveals word by word, sections fade up)
   - Data visualization that feels elegant, not clinical
   - Full-screen sections with generous spacing (120-160px padding)
   - Subtle grid/dot pattern backgrounds
   - Gold/warm accent on dark background

2. **victor-sin.com** — Creative developer portfolio, Paris
   - WebGL/shader subtle background effects (grain, noise texture)
   - Custom cursor (small circle that grows on hover over clickable elements)
   - Butter-smooth page transitions (fade out → fade in)
   - Fluid motion everywhere — nothing is static
   - Stagger animations on lists/grids

3. **cathydolle.com** — Minimalist luxury, React, Awwwards SOTD
   - Extreme whitespace discipline — every element breathes
   - Mix of serif (for headings) + sans-serif (for body) typography
   - Micro-animations that are subtle, not flashy
   - Clean, quiet confidence in the layout
   - Nothing feels crowded or rushed

## What to implement

### 1. Install animation libraries

```bash
npm install gsap @gsap/react lenis
```

### 2. Typography upgrade

- Hero h1: 72px desktop / 40px mobile, font-weight 800, letter-spacing: -0.03em
- Section headings: 48-56px desktop, letter-spacing: -0.02em
- Consider adding a premium serif font for hero/display headings. Add to layout.js:
  ```javascript
  import { Playfair_Display } from 'next/font/google'
  const playfair = Playfair_Display({ subsets: ['latin'], variable: '--font-serif' })
  ```
  Use it for the main hero headline and section titles. Keep Outfit for subheadings and Inter for body.

### 3. Spacing overhaul

- Section padding: increase from 80px to 140px vertical on desktop, 80px on mobile
- Property grid gap: increase from 24px to 32px
- Container max-width: keep 1280px but increase side padding to 48px desktop
- Between major sections: add extra breathing room
- Property card body padding: increase from 20px to 24px

### 4. Smooth scroll (Lenis)

Create a SmoothScroll provider component and add it to layout.js:

```javascript
'use client'
import { useEffect } from 'react'
import Lenis from 'lenis'

export default function SmoothScroll({ children }) {
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    })
    function raf(time) {
      lenis.raf(time)
      requestAnimationFrame(raf)
    }
    requestAnimationFrame(raf)
    return () => lenis.destroy()
  }, [])
  return children
}
```

### 5. GSAP scroll animations

Create a useScrollAnimations hook or component:

- **Hero text**: staggered word-by-word reveal on page load (split text into spans, animate each with 0.05s delay)
- **Section headings**: fadeUp (y: 40 → 0, opacity: 0 → 1) when entering viewport via ScrollTrigger
- **Property cards in grid**: stagger cascade — each card fades up with 0.1s delay after the previous one
- **Stats numbers** (250+ Properties, 47 Prefectures, etc.): countUp animation from 0 to target number when section enters viewport
- **What-to-Know cards** on detail page: stagger reveal (0.15s between each card) with the colored left border growing from 0 to full height

Register ScrollTrigger:
```javascript
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
gsap.registerPlugin(ScrollTrigger)
```

### 6. Custom cursor (desktop only)

Create a CustomCursor client component:
- Small circle (12px diameter, border only, accent color) that follows mouse position with slight lag (lerp 0.08)
- On hover over links, buttons, cards: circle grows to 48px with a fill background at low opacity
- On hover over images: circle shows a "View" text or expands differently
- Hide the default cursor via CSS: `* { cursor: none }` on desktop only
- Detect touch devices and disable completely on mobile/tablet:
  ```javascript
  if ('ontouchstart' in window) return null
  ```

### 7. Property card visual upgrade

- Image section: increase height from 220px to 260px, ratio 16:10
- Add a subtle gradient overlay on the bottom 40% of the image (transparent → dark) for text readability if you ever overlay text
- On hover: the existing image zoom is good, add a subtle border-color transition to accent
- Lifestyle tag badges: slightly larger padding, more rounded
- Price typography: slightly larger (24px instead of 22px)

### 8. Hero section upgrade

- Add a subtle animated background: either a CSS gradient that slowly shifts, or a subtle dot/grid pattern that has parallax movement on scroll
- The stats row below the CTA: animate numbers counting up on load
- Add a subtle floating animation on any decorative elements

### 9. Page transitions

Use a simple fade transition between pages:
- When navigating: current page fades out (opacity 1→0, 200ms)
- New page fades in (opacity 0→1, 300ms)
- Can use framer-motion AnimatePresence if easier:
  ```bash
  npm install framer-motion
  ```

### 10. Detail page polish

- Image gallery: add a smooth transition when switching images (crossfade, not instant swap)
- What-to-Know section: the 4 cards should have more visual weight — slightly larger padding, the colored left border should be 4px wide, add a very subtle background tint matching the card color
- Hazard indicators: instead of just text badges, add small horizontal bar gauges that fill based on level (low=30%, moderate=60%, high=90%) with animated fill on scroll enter
- Make the sticky sidebar smoother (check that it doesn't jump on scroll)

### 11. Color palette refinement

Consider adding a warm accent alongside the current blue:
- Keep var(--accent-blue) as primary accent
- Add var(--accent-gold): #ECD06F or #D4A853 for premium feel
- Use gold sparingly: on the logo, on premium badges, on CTA hover states
- This creates a "dark + blue + gold" palette that feels luxurious

Update globals.css:
```css
--accent-gold: #D4A853;
--gradient-premium: linear-gradient(135deg, #38bdf8, #D4A853);
```

### 12. Loading states

- Add skeleton loaders for property cards (pulsing placeholder shapes matching card layout)
- Add a subtle loading bar at the top of the page during navigation (like YouTube's red bar)
- Property images: fade in on load (opacity 0 → 1 transition when image loads)

## RULES

- Keep ALL existing functionality — this is a visual upgrade only
- Keep the dark theme as the base
- Test on mobile — animations should be reduced or disabled on mobile for performance
- Custom cursor is desktop-only
- GSAP ScrollTrigger animations should use `once: true` so they only play once per session
- Don't over-animate — the goal is subtle premium feel, not a circus
- Performance: animations should run at 60fps. Use transform and opacity only for GSAP tweens (no animating width/height/margin)
- Build must pass with zero errors after changes
```
