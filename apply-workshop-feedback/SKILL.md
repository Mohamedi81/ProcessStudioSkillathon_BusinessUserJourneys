---
name: apply-workshop-feedback
description: Use when a workshop has reviewed use cases and the user wants the outcome captured and applied. Takes a review sheet (xlsx) plus either the workshop feedback as unstructured notes or a transcript, or decisions the user gives one by one, or an already filled sheet. Fills the Decision and Comments columns with the evidence behind each, then updates the source blueprint or process-analysis document into a new version with a change log and open questions. Works with sheets made by the business-experience-shifts skill.
allowed-tools: run_skill_script read_wiki_page write_temp_file read_temp_file save_output_text save_output_file
---

# Apply Workshop Feedback

Inputs:
1. The **review sheet** (`review-sheet.xlsx`) from `business-experience-shifts`. It lists the use cases.
2. The **workshop outcome**, in any one of these forms:
   - **A. Filled sheet**: the Decision column already has values.
   - **B. Unstructured notes or a transcript**: meeting notes, chat export, recording transcript, email thread.
   - **C. Nothing yet**: the user will tell you the decisions (see "Path C").
3. The **source document** the use cases were built from (blueprint or process analysis). The sheet's Summary tab names it. Needed to produce the new version. If it is missing, still do the sheet and say the new version could not be made.

Outputs:
- `review-sheet-filled.xlsx` (paths B and C): the sheet with Decision, Comments and Evidence filled in.
- the revised document, named like the source with the next version (`<name>-v2.md`),
- `change-log.md` and `open-questions.md`.

Never write code. Bundled scripts read and write the sheet. You edit the document as text.

## Step 1: read the sheet
Try the reader **once**. Call `run_skill_script` with script `read_review_sheet.py`, `--input <the uploaded sheet>`, `--output feedback.json`. Read `feedback.json` with `read_temp_file`.
- `items` is the list of use cases with their `as_is` and `to_be` text. `counts` tells you the path: if some use cases already have a decision, treat the rest as pending.

**If the reader is blocked or fails (for example `INPUT_INVALID`), do not stop and do not retry.** A blocked result comes from the platform, not from the user's file. Do not tell the user their file is wrong or has the wrong structure. Read the sheet from the text of the upload instead:
1. Use the text content of the uploaded `.xlsx` that you can already see in the conversation (the preview). It lists the rows of the Review tab with their columns.
2. Build the same `items` list yourself: for each row copy `id`, `role`, `use_case`, `stage`, `source_ref`, `as_is`, `to_be`, `owner`, `decision` and `comment` exactly as written. Copying what the user wrote is not inventing. Set `evidence` to `from uploaded sheet`. Accept a decision only if it is one of "Approved as-is", "Approved with comments", "Rejected". An empty or other value is Pending.
3. If the preview is cut off, has no Decision column, or a row is unreadable, say which use cases you could not read and treat only those as Pending. If no row can be read at all, ask the user to paste the ID and Decision columns, then continue as Path C.
4. Say in one line at the top of your reply that the sheet was read from the upload text because the file reader was unavailable.

## Step 2: get the decisions

### Path A: filled sheet
Use `feedback.json` (or the `items` you built from the upload text) as it is. Go to Step 4.

### Path B: unstructured notes or transcript
Go through every use case in `items` and decide from the notes. Use these rules:

| What the notes show | Decision |
|---|---|
| Clear agreement, no conditions ("yes, go ahead", "agreed", "that works") | Approved as-is |
| Agreement with a condition, change, or caveat ("fine, but not for spot buys") | Approved with comments |
| Clear refusal, or a blocker that makes it not feasible ("we can't do that", "no") | Rejected |
| Not discussed, unclear, only a question with no answer, or a deferral ("let's come back") | Pending |

- **Silence is not approval.** A use case nobody mentioned is Pending.
- **Do not guess.** If a remark could be approval or rejection, mark Pending and say why in the evidence.
- **Evidence is mandatory** for every decision other than Pending. Put the quote, with the speaker if the notes name one, in `evidence`. Copy it, do not paraphrase.
- **Comment** is the reason: the condition for "with comments", the blocker for "Rejected". Use the speaker's own words. Never invent a reason.
- Match remarks to use cases by what they talk about: the use case title, its steps, its source ref (for example `M1`, `W2`), the role, or the system. If a remark fits two use cases, record it on both and note that. If you cannot tell which use case a remark is about, put it in `open-questions.md`.
- If the notes show several people disagreeing on one use case, set it to Pending and record both positions in `evidence`.
- If someone changes their mind later in the same notes, use the last position and note the earlier one in `evidence`.

