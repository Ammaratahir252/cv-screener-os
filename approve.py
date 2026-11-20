"""STEP 2 (after a person has decided in the review sheet): turn decisions into email drafts.
Run:  python approve.py   (uses the newest review sheet in the output folder)
The browser screen (start.bat) does the same thing with buttons."""
from screener.approval import approve, latest_sheet

if __name__ == "__main__":
    sheet = latest_sheet()
    if not sheet:
        raise SystemExit("No review sheet found. Run the screening first (run.bat or start.bat).")
    try:
        result = approve(sheet)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(f"{len(result['drafts'])} email draft(s) created in the 'outbox' folder "
          "(nothing was sent automatically).")
    if result["waiting"]:
        print(f"Still waiting for your decision ({len(result['waiting'])}): " + ", ".join(result["waiting"]))
    if result["invalid"]:
        print("Please type only ADVANCE or REJECT for: " + ", ".join(result["invalid"]))
