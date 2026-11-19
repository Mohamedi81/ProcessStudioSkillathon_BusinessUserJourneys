---
name: business-change-journey
description: Turns a To-Be process blueprint, or a process-analysis report (bottlenecks, root causes, optimization measures), into a single-file HTML change-journey deck for business stakeholders. Each role gets As-Is vs To-Be slides, a bespoke infographic, an enterprise UI wireframe and a sign-off tracker. An As-Is SOP is optional. Use when the user wants stakeholder alignment slides or a change journey from a blueprint or analysis.
allowed-tools: run_skill_script read_wiki_page write_temp_file read_temp_file save_output_text save_output_file
---

# Business Change Journey Deck

Inputs: ONE of these is enough. An As-Is SOP is optional and only adds detail.
- a **To-Be blueprint** (roles, steps, systems, KPIs, human-approval points), or
- a **process analysis** (measured As-Is bottlenecks plus planned fixes and target KPIs).

If both a blueprint and an analysis are given, use the blueprint for roles and To-Be, and the analysis for As-Is numbers.
Output: one HTML file (`journey-deck.html`). Never write code. You write one JSON file, and a bundled script renders it.

## Do not ask questions
Work from what you were given. Do not wait for confirmation. Use these defaults and say so in your final message:
- Deck title: the process name from the source plus " Change Journey". No company name unless the source has one.
- `kicker`: "Business Change Journey".
- `app.base_url`: `app.internal.example`.
- Photos: the neutral stock URLs under "Photos" below.
- Only the HTML deck is produced. No PowerPoint.
- Record IDs, supplier and customer names in wireframes are made up: label them "illustrative" in `signoff_text`.
- Any number or target not in the source is also "illustrative". Never present an invented figure as sourced.

## Steps
1. **Read** the provided document(s) fully.
2. **Harvest** (silently): the human roles, the steps each role owns, the system each step touches, As-Is pain with its number, the To-Be fix, and target numbers. Roles = distinct people who own a decision or approval. If the source names no roles, infer them from who normally does each step and say that you inferred them.
3. **Size the deck**: 2 to 4 slides per role, one slide per atomic step or tightly coupled pair. Prefer steps with a measurable As-Is pain, a human decision, and a system touchpoint. Merge roles with fewer than 2 meaningful steps. Total slide count is derived, never preset.
4. **Write the spec**: author `deck-spec.json` (format below) and save it with `write_temp_file`.
5. **Build**: call `run_skill_script` with script `build_journey_deck.py`, `--input deck-spec.json`, `--output journey-deck.html`.
   - It validates the spec first. If it fails, the error lists every issue. Fix the spec, save it again, and rebuild. Repeat until it passes.
6. **Deliver**: save `journey-deck.html` with `save_output_file`. Then reply with a short summary: roles and slide count, the defaults you used, and which numbers are illustrative.

## deck-spec.json format
```
{
  "deck": { "title": "...", "kicker": "...", "alignment_label": "Stakeholder Alignment",
            "app": { "base_url": "app.internal.example" } },
  "personas": [ {
      "id": "buyer",                     // unique slug
      "short_role": "Buyer",             // default role badge in wireframes
      "tab_label": "Buyer",              // <= 28 chars
      "tab_icon": "briefcase",
      "role_title": "Buyer (Procurement)",
      "location": "Procurement team",
      "mission": "One or two sentences: what this role is accountable for.",
      "image": { "url": "<photo url>", "alt": "<description>" },
      "slides": [ {
          "num": "1.1",                  // "<persona number>.<slide number>", persona numbers start at 1
          "title": "...", "icon": "clipboard",
          "stage_badge": "Requisition to PO",
          "as_is":  { "head_left": "As-Is", "head_right": "<source ref or key number>", "body": "<pain, with number>" },
          "to_be":  { "head_left": "To-Be", "head_right": "<target>", "body": "<target state>" },
          "graphic": { "title": "...", "icon": "chart", "svg": "<inner SVG markup for viewBox 0 0 460 160>" },
          "wireframe": {
            "url_path": "orders/PO-1234", "role_badge": "Buyer",
            "sidebar": ["Orders", "Contracts", "Approvals"], "active_sidebar": "Orders",
            "section_title": "...", "status": { "text": "Pending", "tone": "amber" },
            "intro_html": "<optional short HTML>",
            "table": { "headers": ["Field", "Value"],
                       "rows": [ ["Price", {"text": "Mismatch", "tone": "red"}] ] },
            "actions": ["Reject", "Approve"]       // last one is the primary button
          },
          "signoff_text": "...", "owner": "Buyer"
      } ]
  } ]
}
```
Required: everything above except `alignment_label`, `tab_icon`, `icon`, `role_badge`, `status`, `intro_html`.
- `active_sidebar` must equal one `sidebar` item.
- Table cell = string or `{text, tone: green|amber|red}`; `status.tone`: green|amber|navy.
- Icon keys: flask, calendar, shield, dollar, globe, users, file, chart, clock, check, pin, lock, briefcase, clipboard, settings, truck.
- JSON only: no comments in the real file, and escape double quotes inside strings.

## Rules
- **No emojis or pictograph glyphs.** Use words ("Pass", "Pending"). The build fails on emoji.
- Plain text everywhere except `graphic.svg` and `intro_html`. No `<script>` or event handlers in SVG.
- One infographic per slide, chosen by data shape. Palette: navy `#1e3a8a`, blue `#3b82f6`, green `#10b981`, amber `#f59e0b`, red `#ef4444`, grey `#64748b`. Font `sans-serif`, size 7.5 to 13. Keep all text inside the 460x160 viewBox.

  | Data shape | Graphic |
  |---|---|
  | Sequence with waiting time | timeline of steps with day labels |
  | Before vs after rate | two bars with the target marked |
  | Components of a total vs a limit | stacked bar with limit line |
  | Value vs tolerance | gauge |
  | Many candidates narrowed down | funnel |
  | One trigger fanning out to checks | hub and spoke |
- Every number in `as_is` and `to_be` comes from the source, or is labelled illustrative.
- If the source data is old or from a sample period, say so in `signoff_text` of the affected slides.

## Photos
Use these neutral workplace photos, picked by the closest role. Use the alt text given here, because it matches what the photo shows:
- Office or desk roles: `https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=400&h=400&fit=crop`, alt "Colleagues working on laptops in an office"
- Warehouse or operations roles: `https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=400&h=400&fit=crop`, alt "Warehouse shelves with boxes"
- Finance or treasury roles: `https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400&h=400&fit=crop`, alt "Tax forms, a calculator and a pen on a desk"
- Laboratory or technical roles: `https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=400&h=400&fit=crop`, alt "Laboratory glassware with a pipette"

## Examples
`examples/drinkit/` and `examples/claims-test/` hold complete specs (`deck-spec.json`) and their decks. Learn the structure from them; never copy their content, names or numbers.
