#!/usr/bin/env python3
"""Write workshop decisions into a review sheet (xlsx), rebuilt from one JSON file.

Usage: python3 fill_review_sheet.py --input decisions.json --output review-sheet-filled.xlsx

decisions.json has the shape of feedback.json from read_review_sheet.py:
  {"source": {"Deck": "...", "Source document": "...", "Source version": "..."},
   "items": [{"id", "role", "use_case", "stage", "source_ref", "as_is", "to_be", "owner",
              "decision", "comment", "evidence"}, ...]}
`decision` is "Approved as-is", "Approved with comments", "Rejected" or "Pending".
`evidence` is the quote from the transcript, or "stated by user", that supports the decision.

Checks (exit 1 with every problem on stderr):
  - decision must be one of the four values
  - every decision other than Pending needs evidence
Warnings (still writes the sheet): Rejected or Approved with comments without a reason.
The output keeps the same headers as the original sheet, so read_review_sheet.py reads it back.
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

DEFAULT_OUTPUT_NAME = "review-sheet-filled.xlsx"

DECISIONS = ["Approved as-is", "Approved with comments", "Rejected"]
HEADERS = ["ID", "Role", "Use case", "Stage", "Source ref", "As-Is", "To-Be", "Owner",
           "Decision", "Comments (reason if not approved)", "Evidence"]
KEYS = ["id", "role", "use_case", "stage", "source_ref", "as_is", "to_be", "owner",
        "decision", "comment", "evidence"]
WIDTHS = [8, 24, 38, 24, 18, 48, 48, 22, 26, 50, 50]
DECISION_COL = get_column_letter(HEADERS.index("Decision") + 1)
COMMENT_COL = get_column_letter(HEADERS.index("Comments (reason if not approved)") + 1)
LAST_COL = get_column_letter(len(HEADERS))

THIN = Side(style="thin", color="CBD5E1")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def fill(hex_color):
    return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")


def check(data):
    errors, warnings = [], []
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return ["'items' must be a non-empty list"], warnings
    seen = set()
    for it in items:
        uid = str(it.get("id", "")).strip()
        if not uid:
            errors.append("an item has no 'id'")
            continue
        if uid in seen:
            errors.append(f"{uid}: duplicate id")
        seen.add(uid)
        decision = it.get("decision") or "Pending"
        if decision != "Pending" and decision not in DECISIONS:
            errors.append(f"{uid}: decision '{decision}' must be one of {DECISIONS} or 'Pending'")
            continue
        if decision != "Pending" and not str(it.get("evidence") or "").strip():
            errors.append(f"{uid}: '{decision}' needs evidence (a quote, or 'stated by user')")
        if decision in DECISIONS[1:] and not str(it.get("comment") or "").strip():
            warnings.append(f"{uid}: '{decision}' has no reason")
    return errors, warnings


def build(data):
    items = data["items"]
    wb = Workbook()
    ws = wb.active
    ws.title = "Review"
    for col, (head, width) in enumerate(zip(HEADERS, WIDTHS), start=1):
        c = ws.cell(row=1, column=col, value=head)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = fill("1E3A8A")
        c.alignment = Alignment(vertical="center", wrap_text=True)
        c.border = BORDER
        ws.column_dimensions[c.column_letter].width = width
    ws.row_dimensions[1].height = 30

    for r, it in enumerate(items, start=2):
        for col, key in enumerate(KEYS, start=1):
            value = it.get(key)
            if key == "decision":
                value = None if value in (None, "", "Pending") else value
            c = ws.cell(row=r, column=col, value=(str(value) if value not in (None, "") else None))
            c.alignment = Alignment(vertical="top", wrap_text=True)
            c.border = BORDER
        ws.cell(row=r, column=1).number_format = "@"
        for letter in (DECISION_COL, COMMENT_COL):
            ws[f"{letter}{r}"].fill = fill("FFFBEB")
        ws.row_dimensions[r].height = 78

    last = len(items) + 1
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
    ws.conditional_formatting.add(
        f"{COMMENT_COL}2:{COMMENT_COL}{last}",
        FormulaRule(formula=[f'AND(OR({DECISION_COL}2="{DECISIONS[1]}",{DECISION_COL}2="{DECISIONS[2]}"),{COMMENT_COL}2="")'],
                    fill=fill("FCA5A5")))
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{LAST_COL}{last}"

    src = data.get("source") or {}
    sm = wb.create_sheet("Summary")
    sm.column_dimensions["A"].width = 30
    sm.column_dimensions["B"].width = 44
    sm["A1"], sm["B1"] = "Deck", src.get("Deck") or None
    sm["A2"], sm["B2"] = "Source document", src.get("Source document") or None
    sm["A3"], sm["B3"] = "Source version", src.get("Source version") or None
    sm["A5"], sm["B5"] = "Use cases", f"=COUNTA(Review!A2:A{last})"
    for i, label in enumerate(DECISIONS, start=6):
        sm[f"A{i}"], sm[f"B{i}"] = label, f'=COUNTIF(Review!{rng},"{label}")'
    sm["A9"], sm["B9"] = "Not yet reviewed", "=B5-SUM(B6:B8)"
    sm["A11"] = "Decisions were filled in from workshop notes. Check them against the Evidence column, then return the file."
    for r in (1, 2, 3, 5, 9):
        sm[f"A{r}"].font = Font(bold=True)
    return wb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL: input is not readable JSON: {exc}", file=sys.stderr)
        return 1
    errors, warnings = check(data)
    if errors:
        print(f"FAIL: {len(errors)} issue(s)", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1

    build(data).save(args.output)
    items = data["items"]
    counts = {d: sum(1 for i in items if i.get("decision") == d) for d in DECISIONS}
    pending = len(items) - sum(counts.values())
    print(f"PASS: wrote {args.output}: {counts[DECISIONS[0]]} approved, {counts[DECISIONS[1]]} with comments, "
          f"{counts[DECISIONS[2]]} rejected, {pending} pending")
    for w in warnings:
        print(f" - warning: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
