# The motion system

## 1. Easing (one signature curve for most movement)
- Define a **signature curve** as a cubic-bezier (e.g. a strong ease-out for entrances like `cubic-bezier(0.2, 0, 0, 1)`, and a matching ease-in for exits), used for about 80% of motion [SRC].
- Add at most 2 more: a "standard" in-out curve and, if the personality allows, a spring or overshoot for playful moments.
- Never linear, except for continuous loops (rotation, scrolling tickers, progress).

## 2. Duration palette (3–4 values)
| Token | Typical | Use |
|---|---|---|
| quick | 100–200 ms | UI feedback, small elements |
| standard | 250–400 ms | Most UI transitions |
| expressive | 500–900 ms | Hero moments, slides, section changes |
| ident | 1–2 s (up to ~4 s for film) | Logo animation |
Larger distances and larger elements get longer durations; exits are slightly faster than entrances.

## 3. Transitions and entrance pattern
- One signature entrance (e.g. elements rise 24 px and fade in, staggered 40–60 ms), and one signature transition between scenes (a wipe in the brand's shape, a match cut on the atom, a mask reveal).
- Transitions should come from the brand's geometry (its atom, its angle, its grid).

## 4. Choreography
- **Hierarchy in time:** the most important element moves first, the rest follow in reading order.
- Stagger small groups (40–80 ms), and don't animate everything at once.
- Keep 1–2 things moving at a time on screen; stillness creates focus.
- Hold the final frame long enough to read (about 1 s for the logo end frame).

## 5. Typography in motion
- Animate by word or line, not by letter (unless that's the idea); keep reading time ≥ ~0.3 s per word.
- Kinetic type stays on the brand's grid; never stretch or distort the brand faces.
- Captions on all spoken video, in the brand caption style.

## 6. Tokens for developers
Export the system as CSS custom properties and/or JSON, so product and web use the same values:
```
--motion-ease-signature: cubic-bezier(0.2, 0, 0, 1);
--motion-duration-quick: 150ms;
--motion-duration-standard: 300ms;
--motion-duration-expressive: 700ms;
```
Also include the `prefers-reduced-motion` alternatives (crossfade or no motion).
