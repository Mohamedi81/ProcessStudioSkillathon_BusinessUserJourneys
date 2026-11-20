#!/usr/bin/env python3
"""Render a deck spec (JSON) into an editable PowerPoint deck: one slide per spec slide.

Usage: python3 build_pptx_deck.py --input deck-spec.json --output deck.pptx

Exit code 0: deck written. Exit code 1: spec problems are printed to stderr.
Uses python-pptx (installed in the BYOS sandbox) plus the standard library. No network access:
role photos are not embedded, a coloured role badge is shown instead.
"""
import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

import validate_deck

DEFAULT_OUTPUT_NAME = "deck.pptx"

NAVY, NAVY_LIGHT, NAVY_BORDER = "1E3A8A", "EFF6FF", "BFDBFE"
FOREST, FOREST_LIGHT, FOREST_BORDER = "065F46", "ECFDF5", "A7F3D0"
CRIMSON, CRIMSON_LIGHT, CRIMSON_BORDER = "991B1B", "FEF2F2", "FECACA"
AMBER, AMBER_LIGHT = "92400E", "FFFBEB"
TEXT, MUTED, BORDER, SURFACE, DARK = "0F172A", "64748B", "CBD5E1", "F8FAFC", "1E293B"
FONT = "Calibri"
TONE_TEXT = {"green": FOREST, "amber": AMBER, "red": CRIMSON}
BADGE = {"green": (FOREST_LIGHT, FOREST), "amber": (AMBER_LIGHT, AMBER), "navy": (NAVY_LIGHT, NAVY)}


def rgb(hex_color):
    return RGBColor.from_string(hex_color.lstrip("#").upper())


def box(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, line_w=0.75, radius=None):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.shadow.inherit = False
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(fill)
    else:
        shp.fill.background()
    if line:
        shp.line.color.rgb = rgb(line)
        shp.line.width = Pt(line_w)
    else:
        shp.line.fill.background()
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = radius
    return shp


def text(slide, x, y, w, h, s, size, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, wrap=True, font=FONT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = str(s)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = font
    run.font.color.rgb = rgb(color)
    return tb


def body_size(s):
    n = len(s)
    return 12 if n <= 170 else 10.5 if n <= 260 else 9.5


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s or "")).strip()


# ---------- SVG infographic -> native shapes ----------

def num(el, name, default=0.0):
    raw = el.get(name)
    if raw is None:
        return default
    m = re.match(r"-?\d+(\.\d+)?", raw.strip())
    return float(m.group(0)) if m else default


def color_of(raw, default=None):
    if raw is None:
        return default
    raw = raw.strip().lower()
    if raw in ("none", "transparent"):
        return None
    if raw == "white":
        return "FFFFFF"
    if raw == "black":
        return "000000"
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", raw)
    if not m:
        return default
    h = m.group(1)
    return "".join(c * 2 for c in h).upper() if len(h) == 3 else h.upper()


def draw_svg(slide, inner, x0, y0, scale):
    """Draw the supported SVG elements (rect, circle, ellipse, line, text) as shapes."""
    try:
        root = ET.fromstring("<svg>" + re.sub(r'\sxmlns(:\w+)?="[^"]*"', "", inner) + "</svg>")
    except ET.ParseError:
        text(slide, x0, y0 + 0.6, 460 * scale, 0.5, "Infographic not rendered in PowerPoint (see HTML deck).", 10, MUTED)
        return
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        stroke = color_of(el.get("stroke"))
        sw = max(num(el, "stroke-width", 1.0) * scale * 72, 0.5)
        if tag in ("rect", "circle", "ellipse"):
            if tag == "rect":
                x, y, w, h = num(el, "x"), num(el, "y"), num(el, "width"), num(el, "height")
            elif tag == "circle":
                r = num(el, "r")
                x, y, w, h = num(el, "cx") - r, num(el, "cy") - r, 2 * r, 2 * r
            else:
                rx, ry = num(el, "rx"), num(el, "ry")
                x, y, w, h = num(el, "cx") - rx, num(el, "cy") - ry, 2 * rx, 2 * ry
            if w <= 0 or h <= 0:
                continue
            rx = num(el, "rx")
            kind = MSO_SHAPE.OVAL if tag != "rect" else (MSO_SHAPE.ROUNDED_RECTANGLE if rx > 0 else MSO_SHAPE.RECTANGLE)
            radius = min(rx / min(w, h), 0.5) if rx > 0 else None
            fill = color_of(el.get("fill"), "000000")
            shp = box(slide, x0 + x * scale, y0 + y * scale, w * scale, h * scale, fill=fill,
                      line=stroke, shape=kind, line_w=sw, radius=radius)
            if stroke and el.get("stroke-dasharray"):
                shp.line.dash_style = MSO_LINE.DASH
        elif tag == "line" and stroke:
            conn = slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                Inches(x0 + num(el, "x1") * scale), Inches(y0 + num(el, "y1") * scale),
                Inches(x0 + num(el, "x2") * scale), Inches(y0 + num(el, "y2") * scale))
            conn.line.color.rgb = rgb(stroke)
            conn.line.width = Pt(sw)
            if el.get("stroke-dasharray"):
                conn.line.dash_style = MSO_LINE.DASH
        elif tag == "text":
            s = " ".join("".join(el.itertext()).split())
            if not s:
                continue
            fs = num(el, "font-size", 10.0)
            bold = (el.get("font-weight") or "").lower() in ("bold", "600", "700", "800", "900")
            width = max(len(s) * fs * 0.6, fs) * scale
            anchor = (el.get("text-anchor") or "start").lower()
            left = num(el, "x") * scale
            align = PP_ALIGN.LEFT
            if anchor == "middle":
                left, align = left - width / 2, PP_ALIGN.CENTER
            elif anchor == "end":
                left, align = left - width, PP_ALIGN.RIGHT
            top = (num(el, "y") - fs * 0.85) * scale
            text(slide, x0 + left, y0 + top, width, fs * 1.3 * scale, s, max(fs * scale * 72, 6),
                 color_of(el.get("fill"), "000000"), bold, align, wrap=False)


