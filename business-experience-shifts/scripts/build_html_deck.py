#!/usr/bin/env python3
"""Validate a deck spec (JSON) and render it into a single-file HTML experience-shifts deck.

Usage: python3 build_html_deck.py --input deck-spec.json --output experience-shifts-deck.html

Exit code 0: deck written. Exit code 1: spec problems are printed to stderr, one per line
(fix the spec and run again). Standard library only; reads ../assets/ from the skill bundle.
"""
import argparse
import json
import sys
from pathlib import Path

import build_deck
import validate_deck

DEFAULT_OUTPUT_NAME = "experience-shifts-deck.html"


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

    html_text = build_deck.build(spec)
    errors = validate_deck.validate_html(spec, html_text, [])
    if errors:
        print(f"FAIL: {len(errors)} html issue(s)", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1

    Path(args.output).write_text(html_text, encoding="utf-8")
    slides = sum(len(p["slides"]) for p in spec["personas"])
    print(f"PASS: {len(spec['personas'])} personas, {slides} slides, wrote {args.output} ({len(html_text):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
