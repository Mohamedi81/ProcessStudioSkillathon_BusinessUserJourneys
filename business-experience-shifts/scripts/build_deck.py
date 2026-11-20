#!/usr/bin/env python3
"""Render a deck spec (JSON) into a single-file Business Experience Shifts HTML deck.

Usage: python3 build_deck.py <deck-spec.json> <output.html>

The spec holds ALL domain content. This script and assets/ hold NO domain content.
Text fields are HTML-escaped. Fields ending in `_html` and `svg` are inserted raw.
"""
import html
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

# Generic 24x24 stroke icons (inner SVG markup). Reference by name in the spec.
ICONS = {
    "flask": '<path d="M10 2v7.31M14 2v7.31M8.5 2h7M14 9.3a6.5 6.5 0 1 1-4 0"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "dollar": '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
    "chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "check": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "briefcase": '<rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    "clipboard": '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h0a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h0a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v0a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "truck": '<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
}

TONES = {"green", "amber", "navy"}


def esc(value):
    return html.escape(str(value), quote=True)


def icon(name, size, stroke="currentColor", width=2):
    inner = ICONS.get(name, ICONS["file"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{stroke}" stroke-width="{width}">{inner}</svg>'
    )


def cell_html(cell):
    if isinstance(cell, dict):
        tone = cell.get("tone")
        color = {"green": "var(--forest)", "amber": "var(--amber)", "red": "var(--crimson)"}.get(tone)
        style = f' style="color:{color}; font-weight:700;"' if color else ""
        return f"<td{style}>{esc(cell['text'])}</td>"
    return f"<td>{esc(cell)}</td>"


def table_html(table):
    head = "".join(f"<th>{esc(h)}</th>" for h in table["headers"])
    rows = []
    for row in table["rows"]:
        if isinstance(row, dict) and row.get("total"):
            cells = row["cells"]
            span = row.get("colspan_first", 1)
            first = f'<td colspan="{span}">{esc(cells[0])}</td>'
            rest = "".join(cell_html(c) for c in cells[1:])
            rows.append(f'<tr style="background:#f8fafc; font-weight:700;">{first}{rest}</tr>')
        else:
            cells = row["cells"] if isinstance(row, dict) else row
            rows.append("<tr>" + "".join(cell_html(c) for c in cells) + "</tr>")
    return (
        '<table class="app-table" style="margin-top:8px;"><thead><tr>'
        f"{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def contrast_html(kind, box):
    return (
        f'<div class="contrast-box {kind}"><div class="contrast-head">'
        f'<span>{esc(box["head_left"])}</span><span>{esc(box["head_right"])}</span></div>'
        f'<div class="contrast-body">{esc(box["body"])}</div></div>'
    )


def wireframe_html(wf, base_url, base_role):
    url = base_url.rstrip("/") + "/" + wf["url_path"].lstrip("/")
    sidebar = "".join(
        f'<div class="sidebar-item{" active" if item == wf["active_sidebar"] else ""}">{esc(item)}</div>'
        for item in wf["sidebar"]
    )
    tone = wf.get("status", {}).get("tone", "green")
    status = ""
    if wf.get("status"):
        status = f'<span class="status-badge badge-{tone}">{esc(wf["status"]["text"])}</span>'
    intro = f'<div style="font-size:11.5px; margin:8px 0; line-height:1.45;">{wf["intro_html"]}</div>' if wf.get("intro_html") else ""
    actions = "".join(
        f'<button class="app-btn btn-{"primary" if i == len(wf["actions"]) - 1 else "secondary"}">{esc(a)}</button>'
        for i, a in enumerate(wf["actions"])
    )
    return f"""
        <div class="wireframe-full-card">
          <div class="app-chrome">
            <div class="chrome-left">
              <div class="chrome-dots"><div class="chrome-dot"></div><div class="chrome-dot"></div><div class="chrome-dot"></div></div>
              <div class="chrome-url">{icon("lock", 11)} {esc(url)}</div>
            </div>
            <span class="chrome-role-badge">Role: {esc(wf.get("role_badge", base_role))}</span>
          </div>
          <div class="app-workspace">
            <div class="app-sidebar">{sidebar}</div>
            <div class="app-canvas">
              <div>
                <div class="app-section-title"><span>{esc(wf["section_title"])}</span>{status}</div>
                {intro}
                {table_html(wf["table"])}
              </div>
              <div class="app-action-bar">{actions}</div>
            </div>
          </div>
        </div>"""


def slide_html(slide, persona, deck):
    g = slide["graphic"]
    return f"""
    <div class="slide-canvas">
      <div class="slide-header">
        <div class="slide-header-left">
          <span class="slide-num-tag">Slide {esc(slide["num"])}</span>
          <span class="slide-main-title">{icon(slide.get("icon", "file"), 18, "var(--navy)")} {esc(slide["title"])}</span>
        </div>
        <span class="slide-stage-badge">{esc(slide["stage_badge"])}</span>
      </div>
      <div class="slide-content-grid">
        <div class="left-insights-col">
          {contrast_html("before", slide["as_is"])}
          {contrast_html("after", slide["to_be"])}
          <div class="topic-graphic-card">
            <div class="graphic-head">{icon(g.get("icon", "chart"), 14)} {esc(g["title"])}</div>
            <div class="graphic-body">
              <svg class="graphic-svg" viewBox="0 0 460 160" fill="none" xmlns="http://www.w3.org/2000/svg">
{g["svg"]}
              </svg>
            </div>
          </div>
        </div>
{wireframe_html(slide["wireframe"], deck["app"]["base_url"], persona["short_role"])}
      </div>
      <div class="slide-footer-bar">
        <label class="signoff-label">
          <input type="checkbox" class="signoff-box" onchange="updateAlignment()">
          <span>Slide {esc(slide["num"])} Alignment: {esc(slide["signoff_text"])}</span>
        </label>
        <span style="color:var(--text-light);">Owner: {esc(slide["owner"])}</span>
      </div>
    </div>"""


def panel_html(persona, index, deck):
    img = persona["image"]
    slides = "\n".join(slide_html(s, persona, deck) for s in persona["slides"])
    active = " active" if index == 0 else ""
    return f"""
  <div id="role-{esc(persona["id"])}" class="role-panel{active}">
    <div class="persona-hero">
      <div class="persona-img-wrap"><img src="{esc(img["url"])}" alt="{esc(img["alt"])}" class="persona-img"></div>
      <div class="persona-info">
        <div class="persona-role-title">{esc(persona["role_title"])}</div>
        <div class="persona-dept">{icon("pin", 14)} {esc(persona["location"])}</div>
        <div class="persona-mission">{esc(persona["mission"])}</div>
      </div>
    </div>
{slides}
  </div>"""


def tab_html(persona, index):
    active = " active" if index == 0 else ""
    return (
        f'    <button class="role-btn{active}" data-role="{esc(persona["id"])}" '
        f"onclick=\"showRole('{esc(persona['id'])}')\">"
        f'{icon(persona.get("tab_icon", "users"), 15)} {esc(persona["tab_label"])}</button>'
    )


def build(spec):
    deck = spec["deck"]
    total = sum(len(p["slides"]) for p in spec["personas"])
    css = (SKILL_DIR / "assets" / "deck.css").read_text(encoding="utf-8")
    shell = (SKILL_DIR / "assets" / "deck-shell.html").read_text(encoding="utf-8")
    values = {
        "{{CSS}}": css,
        "{{DECK_TITLE_TEXT}}": esc(deck["title"]),
        "{{DECK_TITLE}}": esc(deck["title"]),
        "{{DECK_KICKER}}": esc(deck["kicker"]),
        "{{ALIGNMENT_LABEL}}": esc(deck.get("alignment_label", "Stakeholder Alignment")),
        "{{TOTAL_SLIDES}}": str(total),
        "{{ROLE_TABS}}": "\n".join(tab_html(p, i) for i, p in enumerate(spec["personas"])),
        "{{ROLE_PANELS}}": "\n".join(panel_html(p, i, deck) for i, p in enumerate(spec["personas"])),
    }
    out = shell
    for key, val in values.items():
        out = out.replace(key, val)
    return out


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = build(spec)
    Path(sys.argv[2]).write_text(out, encoding="utf-8")
    print(f"Wrote {sys.argv[2]} ({len(out):,} bytes)")


if __name__ == "__main__":
    main()
