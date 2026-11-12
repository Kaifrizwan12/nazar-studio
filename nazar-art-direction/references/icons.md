# Icon systems

## Grid and keylines (Material Design's system icons are a well-documented model) [SRC]
- A **24 px** base grid with about **2 px padding**, giving a 20 px live area.
- **Keyline shapes** for consistent visual size: e.g. a 20 px circle, an 18 px square, and 20 × 16 / 16 × 20 rectangles. Round shapes use the circle, square shapes the square, so that every icon *looks* the same size [SRC].
- Design at 100% scale for pixel accuracy, then check at other sizes.

## Style decisions
- **Stroke:** one weight for the whole set (often 1.5–2 px at 24 px), consistent caps and joins
- **Corners:** one radius (or square), matching the brand's geometry
- **Angles:** a fixed angle set (e.g. 45° only)
- **Fill:** outline / filled / duotone. Pick one, plus a filled "active" state if needed
- **Detail:** minimal; it must read at 16 px
- **Built from the brand's atom** where possible, so the icons feel like the logo's family

## Optical balance
- Break the grid where the eye needs it: optical adjustments are deliberate departures from strict keylines [SRC].
- No icon should look heavier or lighter than another at the same size [SRC]. Check the whole set side by side, blurred.
- Centre by visual mass (play arrows shift right; triangles sit lower).

## Delivery
SVG (clean, single path where possible, `currentColor` fills), an icon font or sprite if needed, PNG at standard sizes, a naming convention (`icon-<name>-<style>`), and an overview sheet with names. Add a usage page: sizes (16 / 20 / 24 / 32 / 48), clear space, colours, accessibility (icons with meaning need labels).
