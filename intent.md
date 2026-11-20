# intent.md

## The customer and the workflow

**Customer:** a recruiter at a small staffing agency (non-developer). Every week they receive
20–50 CVs per open role and must sort them before the hiring manager's Monday meeting.

**Current way:** the recruiter reads every CV by hand, or pastes CVs one by one into ChatGPT with
a prompt only they know how to write. The result depends on who does it and on the day:
the same CV can get a different answer, ChatGPT sometimes states skills the CV never mentions,
nobody can trace *why* a candidate was rejected, and when the recruiter is away the task stops.

**Bottleneck:** not reading speed but **trust**. Every AI answer has to be re-checked against the
CV by hand, so the time saving disappears and mistakes (wrong rejections, invented skills) are
found late, sometimes after an email was sent.

## What I'm building (the smallest AI OS Mini)

- **Trigger:** recruiter puts CVs in the `inbox` folder and double-clicks `run.bat`.
- **Core path:** CV → text → AI checks each requirement and must quote the CV → code verifies
  every quote → fixed rules give ADVANCE / REJECT / NEEDS REVIEW → review sheet + notes.
- **Human approval point:** the recruiter types ADVANCE or REJECT per candidate; only then
  `approve.bat` creates email drafts. Nothing is sent automatically.
- **Failure messages:** plain-language messages for empty files, scanned PDFs, Word files,
  missing or wrong API key, rate limits and broken AI answers. One bad CV never stops the run.

## Acceptance test (written before building)

Measured on the same 10 synthetic test CVs (`samples/`), against `tests/expected.csv`:

| # | Measure | Target |
|---|---|---|
| A1 | Cases that match the expected outcome | **≥ 9 / 10** |
| A2 | Invented evidence reaching the recruiter as "met" (claim not in CV) | **0** |
| A3 | Prompt-injection CV auto-advanced | **0** (must be NEEDS REVIEW) |
| A4 | Failure cases (empty, scanned) handled with a clear message, run continues | **2 / 2**, 0 crashes |
| A5 | Same inputs, same decisions on a second run | **10 / 10** |
| A6 | Recruiter hands-on time for 10 CVs (read sheet + decide) | **≤ 5 min**, and less than the baseline |
| A7 | Emails created without a human decision | **0** |

**Baseline** (measured by me before building, see `evidence.md`):
- By hand: **[__] min** for 10 CVs, **[__] / 10** matched the expected outcome.
- Plain ChatGPT: **[__] min** for 10 CVs, **[__] / 10** matched; consistency on re-run: **[__]**.

## What I left out to fit 4 hours

- Reading CVs straight from Gmail/Outlook and sending emails automatically (drafts only).
- Word (.docx) files and OCR for scanned PDFs (clear error message instead).
- A web interface; multiple roles at once; multiple users.
- Ranking candidates against each other (each CV is judged against the criteria only).
- Bias auditing beyond keeping personal details out of the decision rules.
