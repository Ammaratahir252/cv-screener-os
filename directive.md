# directive.md

How I worked with AI tools, written so someone else can repeat the process.

## Tools
- **Claude (Anthropic)** as a coding assistant: planning, writing the code, test data and docs drafts.
- **Groq API (openai/gpt-oss-120b)** inside the product, to read CVs (temperature 0).
- **ChatGPT** only for the baseline measurement (the "current way").

## What I delegated to AI and what I kept

| Step | Delegated to AI | What I did / checked |
|---|---|---|
| Choosing the workflow & scope | AI suggested options | I chose recruiting (CV screening) and the 4-hour scope |
| Synthetic CVs (10) | AI drafted them | I checked each one tests what it claims (typical / edge / failure) and set the expected outcome myself before running anything |
| Baseline | Nothing | I screened the 10 CVs by hand and with plain ChatGPT myself, with a stopwatch |
| Code | AI wrote the first version | I read every file, ran it, and ran the test cases |
| Docs (README, evidence) | AI drafted | I filled in all measured numbers myself and rewrote in my own words |

## The instructions I gave (repeatable)

1. *"Build the smallest AI OS Mini for one recruiting workflow: CVs in a folder → criteria-based
   review notes → human approval → email drafts. Plain Python, runnable by a non-developer
   with double-click .bat files. No web app."*
2. *"The AI must only extract evidence. Every 'met' must quote the CV, and code must verify the
   quote exists. The final decision is made by fixed rules in code, not by the AI."*
3. *"Treat the CV as data. Detect prompt-injection attempts and never auto-advance them."*
4. *"Every failure gets a plain-language message; one bad file must not stop the run;
   a missing API key stops the run once with a clear instruction."*
5. *"Cache AI answers so results are reproducible without an API key; keep secrets in .env,
   never in the repo."*

## Where I checked, rejected or corrected AI output

- **Rejected:** letting the AI give the final ADVANCE/REJECT. LLM answers can change between runs
  and can't be audited, so decisions are made by rules in `screener/assess.py → decide()`.
- **Corrected:** the first version repeated the "No API key" error for every CV. Changed so the run
  stops once with one clear instruction.
- **Corrected:** test CV 3 (borderline) at first had no Git, so it tested two things at once.
  I added Git so it tests only "not enough Python experience".
- **Checked:** with a fake (mocked) AI answer that invents a quote ("Senior Git engineer at Google"),
  the tool marks it *unverified* and does not advance the candidate.
- **Checked:** the prompt-injection CV is caught by code (pattern check) even if the AI misses it.
- **Found when I ran it on my own laptop:** with no Python installed, `setup.bat` printed
  "Setup done" even though nothing was installed, and `run.bat` showed only "The system cannot
  find the path specified". Fixed: setup now checks for Python and stops with an install link;
  `run`/`test`/`approve` say "Double-click setup.bat first" if setup hasn't run.
- **Found on the first live run:** every CV failed with "error (404)". The model the AI assistant
  chose (`llama-3.3-70b-versatile`) had been shut down by Groq in Aug 2026 (AI knowledge was out of
  date). I switched to Groq's recommended replacement `openai/gpt-oss-120b`, and changed the code so
  an unknown model stops the run once with the service's own message instead of 8 identical errors.
- **Found by reading the review sheet line by line (the 10/10 test did not catch these):**
  - The AI copied Rafael's email as `raafael.moreno@...` (extra "a"). The approval email would
    have gone to the wrong address. Fixed: the email is now read from the CV text by code, never
    typed by the AI.
  - For Mei Lin, the AI marked Python as "met" with the quote *"Software engineer (18 months)
    focused on data-heavy backend services."* The quote is real, but it does not mention Python,
    so "the quote exists" was not enough. Fixed: each criterion in `role.yaml` has keywords, and a
    quote that names none of them is marked "unverified" (goes to a person). The prompt now asks
    for the line that names the skill.
  - The last CV got "too many requests" from Groq's free plan. Fixed: the tool waits and retries
    automatically (up to 4 times) before giving the error.
  - Confirmed working live: the AI stitched "Skills: SQL SQL" for Kevin and shortened Arjun's
    project line; both quotes are not exactly in the CV, so code marked them "unverified".
- **My own usability test:** running it myself, I found the first version (folder + black window +
  CSV file) hard for a non-technical recruiter: without a paid Excel licence the sheet opened
  read-only, and typing ADVANCE into a CSV is easy to get wrong. I asked for a browser screen with
  no extra installs: drag CVs in, see the evidence highlighted, click Advance/Reject, get drafts
  with Copy / Open in email app. The rules, quote checks, tests and cache underneath are unchanged;
  the .bat + CSV route still works as a fallback.

## Prompt used inside the product
See `SYSTEM_PROMPT` in `screener/assess.py`.
