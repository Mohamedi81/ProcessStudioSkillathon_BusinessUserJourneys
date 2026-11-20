# Harvest Checklist: Blueprint + SOP -> Deck Spec

Run this BEFORE writing any slide. Build a short harvest table (section E) for yourself and use it to write the spec. Do not stop to ask the user to confirm it.

## A. Inputs to read
One of these is enough:
1. To-Be blueprint (EAEF / ATS register, Autonomy Zones, HITL table, agent/data-product list, MCP tools).
2. Process analysis (measured bottlenecks, root causes, optimization measures, target KPIs, blueprint hand-off).

Optional: As-Is SOP / process description (steps, owners, tools, pain points). It adds detail but is not required.

## B. Extract these (with the source line for each)
| # | Item | Where to look | Becomes |
|---|---|---|---|
| 1 | Company / domain name | titles, headers | `deck.kicker`, `deck.title` |
| 2 | Core systems (ERP, PLM, CRM, ticketing...) | tool columns, MCP schemas | wireframe sidebar, table cells, `base_url` host |
| 3 | Human roles/actors | RACI, HITL table, swimlanes | one persona each |
| 4 | Per-role responsibilities | RACI A/R rows | `mission` |
| 5 | Stages / gates / zones | stage numbering, gate list | `stage_badge` |
| 6 | As-Is pain per step | SOP steps, interview notes | `as_is` |
| 7 | To-Be capability per step | Atomic Thinking Steps, agents | `to_be` |
| 8 | Hard numbers: thresholds, tolerances, SLAs, targets | blueprint KPIs, policies | graphic + table values |
| 9 | Approval / decision actions | HITL table | wireframe `actions` |
| 10 | Real example record (ID, item name) | SOP examples, or invent clearly-fictional | url_path, section_title |

## C. Persona and slide selection rules (replaces the old fixed "18 slides")
- One persona per distinct human role that owns a HITL decision or accountable step. Merge roles
  with <2 meaningful steps; split roles whose steps span unrelated systems.
- 2-4 slides per persona. Each slide = ONE atomic step or tightly coupled step pair.
- Prefer steps that (a) have a quantifiable As-Is pain, (b) have a human decision point, (c) touch a system.
- Total deck size = sum of persona slides; the counter is computed, never hardcoded.
- If a number is not in the sources, mark it "illustrative" in `signoff_text` or ask the user. Never
  present invented figures as sourced facts.

## D. Infographic selection (match data shape, not domain)
| Data shape | Graphic |
|---|---|
| Components summing to a total vs a limit | waterfall / stacked bar with limit line |
| Value vs tolerance band | gauge(s) |
| Items x jurisdictions/criteria, pass/fail | matrix / heatmap grid |
| Many candidates narrowed by criteria | funnel |
| One trigger fanning out to checks | hub-and-spoke ripple |
| Score vs peer distribution | quintile / benchmark bars |
| Allocation across categories | stacked share bar (e.g. mix split) |
| Sequence with waiting time | timeline / swimlane |
Palette: navy `#1e3a8a`, blue `#3b82f6`, pass green `#10b981`/`#065f46`, warn amber `#f59e0b`/`#92400e`,
fail red `#ef4444`, grey text `#64748b`. Font `sans-serif`, sizes 7.5-13.

## E. Harvest table (working notes, not shown for confirmation)
`Persona | Source role | Slides (title, stage) | System | Key number`
