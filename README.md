# CV Screener: AI OS Mini for recruiters

Add CVs, click **Check**, and see for each candidate **Advance / Reject / Needs your review**,
with the **exact sentence from the CV** highlighted behind every point.
Nothing is decided or emailed until **you** click Advance or Reject and create the drafts.

```
Add CVs  ->  Check  ->  read the highlighted evidence  ->  YOU choose Advance / Reject  ->  email drafts
```

---

## First time only (about 5 minutes)

1. **Install Python** from <https://www.python.org/downloads/>. On the first screen of the installer, tick **"Add python.exe to PATH"**.
2. Double-click **`setup.bat`**. It installs what the tool needs and creates a file called **`.env`**.
3. Get a **free AI key** from Groq: <https://console.groq.com/keys> (sign in, click *Create API Key*, copy it).
4. Open **`.env`** with Notepad and paste the key after `GROQ_API_KEY=`, then save.
   *Never share this file or upload it anywhere.*

> Prefer Gemini or OpenAI? Paste that key instead and change `provider:` in `settings.yaml`.

## Every time (the browser screen)

1. Double-click **`start.bat`**. Your browser opens the CV Screener. Keep the black window open while you work.
2. **Add CVs:** drag the CV files (PDF or text) onto the page, or click *choose files*.
3. Click **Check CVs**. A bar shows progress (a few seconds per CV).
4. **Check the results.** Candidates that need your attention are shown first. For each requirement you see
   ✓ shown in the CV, ~ only partly shown, ✕ not found, or **?** not confirmed, with the CV sentence highlighted.
   Yellow warnings point out duplicates, suspicious CVs and AI claims the tool could not confirm.
5. For each candidate click **Advance** or **Reject**. You can follow the AI suggestion or change it.
6. Click **Create email drafts**. Each email appears with **Copy email** and **Open in my email app**.
   Nothing is sent by the tool. Copies are saved in the `outbox` folder, and every decision is
   recorded in `output\decisions_log.csv`.
7. Next week: click **Start a new batch**. Old CVs move to the `archive` folder.

**Download as a spreadsheet** gives you the same results as a CSV file for Excel or Google Sheets.

### Without the browser (optional)

Put CVs in the `inbox` folder and double-click **`run.bat`**. Open the newest `output\review_....csv`
(Excel, Google Sheets or Notepad), type ADVANCE or REJECT in the first column, save, and double-click
**`approve.bat`**. It does exactly the same as the buttons.

## When something goes wrong

| You see | What it means / what to do |
|---|---|
| `ERROR ... file is empty` | The CV file is blank. Check you saved the right file. |
| `ERROR ... no readable text (scan or photo)` | Ask the candidate for a text PDF, or paste the CV into a `.txt` file. |
| `ERROR ... Word files are not supported` | Save the CV as PDF and run again. |
| `STOPPED: No API key found` | Do step 4 of "First time only". |
| `STOPPED: ... rejected the API key` | The key is wrong or expired. Create a new one. |
| `AI service busy, waiting...` | Normal on free plans. The tool waits and tries again by itself. |
| `... still busy after 4 tries` | Wait one minute and run again. Finished CVs are saved, so they are not asked again. |
| `STOPPED: ... does not know the model` | The AI company retired that model. Put a current model name in `settings.yaml`. |
| `Still waiting for your decision` | Some candidates have no decision yet. That's fine: only decided ones get emails. |
| The browser page does not open | Look at the black window: it shows the address (e.g. http://127.0.0.1:8765). Paste it into your browser. |
| `The AI key is missing` (yellow box) | Do step 4 of "First time only", then close the black window and start again. |

One bad file never stops the others: it gets an ERROR row and the run continues.

## Change the job

Edit **`role.yaml`** in Notepad: the role name, the **must-haves** (all needed to advance),
the **nice-to-haves** (shown in the notes only) and the **keywords** for each one.

## Check that it works (for reviewers)

Double-click **`test.bat`** (or run `python evaluate.py`). It runs the 10 test CVs in `samples`
and compares the result with `tests/expected.csv`. It uses the saved AI answers in `cache/`,
so it gives the same result on any computer **without an API key**.
`python evaluate.py --fresh` asks the AI again (needs a key) to check consistency.

## How it decides (in plain words)

1. The AI reads the CV and, for each requirement, says *met*, *partly* or *not met*, with a quote.
2. **The tool checks every quote is really in the CV and really mentions the skill** (keywords in
   `role.yaml`). If not, the point becomes "unverified". The email address is read from the CV by
   the tool, not by the AI.
3. Simple fixed rules make the recommendation:
   - CV tries to instruct the AI, or is a duplicate → **NEEDS REVIEW**
   - any must-have clearly missing → **REJECT**
   - any must-have only partly shown or unverified → **NEEDS REVIEW**
   - all must-haves shown with quotes → **ADVANCE**
4. A person always makes the final decision before any email is drafted.

## Files

| File / folder | What it is |
|---|---|
| `start.bat` | Opens the browser screen (normal way to use it) |
| `inbox/` | CVs waiting to be checked (the screen puts them here) |
| `archive/` | CVs from earlier batches |
| `output/` | Review sheets, notes, decision log |
| `outbox/` | Email drafts after you approve |
| `role.yaml` | The job and its requirements |
| `settings.yaml` | Which AI service to use |
| `samples/`, `tests/` | The 10 test CVs and expected results |
| `cache/` | Saved AI answers (makes results repeatable) |
| `screener/`, `app.py`, `ui/` | The code and the browser screen |
