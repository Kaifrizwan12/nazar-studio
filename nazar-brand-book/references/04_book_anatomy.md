# 04 · Book anatomy: decided per project

There is no fixed structure. The section order, length, format and page system are **designed for each brand**, from its idea, its audience and where the book will be used. What stays constant is the *thinking* that the best identity work shares. Decide the anatomy in intake round 2 (Q6) and lock it in `SPEC.md`.

## 1. What every great guideline does (the universal core)
Across the strongest identity manuals and guidelines (the classic modernist manuals such as NASA 1975, NYCTA 1970, Lufthansa and Munich 1972, and contemporary systems from studios like Pentagram, Wolff Olins, Collins, Koto, Base, Mucho and Order), the same qualities recur:
1. **It explains before it instructs.** The reader understands *why* (the idea, the problem) before learning *how*. Rules without reasons get broken.
2. **It's a system, not a pile of assets.** It shows the parts (mark, colour, type, grid, image, voice) and how they combine, including how to make something new that isn't in the book.
3. **It shows, then tells.** A correct example beats a paragraph. Rules are short, and examples are large.
4. **It's built on the brand's own grid.** The book itself demonstrates the system it describes.
5. **It's honest about use.** It covers real formats at real scale, the edge cases (small sizes, bad backgrounds, other languages) and misuse.
6. **It's usable by someone who wasn't in the room.** A junior designer, a printer or a social media manager can act on it alone.
7. **It has a point of view.** The best ones have a voice and at least one memorable idea in how they're made, not just what they contain.

## 2. Content modules (choose what this brand needs)
**Core (almost always):**
- Why / the idea: the problem, the name, the one idea, beliefs or principles
- Logo: primary mark, lockups, the small-size symbol or atom, clear space and minimum size, misuse
- Colour: palette and proportions, accessibility pairings, print values
- Type: roles, scale, the second script if any
- Graphic language: the atom, textures, patterns, iconography, imagery rules
- Voice: traits, copy device, sample lines
- Applications: the formats this brand really uses
- Close: contacts, credits, sources

**Optional (add them when the brand needs them):**
- Naming and architecture (sub-brands, product ranges, co-branding)
- Mascot or character
- Photography or illustration direction
- Motion and sound (logo animation, transitions, sonic mark)
- Digital and UI tokens (components, accessibility, dark mode)
- Social playbook (pillars, templates, captions, launch plan)
- Packaging system (range architecture, dielines, legal panels)
- Environment and signage (wayfinding, retail, events)
- Data visualisation
- Co-branding and partner rules
- A downloadable asset index

The order is designed per brand too. The default logic is **meaning → look → use** (why, then how it looks, then how it's used), but break it when the brand's story demands: a field guide might open with the specimen, and a newspaper with the headline.

## 3. Structure: pick the book's narrative device
Every Kaif book has a device that shapes its order and pacing. Choose it from the brand's idea:
| Device | How it shapes the book | Fits |
|---|---|---|
| **Chapters** | Plain numbered sections, beautifully paced | Institutions, B2B, when clarity is the point |
| **A day** | Sections follow hours, light pages turning to dark | City, hospitality, routines |
| **A route / journey** | Each section is a stop on a real or imagined map | Delivery, travel, origin stories |
| **A process** | Seed → harvest → dry → pack → shelf; brief → launch | Food, craft, manufacturing |
| **A specimen collection** | Each element catalogued like a natural-history plate | Food, natural products, collectors |
| **An archive** | The brand presented as found documents, numbered | Heritage, revivals |
| **A manual** | Strict numbered rules, a reference format | Infrastructure, tech, systems-heavy brands |
| **A conversation** | Questions and answers, a Q&A book | Service, community brands |

## 4. Format: pick the object
Choose the physical or digital form. At least one option must differ from the previous client's book.
| Format | Feel | Fits |
|---|---|---|
| Landscape screen deck (16:9) | Presentation-native, digital first | Agencies, tech, pitch-led brands |
| Portrait print manual (A4 / US Letter) | A classic reference manual, a binder | Institutions, large teams |
| Pocket book (A5 / A6) | Intimate, carried around | Small brands, retail staff |
| Field guide | Plates, specimen numbers, captions | Food, nature, craft |
| Ledger / account book | Ruled lines, stamped numbers, receipts | Trade, wholesale, heritage shops |
| Newspaper / zine | Columns, headlines, classifieds | Media, launches, youth brands |
| Menu / label book | Every page a label or card | Restaurants, FMCG |
| Passport / ticket book | Stamps per section | Travel, events |
| Card deck / box set | One rule per card | Workshops, playful brands |
| Living web guideline | Searchable, with downloadable assets | Digital products, big teams (build alongside the PDF) |

## 5. Page system: derive it, don't copy it
Set the system in code **before page 1**, so every fix is global. Derive the values from the chosen format:
- **Page size** from the format (1920×1080 for screen, A4 at 300 dpi for print...).
- **Margins** about 6–8% of the short side. Inner margins are larger for bound print.
- **Grid**: columns that suit the content (12 for flexible screen layouts, 6 or 8 for print, 2 for field-guide plates), with a baseline unit taken from the body leading.
- **Furniture** (section label, page number, any page stamp) in fixed positions. It's quiet and small, often mono.
- **Heading block**: fixed positions for kicker / title / subtitle, so text starts are identical across pages.
- **The type scale** comes from `06_type.md`.
All of these live in `brand.json` → `"page"`. The engine reads them, so changing one value changes every page.

## 6. Page types (a palette to compose with)
Statement (one sentence plus one graphic) · **Make your own** (the system applied to something not in the book, so teams learn the logic, like Mailchimp's fictitious brands) · Divider · System table · Exploded diagram · Grid of N · Spec sheet · Do / don't · Before / after · Specimen plate · Timeline · Map · Reveal. Use the minimum number of types, and repeat them consistently, so the book feels designed rather than assembled.

## 7. Length guide
Compact 20–30 pages · standard 40–50 · full 60–80. Length follows the modules chosen, not ambition. Every page must earn its place: if two pages say the same thing, merge them.

## A worked example
The case study in `15_case_nazar.md` was a 16:9 screen deck structured as one day across a real city, with a 12-column grid and meaning → look → use ordering (`15_case_nazar.md`). It's one answer, not the template.
