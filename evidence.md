# evidence.md

All numbers below come from the 10 synthetic CVs in `samples/` (made-up people, no real personal data).
Reproduce the system results with `test.bat` / `python evaluate.py` (no API key needed; uses `cache/`).

## 1. Baseline (current way), measured before comparing

Expected outcomes were written in `tests/expected.csv` before any tool was run.

| | Plain ChatGPT (measured 20 Nov 2026) | By hand |
|---|---|---|
| Time for 10 CVs | about 1 min for ChatGPT to answer (10 CVs pasted in; copying in and checking the answers not included) | Not measured (I ran out of time; I report the gap rather than guess) |
| Matched expected outcome | **6 / 10** | n/a |
| Same answer when repeated in a new chat (CV 1 and CV 9) | Yes, both the same | n/a |
| Prompt-injection CV (case 9) | Not fooled (REJECT), but did not mention the hidden instruction in the first run; only flagged it in the repeat | n/a |
| Empty file / scanned PDF | **Both REJECTED** — a real candidate whose upload failed would get a rejection email | n/a |
| Duplicate CV (case 10) | Noticed it, but still said **ADVANCE** — Daniel would get two invitations | n/a |
| Evidence you can check | Summaries in ChatGPT's own words, no exact quotes; to trust them you must re-read each CV | n/a |

