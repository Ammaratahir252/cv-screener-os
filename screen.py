"""STEP 1: screen every CV in the inbox folder.  Run:  python screen.py"""
from collections import Counter

from screener.pipeline import ROOT, screen_folder

if __name__ == "__main__":
    print("Screening CVs in the 'inbox' folder...\n")
    notices = []
    sheet, rows = screen_folder(ROOT / "inbox", ROOT / "output", notices=notices)
    for n in notices:
        print(f"  NOTE: {n}\n")
    for r in rows:
        print(f"  {r['File']:<32} {r['AI recommendation']:<13} {r['Why']}")
    counts = Counter(r["AI recommendation"] for r in rows)
    print("\nDone: " + ", ".join(f"{v} {k}" for k, v in counts.items()))
    print(f"\nNEXT: open {sheet.relative_to(ROOT)} in Excel,")
    print("type ADVANCE or REJECT in the first column for each candidate, save it,")
    print("then run approve (approve.bat). No email is created until you do this.")
