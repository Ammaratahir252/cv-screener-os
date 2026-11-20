"""The human approval step: turn a person's ADVANCE / REJECT decisions into email drafts.

Used by both approve.py (sheet edited in Excel) and the browser screen (buttons).
Nothing is ever sent: drafts are written to the outbox folder, and every decision is logged.
"""
import csv
from datetime import datetime
from pathlib import Path

import yaml

from .assess import draft_email
from .pipeline import REVIEW_COLUMNS, ROOT

DECISION_COL = REVIEW_COLUMNS[0]
VALID = ("ADVANCE", "REJECT")


def latest_sheet():
    sheets = sorted((ROOT / "output").glob("review_*.csv"))
    return sheets[-1] if sheets else None


def read_sheet(sheet: Path):
    with sheet.open(encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.DictReader(f))
    if rows and DECISION_COL not in rows[0]:
        raise ValueError(f"The column '{DECISION_COL}' is missing in {sheet.name}. "
                         "Did the sheet get renamed or edited?")
    return rows


def write_decisions(sheet: Path, decisions: dict):
    """Write decisions made with the buttons into the review sheet, so the sheet stays the record."""
    rows = read_sheet(sheet)
    for r in rows:
        if r["File"] in decisions:
            r[DECISION_COL] = decisions[r["File"]] or ""
    with sheet.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def approve(sheet: Path):
    """Create a draft for every row a person has decided. Returns what happened."""
    role = yaml.safe_load((ROOT / "role.yaml").read_text(encoding="utf-8"))
    rows = read_sheet(sheet)
    outbox = ROOT / "outbox"
    outbox.mkdir(exist_ok=True)
    log = ROOT / "output" / "decisions_log.csv"
    new_log = not log.exists()
    drafts, waiting, invalid = [], [], []
    with log.open("a", newline="", encoding="utf-8") as lf:
        w = csv.writer(lf)
        if new_log:
            w.writerow(["time", "sheet", "file", "candidate", "AI recommendation",
                        "human decision", "AI overruled?"])
        for r in rows:
            if r["AI recommendation"] == "ERROR":
                continue
            human = (r[DECISION_COL] or "").strip().upper()
            if not human:
                waiting.append(r["File"])
                continue
            if human not in VALID:
                invalid.append(f"{r['File']} ('{r[DECISION_COL]}')")
                continue
            body = draft_email(human, r["Candidate"], role)
            to = r.get("Email", "")
            text = (f"To: {to}\n" if to else "") + body
            path = outbox / f"{r['File'].rsplit('.', 1)[0]}_{human.lower()}.txt"
            path.write_text(text, encoding="utf-8")
            w.writerow([f"{datetime.now():%Y-%m-%d %H:%M}", sheet.name, r["File"], r["Candidate"],
                        r["AI recommendation"], human,
                        "yes" if human != r["AI recommendation"] else "no"])
            subject, _, rest = body.partition("\n\n")
            drafts.append({"file": r["File"], "candidate": r["Candidate"], "to": to,
                           "decision": human, "subject": subject.replace("Subject: ", "", 1),
                           "body": rest, "saved_as": f"outbox/{path.name}"})
    return {"drafts": drafts, "waiting": waiting, "invalid": invalid}
