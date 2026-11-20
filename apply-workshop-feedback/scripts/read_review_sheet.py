#!/usr/bin/env python3
"""Read a returned workshop review sheet (xlsx) into structured feedback (JSON).

Usage: python3 read_review_sheet.py --input review-sheet.xlsx --output feedback.json

Reads the Review sheet by header name (ID, Decision, Comments...), so reordered or extra columns are fine.
Writes feedback.json: counts per decision, one item per use case, and a `problems` list.
Exit code 0: feedback written, even if some use cases are still pending (see `problems`).
Exit code 1: the file is unreadable or is not a review sheet.
Uses openpyxl (installed in the BYOS sandbox) plus the standard library.
"""
import argparse
import json
import sys
from pathlib import Path

from openpyxl import load_workbook

DEFAULT_OUTPUT_NAME = "feedback.json"

APPROVED, COMMENTS, REJECTED = "Approved as-is", "Approved with comments", "Rejected"
DECISIONS = [APPROVED, COMMENTS, REJECTED]
REASON_HEADER_PREFIX = "Comments"


def cell_text(value):
    return "" if value is None else str(value).strip()


def normalise_decision(raw):
    """Map a typed value onto a known decision, tolerating case and spacing. Unknown values return None."""
    key = " ".join(raw.lower().replace("-", " ").split())
    for d in DECISIONS:
        if key == " ".join(d.lower().replace("-", " ").split()):
            return d
    return None


def read(path):
    wb = load_workbook(path, data_only=True)
    if "Review" not in wb.sheetnames:
        raise ValueError("no 'Review' sheet found: this is not a review sheet from this skill")
    ws = wb["Review"]
    headers = {cell_text(c.value): i for i, c in enumerate(ws[1])}
    for needed in ("ID", "Decision"):
        if needed not in headers:
            raise ValueError(f"header '{needed}' not found in the Review sheet")
    reason_col = next((i for h, i in headers.items() if h.startswith(REASON_HEADER_PREFIX)), None)

    def col(row, name):
        i = headers.get(name)
        return cell_text(row[i].value) if i is not None and i < len(row) else ""

    summary = {}
    if "Summary" in wb.sheetnames:
        sm = wb["Summary"]
        for r in range(1, 4):
            label, value = cell_text(sm.cell(r, 1).value), cell_text(sm.cell(r, 2).value)
            if label:
                summary[label] = value

    items, problems = [], []
    for row in ws.iter_rows(min_row=2):
        uid = cell_text(row[headers["ID"]].value)
        if not uid:
            continue
        raw = cell_text(row[headers["Decision"]].value)
        decision = normalise_decision(raw) if raw else None
        comment = cell_text(row[reason_col].value) if reason_col is not None else ""
        item = {
            "id": uid, "role": col(row, "Role"), "use_case": col(row, "Use case"),
            "stage": col(row, "Stage"), "source_ref": col(row, "Source ref"), "owner": col(row, "Owner"),
            "as_is": col(row, "As-Is"), "to_be": col(row, "To-Be"),
            "decision": decision or "Pending", "comment": comment, "evidence": col(row, "Evidence"),
        }
        if raw and decision is None:
            problems.append(f"{uid}: decision '{raw}' is not one of {DECISIONS}")
            item["decision"] = "Pending"
            item["raw_decision"] = raw
        elif decision in (COMMENTS, REJECTED) and not comment:
            problems.append(f"{uid}: '{decision}' has no reason in the comments column")
        items.append(item)

    counts = {d: sum(1 for i in items if i["decision"] == d) for d in DECISIONS}
    counts["Pending"] = sum(1 for i in items if i["decision"] == "Pending")
    return {"source": summary, "total": len(items), "counts": counts, "items": items, "problems": problems}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    try:
        feedback = read(args.input)
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL: cannot read review sheet: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # corrupt or non-xlsx files raise library-specific errors
        print(f"FAIL: cannot read review sheet: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    Path(args.output).write_text(json.dumps(feedback, indent=2, ensure_ascii=False), encoding="utf-8")
    c = feedback["counts"]
    print(f"PASS: {feedback['total']} use cases: {c[APPROVED]} approved, {c[COMMENTS]} with comments, "
          f"{c[REJECTED]} rejected, {c['Pending']} pending, {len(feedback['problems'])} problem(s)")
    for p in feedback["problems"]:
        print(f" - {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
