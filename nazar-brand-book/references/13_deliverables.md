# 13 · Deliverables and asset pack

## Always
- `exports/<Brand>_Brand_Book_<year>.pdf`: the bound book
- `exports/pages/NN_<pid>.png`: one 1920 px PNG per page
- `exports/sheet.png`: the contact sheet (4 columns), which is what Kaif reviews
- `SPEC.md`: updated to match the built book ("where the spec and the book disagree, the book wins")
- `behance.md`: a write-up in short paragraphs (the name → the problem → the idea → the mark → the system → the book → credits)

## The asset pack: `assets/` (flat, simple, clearly named)
```
assets/
  README.md                          what each folder is for and which file to use where
  logo/        <brand>_mark_transparent.png, _on-<dark>.png, _on-<light>.png
               <brand>_mark-tagline_<colour>_transparent.png …
               svg/                  the master SVGs
  icons/       <brand>_icon_avatar_instagram_1080.png, _tiktok_1080, _linkedin_400
               <brand>_icon_<atom>_<colour>_1000.png
               <brand>_icon_favicon_32 / _180 / _512.png
               <brand>_icon_ig-highlight_01-<name>_1080.png …
               svg/
  social/      post templates, story template, launch posts, banner; svg/
  colour/      palette.png, palette.ase or .json, tokens.css
  fonts/       the OFL fonts only (with licence files); a note for any licensed font that isn't shipped
  brand-book/  the PDF and the Behance text
```
Naming: all lowercase, `<brand>_<type>_<variant>_<size>.<ext>`, with hyphens inside words and underscores between parts. No "final_v2_new".

## Generating it
Write `engine/assets.py` per brand: it renders each asset SVG with cairosvg at the stated sizes and writes the README. Then rerun it after any logo or colour change.

## Handover note to the client (in the README)
- Which logo to use by default (the mark alone, almost always)
- When to use the atom instead (small sizes, avatars), and that it never sits beside the mark
- Font licences
- Who to contact for anything not covered