# ---------- slide pieces ----------

def contrast(slide, x, y, w, h, kind, data):
    fill, border, ink = (CRIMSON_LIGHT, CRIMSON_BORDER, CRIMSON) if kind == "before" else (FOREST_LIGHT, FOREST_BORDER, FOREST)
    box(slide, x, y, w, h, fill=fill, line=border)
    text(slide, x + 0.15, y + 0.1, w * 0.4, 0.25, data["head_left"].upper(), 10, ink, True)
    text(slide, x + w * 0.4, y + 0.1, w * 0.6 - 0.15, 0.25, data["head_right"].upper(), 10, ink, True, PP_ALIGN.RIGHT)
    text(slide, x + 0.15, y + 0.4, w - 0.3, h - 0.5, data["body"], body_size(data["body"]))


def graphic_card(slide, x, y, w, h, g):
    box(slide, x, y, w, h, fill="FFFFFF", line=BORDER)
    text(slide, x + 0.15, y + 0.08, w - 0.3, 0.25, g["title"].upper(), 10, NAVY, True)
    scale = (w - 0.4) / 460
    draw_svg(slide, g["svg"], x + 0.2, y + 0.4, min(scale, (h - 0.5) / 160))


def wireframe(slide, x, y, w, h, wf, base_url, role):
    url = base_url.rstrip("/") + "/" + wf["url_path"].lstrip("/")
    box(slide, x, y, w, h, fill="FFFFFF", line=BORDER)
    box(slide, x, y, w, 0.38, fill=DARK)
    text(slide, x + 0.15, y + 0.09, w * 0.65, 0.22, url, 9, "FFFFFF", font="Consolas")
    text(slide, x + w * 0.65, y + 0.09, w * 0.35 - 0.15, 0.22, "Role: " + wf.get("role_badge", role), 9,
         "E2E8F0", False, PP_ALIGN.RIGHT)
    side_w, top = 1.45, y + 0.38
    box(slide, x, top, side_w, h - 0.38, fill=SURFACE, line=None)
    for i, item in enumerate(wf["sidebar"]):
        iy = top + 0.12 + i * 0.4
        active = item == wf["active_sidebar"]
        if active:
            box(slide, x + 0.08, iy, side_w - 0.16, 0.32, fill=NAVY_LIGHT, line=NAVY_BORDER)
        text(slide, x + 0.16, iy, side_w - 0.3, 0.32, item, 9.5, NAVY if active else MUTED, active,
             anchor=MSO_ANCHOR.MIDDLE)
    cx, cw = x + side_w + 0.2, w - side_w - 0.4
    status = wf.get("status")
    text(slide, cx, top + 0.15, cw * (0.62 if status else 1), 0.3, wf["section_title"], 13, TEXT, True)
    if status:
        fill, ink = BADGE.get(status.get("tone", "green"), BADGE["green"])
        bw = min(max(len(status["text"]) * 0.085 + 0.3, 0.9), cw * 0.4)
        box(slide, cx + cw - bw, top + 0.15, bw, 0.28, fill=fill, line=ink, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3)
        text(slide, cx + cw - bw, top + 0.15, bw, 0.28, status["text"].upper(), 8, ink, True,
             PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    ty = top + 0.6
    intro = plain(wf.get("intro_html"))
    if intro:
        text(slide, cx, ty, cw, 0.5, intro, 10, TEXT)
        ty += 0.55
    table(slide, cx, ty, cw, wf["table"])
    n = len(wf["actions"])
    bw, by = 1.55, y + h - 0.55
    for i, label in enumerate(reversed(wf["actions"])):
        bx = cx + cw - (i + 1) * bw - i * 0.12
        primary = i == 0
        box(slide, bx, by, bw, 0.34, fill=NAVY if primary else "FFFFFF", line=NAVY if primary else BORDER,
            shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.2)
        text(slide, bx, by, bw, 0.34, label, 9.5, "FFFFFF" if primary else TEXT, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    return n


def table(slide, x, y, w, t):
    headers = t["headers"]
    ncols = len(headers)
    rows = []
    for r in t["rows"]:
        cells = r["cells"] if isinstance(r, dict) else r
        rows.append((list(cells) + [""] * ncols)[:ncols])
    gf = slide.shapes.add_table(len(rows) + 1, ncols, Inches(x), Inches(y), Inches(w), Inches(0.3 * (len(rows) + 1)))
    tbl = gf.table
    for c in range(ncols):
        tbl.columns[c].width = Inches(w / ncols)
    for r in range(len(rows) + 1):
        tbl.rows[r].height = Inches(0.3)
    for c, head in enumerate(headers):
        fill_cell(tbl.cell(0, c), head, "F1F5F9", MUTED, True, 9)
    for r, cells in enumerate(rows, start=1):
        for c, value in enumerate(cells):
            if isinstance(value, dict):
                fill_cell(tbl.cell(r, c), value["text"], "FFFFFF", TONE_TEXT.get(value.get("tone"), TEXT), True, 10)
            else:
                fill_cell(tbl.cell(r, c), value, "FFFFFF", TEXT, False, 10)


def fill_cell(cell, value, fill, color, bold, size):
    cell.fill.solid()
    cell.fill.fore_color.rgb = rgb(fill)
    cell.margin_left = cell.margin_right = Inches(0.08)
    cell.margin_top = cell.margin_bottom = Inches(0.03)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = cell.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = str(value)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = FONT
    run.font.color.rgb = rgb(color)


def title_slide(prs, deck, spec):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    box(s, 0, 0, 13.333, 7.5, fill="0B1120")
    box(s, 0.8, 2.4, 0.08, 1.9, fill="3B82F6")
    text(s, 1.1, 2.3, 11, 0.4, deck["kicker"].upper(), 14, "34D399", True)
    text(s, 1.1, 2.8, 11, 1.2, deck["title"], 40, "FFFFFF", True)
    slides = sum(len(p["slides"]) for p in spec["personas"])
    roles = ", ".join(p["tab_label"] for p in spec["personas"])
    text(s, 1.1, 4.1, 11, 0.8, f"{len(spec['personas'])} roles, {slides} slides: {roles}", 14, "94A3B8")
    s.notes_slide.notes_text_frame.text = deck["title"]


def content_slide(prs, deck, persona, sl):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    box(s, 0.5, 0.32, 1.15, 0.34, fill=NAVY_LIGHT, line=NAVY_BORDER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.2)
    text(s, 0.5, 0.32, 1.15, 0.34, "SLIDE " + str(sl["num"]), 10, NAVY, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    text(s, 1.85, 0.28, 8.6, 0.45, sl["title"], 22, NAVY, True, anchor=MSO_ANCHOR.MIDDLE)
    box(s, 10.5, 0.34, 2.33, 0.32, fill="FFFFFF", line=BORDER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.2)
    text(s, 10.5, 0.34, 2.33, 0.32, sl["stage_badge"], 10, MUTED, False, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    text(s, 1.85, 0.78, 8.6, 0.28, persona["role_title"] + "  |  " + persona["location"], 11, MUTED)
    line = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.5), Inches(1.2), Inches(12.83), Inches(1.2))
    line.line.color.rgb = rgb("E2E8F0")
    contrast(s, 0.5, 1.4, 6.2, 1.25, "before", sl["as_is"])
    contrast(s, 0.5, 2.75, 6.2, 1.25, "after", sl["to_be"])
    graphic_card(s, 0.5, 4.1, 6.2, 2.5, sl["graphic"])
    wireframe(s, 6.95, 1.4, 5.88, 5.2, sl["wireframe"], deck["app"]["base_url"], persona["short_role"])
    box(s, 0.5, 6.88, 0.2, 0.2, fill="FFFFFF", line=MUTED, line_w=1.25)
    text(s, 0.85, 6.82, 9.6, 0.45, "Slide " + str(sl["num"]) + " Alignment: " + sl["signoff_text"], 11, TEXT, True)
    text(s, 10.6, 6.84, 2.23, 0.3, "Owner: " + sl["owner"], 10, MUTED, False, PP_ALIGN.RIGHT)
    s.notes_slide.notes_text_frame.text = (
        persona["role_title"] + ": " + persona["mission"] + "\n\nAs-Is: " + sl["as_is"]["body"] +
        "\n\nTo-Be: " + sl["to_be"]["body"] + "\n\nSign-off: " + sl["signoff_text"])


def build(spec):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    title_slide(prs, spec["deck"], spec)
    for persona in spec["personas"]:
        for sl in persona["slides"]:
            content_slide(prs, spec["deck"], persona, sl)
    return prs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    try:
        spec = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL: input is not readable JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate_deck.validate_spec(spec, [])
    if errors:
        print(f"FAIL: {len(errors)} spec issue(s)", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1

    prs = build(spec)
    prs.save(args.output)
    slides = sum(len(p["slides"]) for p in spec["personas"])
    print(f"PASS: {len(spec['personas'])} personas, {slides} content slides plus title, wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