ChatGPT judged the six "normal" CVs correctly (including spotting that Kevin's only job is retail).
Its failures are all in the cases that need a *warning* instead of a *decision*.

## 2. Test cases: expected vs actual (final version)

`python evaluate.py` (saved AI answers, runs anywhere without a key):

| # | Case | Type | Expected | Actual | Result |
|---|---|---|---|---|---|
| 1 | 01_strong_match.txt | typical | ADVANCE | ADVANCE | PASS |
| 2 | 02_clear_reject.txt | typical | REJECT | REJECT | PASS |
| 3 | 03_borderline.txt | edge | NEEDS REVIEW | NEEDS REVIEW | PASS |
| 4 | 04_synonyms.txt | edge | ADVANCE | ADVANCE | PASS |
| 5 | 05_keyword_stuffing.txt | edge | NOT ADVANCE | NEEDS REVIEW | PASS |
| 6 | 06_missing_requirement.txt | typical | REJECT | REJECT | PASS |
| 7 | 07_empty_file.txt | failure | ERROR | ERROR | PASS |
| 8 | 08_scanned_pdf.pdf | failure | ERROR | ERROR | PASS |
| 9 | 09_prompt_injection.txt | failure | NEEDS REVIEW | NEEDS REVIEW | PASS |
| 10 | 10_duplicate_of_01.txt | edge | NEEDS REVIEW | NEEDS REVIEW | PASS |

**10/10 passed** in 0.1 s.

**Consistency** (`python evaluate.py --fresh`, asks the AI again with no saved answers):
- Run 1 (20 Nov, 15:21): **10/10** identical decisions, 18.6 s. (Before the final prompt change.)
- Run 2 (20 Nov, 19:19, final prompt): the first 5 CVs gave **the same decisions**; then Groq's free
  daily allowance ran out, so CVs 6, 9 and 10 were not sent to the AI (see failure case F5 below).
- Run 3 (21 Nov, 11:46, final prompt): **9/10**. All 7 CVs that reached the AI gave the same decisions as
  the saved answers, and both broken files gave the same error. CV 10 was not sent to the AI because the
  free daily allowance ran out again (Groq counts the last 24 hours); the tool reported it as "Not checked".
  Saved in `tests/results_fresh.md`.
- **Summary:** in every fresh run, every CV that reached the AI got the same decision (10/10, 5/5, 7/7).
  The only differences were CVs the AI was never asked about because of the free quota.

### Extra failure cases observed live (not simulated)

| # | What happened | What the tool did |
|---|---|---|
| F1 | No Python installed on the laptop | `setup.bat` now stops with "Python is not installed" and the download link (first version wrongly said "Setup done") |
| F2 | AI model retired by Groq (404) | Stops once: "The AI service does not know the model…", instead of 8 identical errors |
| F3 | Per-minute limit (429) on the free plan | Waits and retries by itself, prints "AI service busy, waiting…" |
| F4 | AI copied an email wrongly (`raafael.moreno@…`) | Email is now read from the CV by code, never by the AI |
| F5 | Daily free allowance used up mid-run | Stops asking the AI, keeps finished CVs, marks the rest "Not checked", clear message, no crash |
| F6 | Excel without a licence opens the sheet read-only | Added the browser screen; the sheet is still downloadable for Google Sheets/Notepad |

## 3. Before vs after

| Measure | Plain ChatGPT | AI OS Mini | Target |
|---|---|---|---|
| Matches expected (10 cases) | 6/10 | **10/10** | ≥ 9/10 (A1) |
| Claims you can check | none (summaries) | every point has an exact CV quote, checked in code | — |
| Invented evidence shown as "met" | can't tell without re-reading | **0** — made-up quotes (Kevin's "Skills: SQL SQL", Arjun's shortened line) were caught live and shown as "?" | 0 (A2) |
| Injection CV advanced | No | **No** (NEEDS REVIEW + warning) | 0 (A3) |
| Empty / scanned file | Rejected the candidate | **Clear message, candidate not rejected**, run continued | 2/2 (A4) |
| Duplicate | Advanced twice | **Flagged** | — |
| Same decisions on re-run | 2/2 checked | Every CV the AI answered: same decision in all 3 fresh runs (10/10, 5/5, 7/7); some CVs not asked because of the free quota | 10/10 (A5) |
| Recruiter time for 10 CVs | ~1 min AI time + pasting + re-checking every answer against the CVs | **3 min** (measured): read the screen, decide all 8 candidates, create drafts (+ ~19 s machine time with live AI) | ≤ 5 min (A6) |
| Emails without a human decision | n/a | **0** — drafts only after Advance/Reject is clicked; nothing is sent | 0 (A7) |

## 4. What I reused vs what I built

- **Checked first:** n8n has ready-made resume-screening templates (e.g. n8n workflow #6612,
  Gmail/Drive → OpenAI → Google Sheets), Zapier has ChatGPT steps, and plain ChatGPT can screen CVs
  (measured above). These give a score, but they do **not** verify that the AI's claims are in the CV,
  don't flag broken files or duplicates, and need a hosted account and set-up a non-developer can't fix.
- **Reused:** an existing LLM API (Groq, OpenAI-compatible), `pypdf` for PDF text, Python's built-in web
  server for the screen, CSV as the record the recruiter can open in any spreadsheet.
- **Built (the gap):** quote verification in code (quote must exist AND mention the skill), rule-based
  decisions, prompt-injection and duplicate flags, plain-language failure messages, quota handling,
  an explicit human approval step, and a cache so results are reproducible without a key.

## 5. What still fails and why

- Scanned PDFs are not read (no OCR in scope); the candidate gets a clear "ask for a text PDF" message.
- Duplicates are found by email address or identical text; a re-application with a new email and an
  edited CV would not be caught.
- The pattern check for prompt injection catches common phrasings only; the AI's own flag is a second
  layer, and a person reviews every flagged case.
- "1 year of Python" is judged by the AI from the text; unusual CV formats may still need review.
- The AI's written summary can disagree with the rule-based suggestion (seen once). The screen labels it
  as the AI's own text; the decision always comes from the rules.
- Groq's free plan allows roughly 70–100 CVs per day; bigger volumes need a paid key or another provider.

## 6. Next thing I would fix

Read CVs directly from the recruiter's mailbox (Gmail/Outlook) into the screen, so the trigger is
"new application email" instead of dragging files. After that: OCR for scanned PDFs.
