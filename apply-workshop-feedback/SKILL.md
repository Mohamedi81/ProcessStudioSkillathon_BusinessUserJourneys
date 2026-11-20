---
name: apply-workshop-feedback
description: Use when a workshop review sheet (xlsx) has come back with decisions (Approved as-is, Approved with comments, Rejected) and reasons, and the user wants the source blueprint or process-analysis document updated into a new version. Reads the returned sheet, applies every decision to the source document, and produces a revised document, a change log and a list of open questions. Works with sheets made by the business-experience-shifts skill.
allowed-tools: run_skill_script read_wiki_page write_temp_file read_temp_file save_output_text save_output_file
---

# Apply Workshop Feedback

Inputs, both required:
1. The returned **review sheet** (`review-sheet.xlsx`) from the workshop.
2. The **source document** the use cases were built from (a To-Be blueprint or a process analysis). The sheet's Summary tab names it. Use the version the sheet names.

Outputs, every run:
- the revised document, named like the source with the next version (`<name>-v2.md`),
- `change-log.md`: what changed and why, per use case,
- `open-questions.md`: what the workshop did not settle.

Never write code. A bundled script reads the sheet. You edit the document as text.

## Do not ask questions
Work from the two inputs. If the source document is missing, stop and say so in one sentence: without it nothing can be revised. Do not guess its content.

## Steps
1. **Read the sheet**: call `run_skill_script` with script `read_review_sheet.py`, `--input review-sheet.xlsx`, `--output feedback.json`. Then read `feedback.json` with `read_temp_file`.
   - If it fails, the file is not a review sheet from this workflow. Report that and stop.
   - `problems` lists missing reasons, unknown decision values and similar gaps. Do not stop. Handle them as the rules say below and report them.
2. **Read the source document** fully. Find each use case through its `source_ref` (for example `M1, W2` means measure M1 and weakness W2). If a ref cannot be found, say so in the change log. Do not guess.
3. **Apply the decisions** with these rules:

   | Decision | What you do to the document |
   |---|---|
   | Approved as-is | No content change. Mark it approved in the change log. |
   | Approved with comments | Keep the idea and revise the affected text to reflect the comment. Show the changed passage. If the comment is a condition, state it as a condition in the document. |
   | Rejected | Remove the measure or step from the target state and from the projected impact and roadmap, or move it to a "Rejected in workshop" section with the reason. Never delete silently. Recompute any total that included it. |
   | Pending, or an invalid value | No change. List it in `open-questions.md`. |
   | Rejected or Approved with comments with no reason | Apply the decision, and list "reason missing" in `open-questions.md`. Do not invent a reason. |

   - Edit only what the feedback supports. Leave every untouched passage exactly as it was.
   - Never invent numbers. If a comment changes a figure and gives no new value, flag it as an open question.
   - If two decisions pull in opposite directions on the same measure (for example one use case approved, another rejected), keep what both can agree on and list the conflict as an open question.
   - Recalculate dependent figures (for example a KPI target table) only when every input is known. Otherwise mark them "to be re-baselined".
4. **Version**: add a short block at the top of the revised document: version number, the date of the review if known, source version, and counts (approved, with comments, rejected, pending). Do not overwrite the original.
5. **Write the change log**: one row per use case: ID, use case, decision, reason, what changed in the document (section and sentence), and the source ref. Group rows by decision. Put a one-line summary first.
6. **Write the open questions**: each item with the use case ID, what is unresolved, and who owns it (the use case's Owner column).
7. **Save** the revised document, `change-log.md` and `open-questions.md` with `save_output_file` (write them with `write_temp_file` first). Reply with a short summary: counts per decision, what changed, and what is still open.

## Rules
- The sheet is the only evidence for decisions. Do not infer approval from silence.
- Quote the workshop's own reason in the change log. Do not paraphrase it into something stronger.
- Keep the document's structure, headings and tables. If a section is removed, say so in the change log.
- Keep the source `source_ref` labels (M1, W2 and so on) in the revised document so the next review can trace them.
- If the source is a .docx, .pptx or .xlsx rather than text, tell the user the revised text is delivered as markdown and that formatting is not preserved.
- The next workshop can reuse the revised document: tell the user to run `business-experience-shifts` on it to get a new deck and sheet.
