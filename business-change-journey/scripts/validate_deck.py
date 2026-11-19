#!/usr/bin/env python3
"""Validate a deck spec and (optionally) the built HTML for portability.

Usage:
  python3 validate_deck.py <deck-spec.json> [--html built.html] [--forbid terms.txt]

Checks (exit code 1 on any failure):
  1. Schema: every required field exists on deck / persona / slide.
  2. Structure: unique persona ids, unique slide numbers, >=1 slide per persona,
     slide numbers prefixed by persona index (e.g. persona 2 -> 2.1, 2.2).
  3. Style: no emoji / pictographs anywhere in the spec.
  4. Leakage: none of the --forbid terms (one per line, case-insensitive) appear
     in the spec or built HTML. Use the previous domain's vocabulary here.
  5. HTML: sign-off boxes == slides, tabs == panels, no unreplaced {{TOKENS}}.
"""
import argparse
import json
import re
import sys
from pathlib import Path

DECK_REQ = ["title", "kicker", "app"]
APP_REQ = ["base_url"]
PERSONA_REQ = ["id", "short_role", "tab_label", "role_title", "location", "mission", "image", "slides"]
IMAGE_REQ = ["url", "alt"]
SLIDE_REQ = ["num", "title", "stage_badge", "as_is", "to_be", "graphic", "wireframe", "signoff_text", "owner"]
BOX_REQ = ["head_left", "head_right", "body"]
GRAPHIC_REQ = ["title", "svg"]
WF_REQ = ["url_path", "sidebar", "active_sidebar", "section_title", "table", "actions"]

EMOJI = "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U00002B00-\U00002BFF\U0000231A-\U000023FF]"


def walk_text(node):
    if isinstance(node, dict):
        for v in node.values():
            yield from walk_text(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_text(v)
    elif isinstance(node, str):
        yield node


def need(obj, keys, where, errors):
    for k in keys:
        if k not in obj or obj[k] in ("", None, []):
            errors.append(f"{where}: missing '{k}'")


def validate_spec(spec, forbid):
    errors = []
    deck = spec.get("deck", {})
    need(deck, DECK_REQ, "deck", errors)
    need(deck.get("app", {}), APP_REQ, "deck.app", errors)

    personas = spec.get("personas", [])
    if not personas:
        errors.append("personas: at least one persona required")
    ids, nums = set(), set()
    for pi, p in enumerate(personas, start=1):
        pw = f"personas[{pi}]"
        need(p, PERSONA_REQ, pw, errors)
        need(p.get("image", {}), IMAGE_REQ, pw + ".image", errors)
        if p.get("id") in ids:
            errors.append(f"{pw}: duplicate id '{p.get('id')}'")
        ids.add(p.get("id"))
        for si, s in enumerate(p.get("slides", []), start=1):
            sw = f"{pw}.slides[{si}]"
            need(s, SLIDE_REQ, sw, errors)
            need(s.get("as_is", {}), BOX_REQ, sw + ".as_is", errors)
            need(s.get("to_be", {}), BOX_REQ, sw + ".to_be", errors)
            need(s.get("graphic", {}), GRAPHIC_REQ, sw + ".graphic", errors)
            need(s.get("wireframe", {}), WF_REQ, sw + ".wireframe", errors)
            num = str(s.get("num"))
            if num in nums:
                errors.append(f"{sw}: duplicate slide num {num}")
            nums.add(num)
            if not num.startswith(f"{pi}."):
                errors.append(f"{sw}: num '{num}' should start with '{pi}.'")
            svg = s.get("graphic", {}).get("svg", "")
            if "<script" in svg.lower() or "onload" in svg.lower():
                errors.append(f"{sw}.graphic.svg: scripts/event handlers not allowed")

    blob = "\n".join(walk_text(spec))
    m = re.search(EMOJI, blob)
    if m:
        errors.append(f"style: emoji/pictograph found ({m.group(0)!r}); design rules forbid emojis")
    for term in forbid:
        if term.lower() in blob.lower():
            errors.append(f"leakage: forbidden term '{term}' found in spec")
    return errors


def validate_html(spec, html, forbid):
    errors = []
    total = sum(len(p["slides"]) for p in spec["personas"])
    boxes = html.count('class="signoff-box"')
    if boxes != total:
        errors.append(f"html: signoff boxes != slides ({boxes} vs {total})")
    if html.count('class="role-btn') != len(spec["personas"]) or html.count('class="role-panel') != len(spec["personas"]):
        errors.append("html: role tabs/panels count differs from persona count")
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftovers:
        errors.append(f"html: unreplaced tokens {sorted(set(leftovers))}")
    for term in forbid:
        if term.lower() in html.lower():
            errors.append(f"leakage: forbidden term '{term}' found in built HTML")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--html")
    ap.add_argument("--forbid")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    forbid = []
    if args.forbid:
        forbid = [l.strip() for l in Path(args.forbid).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]

    errors = validate_spec(spec, forbid)
    if args.html and not errors:
        errors += validate_html(spec, Path(args.html).read_text(encoding="utf-8"), forbid)

    if errors:
        print(f"FAIL ({len(errors)} issue(s))")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    slides = sum(len(p["slides"]) for p in spec["personas"])
    print(f"PASS: {len(spec['personas'])} personas, {slides} slides, {len(forbid)} forbidden terms checked")


if __name__ == "__main__":
    main()
