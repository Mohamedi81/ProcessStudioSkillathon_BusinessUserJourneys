#!/usr/bin/env python3
"""Render a deck spec (JSON) into an Excel workshop review sheet: one row per use case.

Usage: python3 build_review_sheet.py --input deck-spec.json --output review-sheet.xlsx

Columns: ID | Role | Use case | Stage | As-Is | To-Be | Owner | Decision | Comments
Decision is a dropdown: Approved as-is, Approved with comments, Rejected.
The header row and the ID column are stable so the returned file can be read back by machine.
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
from openpyxl.worksheet.datavalidation import DataValidation

import validate_deck

DEFAULT_OUTPUT_NAME = "review-sheet.xlsx"

DECISIONS = ["Approved as-is", "Approved with comments", "Rejected"]
HEADERS = ["ID", "Role", "Use case", "Stage", "As-Is", "To-Be", "Owner", "Decision", "Comments"]
WIDTHS = [8, 24, 38, 24, 48, 48, 22, 26, 50]
DECISION_COL, COMMENT_COL = "H", "I"

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
    ws.row_dimensions[1].height = 24

    row = 1
    for persona in spec["personas"]:
        for sl in persona["slides"]:
            row += 1
            values = [
                str(sl["num"]), persona["role_title"], sl["title"], sl["stage_badge"],
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
    dv.add(f"{DECISION_COL}2:{DECISION_COL}{last}")

    rng = f"{DECISION_COL}2:{DECISION_COL}{last}"
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'{DECISION_COL}2="{DECISIONS[0]}"'], fill=fill("D1FAE5")))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'{DECISION_COL}2="{DECISIONS[1]}"'], fill=fill("FEF3C7")))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'{DECISION_COL}2="{DECISIONS[2]}"'], fill=fill("FECACA")))
    # Comments are expected when the decision is not a plain approval.
    ws.conditional_formatting.add(
        f"{COMMENT_COL}2:{COMMENT_COL}{last}",
        FormulaRule(formula=[f'AND(OR({DECISION_COL}2="{DECISIONS[1]}",{DECISION_COL}2="{DECISIONS[2]}"),{COMMENT_COL}2="")'],
                    fill=fill("FCA5A5")))

    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{COMMENT_COL}{last}"

    sm = wb.create_sheet("Summary")
    sm.column_dimensions["A"].width = 30
    sm.column_dimensions["B"].width = 14
    sm["A1"], sm["B1"] = "Deck", spec["deck"]["title"]
    sm["A3"], sm["B3"] = "Use cases", f"=COUNTA(Review!A2:A{last})"
    for i, label in enumerate(DECISIONS, start=4):
        sm[f"A{i}"], sm[f"B{i}"] = label, f'=COUNTIF(Review!{DECISION_COL}2:{DECISION_COL}{last},"{label}")'
    sm["A7"], sm["B7"] = "Not yet reviewed", "=B3-SUM(B4:B6)"
    sm["A9"] = "Fill in the Decision column on the Review sheet, then return the file."
    for r in (1, 3, 7):
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
