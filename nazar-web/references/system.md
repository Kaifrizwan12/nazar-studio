# The visual system on the web

## 1. Tokens
- **Base tokens:** raw values (the palette, the spacing scale, radii, durations).
- **Semantic tokens:** roles (`color-text-primary`, `color-surface-brand`, `color-border-subtle`, `space-section`), which point to base tokens [SRC].
- **Component tokens** only when needed.
- Light and dark themes are swaps of semantic tokens. Check contrast for every pair.
- Export as CSS custom properties and JSON (e.g. the W3C design tokens format), shared with the brand book's palette and type.

## 2. Responsive type
- A modular scale (e.g. ratio 1.2–1.25 for text-heavy pages, larger for marketing heroes) [SRC], with **fluid sizes** via `clamp()` between a mobile and a desktop size.
- Body text 16–20 px; line length 45–75 characters; line height 1.4–1.6 for body, tighter for display.
- At most 2 families and 3–4 weights in total (performance). Use variable fonts where they reduce files. Self-host with `font-display: swap`. Check the web licence.
- Second script and RTL: set `dir` and `lang`, mirror the layout where needed, and use proper fonts for each script.

## 3. Grid and breakpoints
- A fluid 4-column (mobile) / 8 (tablet) / 12 (desktop) grid, or the brand's own grid, with a maximum content width.
- Breakpoints driven by content, not devices. Typical points around 600 / 900 / 1200 / 1600 px.
- A spacing scale on a base unit (4 or 8 px).

## 4. Components
Buttons (primary, secondary, text; with hover, focus, active, disabled), links, navigation (desktop and mobile), cards, forms (labels, errors, help text), media blocks, quotes, accordions, the footer. Every component in every state, including focus (≥ 3:1 contrast for focus indicators and UI boundaries, per WCAG 1.4.11) [SRC].

## 5. Art direction on the web
- **Real imagery** from the art direction kit, cropped per breakpoint (art-directed `<picture>` sources, not just scaled).
- 1–2 **signature moments**: a scroll-driven story, a hero built from the brand's atom, a cinematic section (letterbox video, title cards), a playful hidden detail (the brand book's giggle, translated to the web).
- Texture with care: subtle grain or halftone in CSS or SVG, never heavy images that slow the page.

## 6. Motion on the web
Use the tokens from `nazar-motion` (signature easing, duration palette). Animate transform and opacity (cheap), respect `prefers-reduced-motion`, and keep scroll effects smooth and optional to understanding.
