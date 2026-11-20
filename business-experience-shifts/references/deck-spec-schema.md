# Deck Spec Schema

The deck spec is one JSON file. It is the ONLY place domain content lives. `scripts/build_deck.py`
renders it; `scripts/validate_deck.py` checks it.

```
{
  "deck":     { "title", "kicker", "alignment_label?", "app": { "base_url" } },
  "personas": [ Persona, ... ]
}
```

## Persona (one role tab + one panel)
| Field | Meaning | Harvested from blueprint |
|---|---|---|
| `id` | short slug, unique (`rd`, `adjuster`) | derived from role |
| `short_role` | default wireframe role badge | role/actor name |
| `tab_label` | tab text (<= 28 chars) | role name |
| `tab_icon` | key from the icon set | choose by function |
| `role_title` | full title incl. abbreviation | RACI / actor register |
| `location` | team or site line | org / site info in SOP |
| `mission` | 1-2 sentences, what this role is accountable for | RACI "A/R" rows |
| `image` | `{url, alt}` workplace photo of that role | any stock/approved photo |
| `slides` | 2-4 Slide objects | see slide selection rules |

## Slide
| Field | Meaning |
|---|---|
| `num` | `"<personaIndex>.<n>"` e.g. `"2.1"` |
| `title`, `icon` | headline and icon key |
| `stage_badge` | blueprint stage / gate / zone reference |
| `as_is` / `to_be` | `{head_left, head_right, body}` (SOP ref + pain; target state) |
| `graphic` | `{title, icon?, svg}` inner markup for `viewBox="0 0 460 160"` |
| `wireframe` | see below |
| `signoff_text` | text after "Slide N Alignment:" |
| `owner` | accountable role |

## Wireframe
`url_path`, `role_badge?`, `sidebar[]`, `active_sidebar` (must equal one sidebar item),
`section_title`, `status? {text, tone: green|amber|navy}`, `intro_html?`,
`table {headers[], rows[]}` (row = array of cells, or `{total:true, colspan_first, cells[]}`;
a cell is a string or `{text, tone: green|amber|red}`), `actions[]` (last = primary button).

## Icon keys
flask, calendar, shield, dollar, globe, users, file, chart, clock, check, pin, lock, briefcase,
clipboard, settings, truck. Unknown key falls back to `file`.

## Rules
- Plain text only in text fields (escaped). Only `svg` and `intro_html` are raw.
- No emojis. Use words ("Pass", "Pending") not glyphs; the validator rejects emoji.
- Slide numbers must be prefixed by the persona's 1-based index.