Write `decisions.json` with `write_temp_file`: the same structure as `feedback.json`, with `decision`, `comment` and `evidence` set on each item, and nothing else changed. Then call `run_skill_script` with script `fill_review_sheet.py`, `--input decisions.json`, `--output review-sheet-filled.xlsx`.
- It checks that every decision has evidence and is a valid value. On failure it lists the problems. Fix `decisions.json` and run it again.
- Warnings about a missing reason are fine: carry them to `open-questions.md`.

### Path C: the user gives decisions one by one
There is no transcript, so ask the user. Do not make decisions up.
1. List the use cases as a numbered list: ID, role, title, and the To-Be in one line. Group by role.
2. Ask the user which ones are accepted as-is, which are accepted with comments (and what), and which are rejected (and why). Tell them they can answer in one message, for example "1.1, 1.3 ok. 1.2 ok but not spot buys. 2.1 rejected, no scanners yet".
3. Everything they do not mention stays Pending. Say so.
4. Set `evidence` to `stated by user` for each decision. Then fill the sheet as in Path B.

This is the only path where you may ask a question. Paths A and B run without questions.

## Step 3: show the result of the fill (paths B and C)
Reply with a table of what you recorded: ID, use case, decision, reason, and evidence. Tell the user the workshop should check the Evidence column against what was said before the decisions are applied. Offer to change any decision. If the user corrects one, update `decisions.json`, run `fill_review_sheet.py` again, and continue.
If the user has already said to go ahead, continue to Step 4 and make the same table part of your final summary.

## Step 4: apply the decisions to the source document
1. **Read the source document** fully. Find each use case through its `source_ref` (for example `M1, W2` means measure M1 and weakness W2). If a ref cannot be found, say so in the change log. Do not guess.
2. **Apply the decisions**:

   | Decision | What you do to the document |
   |---|---|
   | Approved as-is | No content change. Mark it approved in the change log. |
   | Approved with comments | Keep the idea and revise the affected text to reflect the comment. State a condition as a condition. |
   | Rejected | Remove the measure or step from the target state and from the projected impact and roadmap, or move it to a "Rejected in workshop" section with the reason. Never delete silently. Recompute any total that included it. |
   | Pending or an invalid value | No change. List it in `open-questions.md`. |
   | Rejected or Approved with comments with no reason | Apply the decision, and list "reason missing" in `open-questions.md`. Do not invent a reason. |

   - Edit only what the feedback supports. Leave every untouched passage exactly as it was.
   - Never invent numbers. If a comment changes a figure and gives no new value, flag it as an open question.
   - If two decisions pull in opposite directions on the same measure, keep what both can agree on and list the conflict as an open question.
   - Recalculate dependent figures only when every input is known. Otherwise mark them "to be re-baselined".
3. **Version**: add a short block at the top of the revised document: version number, source version, and counts (approved, with comments, rejected, pending). Do not overwrite the original.
4. **Change log** (`change-log.md`): a one-line summary first. Then one row per use case: ID, use case, decision, reason (quoted), evidence, what changed in the document (section and sentence), and the source ref. Group rows by decision.
5. **Open questions** (`open-questions.md`): each item with the use case ID, what is unresolved, and who owns it (the Owner column).

## Step 5: deliver
Write each file with `write_temp_file` and save it with `save_output_file`: `review-sheet-filled.xlsx` (paths B and C), the revised document, `change-log.md` and `open-questions.md`. Reply with a short summary: counts per decision, what changed, and what is still open. If the workshop covered fewer than all use cases, say how many are still pending.

## Rules
- The sheet and the notes are the only evidence for decisions. Do not infer approval from silence.
- Keep the document's structure, headings and tables. If a section is removed, say so in the change log.
- Keep the source `source_ref` labels (M1, W2 and so on) in the revised document so the next review can trace them.
- If the source is a .docx, .pptx or .xlsx, tell the user the revised text is delivered as markdown and that formatting is not preserved.
- To start the next round, tell the user to run `business-experience-shifts` on the revised document.
