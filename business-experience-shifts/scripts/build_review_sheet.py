#!/usr/bin/env python3
"""Render a deck spec (JSON) into an Excel workshop review sheet: one row per use case.

Usage: python3 build_review_sheet.py --input deck-spec.json --output review-sheet.xlsx

Review sheet columns:
  ID | Role | Use case | Stage | Source ref | As-Is | To-Be | Owner | Decision | Comments (reason if not approved)
Decision is a dropdown: Approved as-is, Approved with comments, Rejected.
Source ref names the blueprint or analysis item the use case came from (slide field `source_ref`).
The Summary sheet carries the deck title and the source document name and version.
The returned file is read back by header name (see the apply-workshop-feedback skill), so do not
rename the ID, Decision or Comments headers.
Exit code 0: sheet written. Exit code 1: spec problems are printed to stderr.
Uses openpyxl (installed in the BYOS sandbox) plus the standard library.
"""
import argparse
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

import validate_deck

DEFAULT_OUTPUT_NAME = "review-sheet.xlsx"

DECISIONS = ["Approved as-is", "Approved with comments", "Rejected"]
HEADERS = ["ID", "Role", "Use case", "Stage", "Source ref", "As-Is", "To-Be", "Owner",
           "Decision", "Comments (reason if not approved)"]
WIDTHS = [8, 24, 38, 24, 18, 48, 48, 22, 26, 50]
DECISION_COL = get_column_letter(HEADERS.index("Decision") + 1)
COMMENT_COL = get_column_letter(len(HEADERS))

NAVY = "1E3A8A"
THIN = Side(style="thin", color="CBD5E1")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def fill(hex_color):
    return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")


def build(spec):
    wb = Workbook()
    ws = wb.active
    ws.title = "Review"

    for col, (head, width) in enumerate(zip(HEADERS, WIDTHS), start=1):
        c = ws.cell(row=1, column=col, value=head)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = fill(NAVY)
        c.alignment = Alignment(vertical="center", wrap_text=True)
        c.border = BORDER
        ws.column_dimensions[c.column_letter].width = width
    ws.row_dimensions[1].height = 30

    row = 1
    for persona in spec["personas"]:
        for sl in persona["slides"]:
            row += 1
            values = [
                str(sl["num"]), persona["role_title"], sl["title"], sl["stage_badge"],
                sl.get("source_ref") or None,
                f'{sl["as_is"]["head_right"]}. {sl["as_is"]["body"]}',
                f'{sl["to_be"]["head_right"]}. {sl["to_be"]["body"]}',
                sl["owner"], None, None,
            ]
            for col, value in enumerate(values, start=1):
                c = ws.cell(row=row, column=col, value=value)
                c.alignment = Alignment(vertical="top", wrap_text=True)
                c.border = BORDER
            ws.cell(row=row, column=1).number_format = "@"
            for letter in (DECISION_COL, COMMENT_COL):
                ws[f"{letter}{row}"].fill = fill("FFFBEB")
            ws.row_dimensions[row].height = 78

    last = row
    dv = DataValidation(type="list", formula1='"' + ",".join(DECISIONS) + '"', allow_blank=True,
                        showErrorMessage=True, errorTitle="Decision",
                        error="Pick one of: " + ", ".join(DECISIONS))
    dv.promptTitle, dv.prompt, dv.showInputMessage = "Decision", "Pick a decision from the list", True
    ws.add_data_validation(dv)
    rng = f"{DECISION_COL}2:{DECISION_COL}{last}"
    dv.add(rng)

    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'{DECISION_COL}2="{DECISIONS[0]}"'], fill=fill("D1FAE5")))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'{DECISION_COL}2="{DECISIONS[1]}"'], fill=fill("FEF3C7")))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'{DECISION_COL}2="{DECISIONS[2]}"'], fill=fill("FECACA")))
    # A reason is expected when the decision is not a plain approval.
    ws.conditional_formatting.add(
        f"{COMMENT_COL}2:{COMMENT_COL}{last}",
        FormulaRule(formula=[f'AND(OR({DECISION_COL}2="{DECISIONS[1]}",{DECISION_COL}2="{DECISIONS[2]}"),{COMMENT_COL}2="")'],
                    fill=fill("FCA5A5")))

    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{COMMENT_COL}{last}"

    deck = spec["deck"]
    sm = wb.create_sheet("Summary")
    sm.column_dimensions["A"].width = 30
    sm.column_dimensions["B"].width = 44
    sm["A1"], sm["B1"] = "Deck", deck["title"]
    sm["A2"], sm["B2"] = "Source document", deck.get("source_name") or None
    sm["A3"], sm["B3"] = "Source version", deck.get("source_version") or None
    sm["A5"], sm["B5"] = "Use cases", f"=COUNTA(Review!A2:A{last})"
    for i, label in enumerate(DECISIONS, start=6):
        sm[f"A{i}"], sm[f"B{i}"] = label, f'=COUNTIF(Review!{rng},"{label}")'
    sm["A9"], sm["B9"] = "Not yet reviewed", "=B5-SUM(B6:B8)"
    sm["A11"] = "Fill in Decision on the Review sheet. Give a reason for every decision that is not Approved as-is. Then return the file."
    for r in (1, 2, 3, 5, 9):
        sm[f"A{r}"].font = Font(bold=True)
    return wb


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

    build(spec).save(args.output)
    rows = sum(len(p["slides"]) for p in spec["personas"])
    print(f"PASS: {rows} use cases, wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
