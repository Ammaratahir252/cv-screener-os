# evidence.md

All numbers below come from the 10 synthetic CVs in `samples/` (no real personal data).
Reproduce the system results with `test.bat` / `python evaluate.py` (no API key needed; uses `cache/`).

## 1. Baseline (current way), measured before building

| | By hand | Plain ChatGPT |
|---|---|---|
| Time for 10 CVs | [__] min | [__] min |
| Matched expected outcome | [__] / 10 | [__] / 10 |
| Same answer when repeated (CV 1 and CV 9) | n/a | [__] |
| Prompt-injection CV (case 9) | [__] | [__] |
| Empty / scanned files | [__] | [__] |
| Evidence you can check for each decision | Only in my head | [__] |

## 2. Test cases: expected vs actual

Expected outcomes were written in `tests/expected.csv` **before** running the system.

[Paste the table from `tests/results.md` here]

Consistency (`python evaluate.py --fresh`, second run without cache): [__] / 10 identical.

## 3. Before vs after

| Measure | By hand | Plain ChatGPT | AI OS Mini | Target |
|---|---|---|---|---|
| Recruiter time for 10 CVs | [__] min | [__] min | [__] min to read the sheet and decide (+ [__] s machine time) | ≤ 5 min |
| Matches expected | [__]/10 | [__]/10 | [__]/10 | ≥ 9/10 |
| Invented evidence shown as "met" | n/a | [__] | 0 (quotes verified in code) | 0 |
| Injection CV auto-advanced | n/a | [__] | No (NEEDS REVIEW) | 0 |
| Failure files handled | n/a | [__] | 2/2 clear messages, run continued | 2/2 |
| Human touches | read 10 CVs + write 10 notes | paste 10 CVs + read 10 answers | 1 click + 1 decision per candidate + 1 click | fewer |
| Emails without a human decision | n/a | n/a | 0 | 0 |

## 4. What I reused vs what I built

- **Checked first:** n8n has ready-made resume-screening templates (e.g. n8n workflow #6612,
  Gmail/Drive → OpenAI → Google Sheets), Zapier has ChatGPT steps, and plain ChatGPT can screen CVs.
  These give a score, but they do **not** verify that the AI's claims are in the CV, don't guard
  against CVs that instruct the AI, and need a hosted n8n/Zapier account and set-up a
  non-developer can't fix when it breaks.
- **Reused:** an existing LLM API (Groq, OpenAI-compatible), `pypdf` for PDF text, Excel/CSV as
  the review screen the recruiter already knows, my earlier CV-screener project idea.
- **Built (the gap):** quote verification in code, rule-based decisions, prompt-injection and
  duplicate flags, plain-language failure messages, an explicit human approval step, and a
  cache so results are reproducible.

## 5. What still fails and why

- [List any FAIL rows from the test table and the reason.]
- Scanned PDFs are rejected with a message instead of being read (no OCR in scope).
- Duplicate detection uses the email address or identical text; a candidate who re-applies with
  a different email and an edited CV would not be caught.
- The pattern check for prompt injection catches common phrasings only; the AI's own flag is a
  second layer, and a human reviews every flagged case.
- "1 year of Python" is judged by the AI from the text; unusual CV formats may still need review.

## 6. Next thing I would fix

Read CVs directly from the recruiter's mailbox (Gmail/Outlook) into `inbox`, so the trigger is
"new application email" instead of saving files by hand. After that: OCR for scanned PDFs.
