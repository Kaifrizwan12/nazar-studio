# Handoff and QA

## Accessibility (WCAG 2.2 AA baseline) [SRC]
- Text contrast ≥ 4.5:1 (large text ≥ 3:1); UI components and focus indicators ≥ 3:1 against adjacent colours.
- Colour is never the only signal (errors, links, states).
- Full keyboard access in a logical order, visible focus, and skip links.
- Semantic headings (one H1 per page, no skipped levels), labelled form fields, descriptive links.
- Alt text for meaningful images; empty alt for decorative ones; captions for video.
- Reduced motion respected; no flashing content.
- Touch targets around 44 × 44 px minimum.

## Performance basics
- Images in modern formats (AVIF/WebP), sized per breakpoint, lazy-loaded below the fold, with explicit width and height to avoid layout shift.
- Few font files (subset, preload the critical one).
- No heavy libraries for small effects; video compressed with a poster frame.
- Test on a mid-range phone on a slow connection.

## SEO basics
A unique title and meta description per page, clean URLs, semantic HTML, Open Graph images (designed with brand templates), a sitemap, and correct `lang` attributes.

## Developer handoff
- Tokens (CSS/JSON), the component library with all states, page designs at mobile, tablet and desktop, the interaction and motion spec, an asset export (SVG icons and logos, optimised images), copy in a document, and annotations for anything non-obvious.
- One review of the built site against the designs before launch.

## Web QA (on top of core `qa_design.md`)
- [ ] Every page has one clear primary action
- [ ] Real copy and real images; no placeholders left
- [ ] Tokens are used everywhere (no stray hex values or one-off sizes)
- [ ] Responsive at every breakpoint, including very narrow (320 px) and very wide
- [ ] Accessibility checks pass (contrast, keyboard, focus, headings, alt text, reduced motion)
- [ ] Fonts licensed for the web, with a limited number of files
- [ ] Performance tested on a real phone
- [ ] Open Graph images and favicons in place
- [ ] Signature moment works without breaking accessibility or performance
- [ ] Forms tested end to end; error states designed
