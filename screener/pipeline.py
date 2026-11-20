"""The whole screening run: inbox folder -> review sheet + notes."""
import csv
import hashlib
import logging
import os
import re
from datetime import datetime
from pathlib import Path

import yaml

from .assess import assess, decide, draft_email
from .llm import AIError
from .read_cv import read_cv

ROOT = Path(__file__).resolve().parent.parent
REVIEW_COLUMNS = ["YOUR DECISION (ADVANCE / REJECT)", "AI recommendation", "Why",
                  "Candidate", "Email", "File", "Must-haves", "Evidence from CV",
                  "Nice-to-haves", "Flags", "Notes file"]
MARK = {"met": "✔", "partly": "~", "not_met": "✘", "unverified": "?"}


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                if v.strip():
                    os.environ.setdefault(k.strip(), v.strip())


def load_config():
    settings = yaml.safe_load((ROOT / "settings.yaml").read_text(encoding="utf-8"))
    role = yaml.safe_load((ROOT / "role.yaml").read_text(encoding="utf-8"))
    if not role or not role.get("must_have"):
        raise SystemExit("role.yaml has no must-have criteria. Add at least one and run again.")
    return settings, role


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "candidate"


def screen_folder(inbox: Path, out_dir: Path, use_cache=True, cache_dir=None, progress=None, notices=None):
    """progress(done, total, filename) is called before each CV (used by the browser screen).
    notices: a list that receives plain-language warnings about the whole run."""
    notices = notices if notices is not None else []
    load_env()
    settings, role = load_config()
    cache_dir = cache_dir or ROOT / "cache"
    out_dir.mkdir(parents=True, exist_ok=True)
    notes_dir = out_dir / "notes"
    notes_dir.mkdir(exist_ok=True)
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(filename=ROOT / "logs" / "run.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    if not inbox.exists():
        raise SystemExit(f"The inbox folder is missing. Create a folder called 'inbox' here: {inbox.parent}")
    files = sorted(p for p in inbox.iterdir() if p.name != ".gitkeep"
                   and p.is_file() and not p.name.startswith("."))
    if not files:
        raise SystemExit(f"The inbox folder is empty. Put CV files (.pdf or .txt) into: {inbox}")

    rows, seen, quota_stop = [], {}, ""
    for i, path in enumerate(files):
        if progress:
            progress(i, len(files), path.name)
        text, error = read_cv(path)
        if error:
            logging.warning("%s: %s", path.name, error)
            rows.append(_row("ERROR", error, "-", "", path.name, "", "", "", "Could not read file", "",
                             {"error": error}))
            continue
        try:
            result = assess(text, role, settings, cache_dir, use_cache, offline=bool(quota_stop))
        except AIError as exc:
            logging.error("%s: %s", path.name, exc)
            if exc.kind == "quota":
                # Stop asking the AI, but keep going: saved answers and file checks still work,
                # and everything finished so far ends up in the review sheet.
                quota_stop = str(exc)
                notices.append(quota_stop)
                exc = AIError("Not checked: the AI allowance ran out. Check it again later.", kind="skipped")
            elif exc.fatal:
                raise SystemExit(f"STOPPED: {exc}")
            rows.append(_row("ERROR", str(exc), "-", "", path.name, "", "", "", "AI step failed", "",
                             {"error": str(exc)}))
            continue

        fingerprint = result["email"] or hashlib.sha1(re.sub(r"\W+", "", text.lower()).encode()).hexdigest()
        duplicate_of = seen.get(fingerprint)
        seen.setdefault(fingerprint, path.name)
        decision, why = decide(result, duplicate_of)

        must = [c for c in result["checks"] if c["kind"] == "must_have"]
        nice = [c for c in result["checks"] if c["kind"] == "nice_to_have"]
        flags = []
        if result["injection"]:
            flags.append("Possible manipulation of the AI")
        if duplicate_of:
            flags.append(f"Duplicate of {duplicate_of}")
        unconfirmed = [c for c in result["checks"] if c["status"] == "unverified"]
        for kind, words in (("must_have", "a must-have"), ("nice_to_have", "a good-to-have")):
            ids = [c.get("label") or c["id"] for c in unconfirmed if c["kind"] == kind]
            if ids:
                flags.append(f"Could not confirm the AI's claim for {', '.join(ids)} ({words})")

        note_file = notes_dir / f"{path.stem}_{slug(result['name'])}.md"
        note_file.write_text(_notes(result, decision, why, path.name, role), encoding="utf-8")
        rows.append(_row(
            decision, why, result["name"], result["email"], path.name,
            "  ".join(f"{MARK[c['status']]} {c['id']}" for c in must),
            " | ".join(f"{c['id']}: \"{c['evidence']}\"" for c in must if c["evidence"]),
            "  ".join(f"{MARK[c['status']]} {c['id']}" for c in nice),
            "; ".join(flags), note_file.name,
            {"summary": result["summary"], "checks": result["checks"], "flags": flags,
             "draft": draft_email(decision, result["name"], role)}))
        logging.info("%s -> %s (%s)", path.name, decision, why)

    sheet = out_dir / f"review_{datetime.now():%Y-%m-%d_%H%M}.csv"
    with sheet.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig opens cleanly in Excel
        writer = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return sheet, rows


def _row(decision, why, name, email, file, must, evidence, nice, flags, notes, details=None):
    row = dict(zip(REVIEW_COLUMNS, ["", decision, why, name, email, file, must, evidence, nice, flags, notes]))
    row["details"] = details or {}  # extra detail for the browser screen (not written to the sheet)
    return row


def _notes(result, decision, why, filename, role):
    out = [f"# {result['name']}  ({filename})", "",
           f"**AI recommendation:** {decision}  ", f"**Why:** {why}", "",
           f"**Summary:** {result['summary']}", "", "| Criterion | Status | Evidence from CV |",
           "|---|---|---|"]
    for c in result["checks"]:
        label = "MUST" if c["kind"] == "must_have" else "nice"
        out.append(f"| {label}: {c['text']} | {MARK[c['status']]} {c['status']} | {c['evidence'] or '-'} |")
    email = draft_email(decision, result["name"], role)
    out += ["", "## Draft email (sent only after you approve)", "",
            email or "_No draft: a person needs to decide first._"]
    return "\n".join(out) + "\n"
