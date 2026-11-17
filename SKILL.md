---
name: business-change-journey
description: Use when the user wants business-stakeholder change-journey slides (As-Is vs To-Be, bespoke infographic, enterprise UI wireframe, sign-off tracker) generated from ANY process blueprint (EAEF/ATS/DPS) plus an As-Is SOP. Produces a single-file 16:9 HTML deck and optionally a PPTX. Domain-neutral and portable.
---

# Business Change Journey Deck (portable)

Turns a To-Be process blueprint plus an As-Is SOP into a persona-by-persona alignment deck.
**All domain content lives in a JSON deck spec. Nothing about any specific company, system or
industry is built into this skill.** If you catch yourself reusing a name, number or system from an
example, stop: harvest it from the user's sources instead.

## Files in this skill
| Path | Role |
|---|---|
| `references/harvest-checklist.md` | What to extract, persona/slide selection rules, infographic selection |
| `references/deck-spec-schema.md` | The JSON contract |
| `assets/deck.css`, `assets/deck-shell.html` | Fixed look and behaviour (domain-free) |
| `scripts/build_deck.py` | spec -> HTML |
| `scripts/validate_deck.py` | schema, emoji, leakage and HTML integrity checks |
| `references/portability-tests.md` | How portability is proven |
| `examples/` | Reference specs and a foreign test blueprint. Learn structure from them, never copy content |

## Workflow
1. **Collect inputs.** Use `ask_followup_question` if the As-Is SOP or To-Be blueprint is missing.
   Read them fully (`read_file`, or `office_read` for .docx/.pptx/.xlsx).
2. **Harvest.** Follow `references/harvest-checklist.md`. Present the harvest table (persona, slides,
   system, key number, source line) and get the user's confirmation before building.
3. **Write the spec.** Create `deck-spec.json` per `references/deck-spec-schema.md`.
   - Every figure must trace to the sources; label anything invented as illustrative.
   - Pick each infographic by data shape (checklist section D), hand-writing the SVG with
     `viewBox="0 0 460 160"`.
4. **Validate.** `python3 scripts/validate_deck.py deck-spec.json`. Fix all issues.
5. **Build.** `python3 scripts/build_deck.py deck-spec.json <name>.html`, then re-run the validator
   with `--html <name>.html`.
6. **If this deck follows a different domain in the same workspace**, also run the validator with
   `--forbid <previous-domain-terms.txt>` to prove no residue carried over.
7. **PPTX (optional).** Only on request: load `office-insights` and build one slide per spec slide
   (left: As-Is/To-Be/graphic; right: wireframe table).

## Fixed layout (do not vary per domain)
- 16:9 slide card: header (number, title, stage badge), two columns, footer sign-off bar.
- Left: red As-Is box, green To-Be box, topic-specific infographic.
- Right: browser-chrome wireframe (URL, role badge), sidebar, data table, action buttons.
- Top: global alignment meter, computed from the number of sign-off boxes.

## Design rules
- No emojis or pictograph glyphs; use words. 2px stroke SVG icons from the built-in set.
- Sober consulting palette; one bespoke infographic per slide; no generic arrow chains.
- One workplace photo per persona that matches the role's real environment.
- Wireframe URL host comes from the user's real or plausible internal domain (`deck.app.base_url`).

## Sizing rules (replace any fixed count)
Personas = distinct human roles owning a decision in the blueprint. 2-4 slides each.
Deck size is derived, not preset. See the checklist.

## Portability guarantee
Before telling the user the deck is done: validator PASS, and if a prior domain exists in the
workspace, leakage check PASS. Report both results.
