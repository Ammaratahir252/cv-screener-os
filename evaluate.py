"""Run all 10 test cases and compare with tests/expected.csv.

  python evaluate.py            uses saved AI answers (cache) -> reproducible, no API key needed
  python evaluate.py --fresh    asks the AI again (needs API key) to test consistency
"""
import csv
import shutil
import sys
import tempfile
import time
from pathlib import Path

from screener.pipeline import ROOT, screen_folder


def ok(expected, actual):
    if expected == "NOT ADVANCE":
        return actual in ("REJECT", "NEEDS REVIEW")
    return expected == actual


if __name__ == "__main__":
    fresh = "--fresh" in sys.argv
    with (ROOT / "tests" / "expected.csv").open(encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
    tmp = Path(tempfile.mkdtemp())
    inbox = tmp / "inbox"
    shutil.copytree(ROOT / "samples", inbox)
    cache = (tmp / "cache") if fresh else ROOT / "cache"
    start = time.time()
    _, rows = screen_folder(inbox, tmp / "out", use_cache=not fresh, cache_dir=cache)
    secs = time.time() - start
    got = {r["File"]: r for r in rows}

    passed = 0
    lines = ["| # | Case | Type | Expected | Actual | Result |", "|---|---|---|---|---|---|"]
    for c in cases:
        actual = got.get(c["file"], {}).get("AI recommendation", "MISSING")
        good = ok(c["expected"], actual)
        passed += good
        lines.append(f"| {c['case']} | {c['file']} | {c['type']} | {c['expected']} | {actual} | {'PASS' if good else 'FAIL'} |")
        if not good:
            lines[-1] += f" ({got.get(c['file'], {}).get('Why', '')})"
    report = "\n".join(lines) + f"\n\n**{passed}/{len(cases)} passed** in {secs:.1f} s ({'fresh AI answers' if fresh else 'saved answers'})\n"
    print(report)
    out = ROOT / "tests" / ("results_fresh.md" if fresh else "results.md")
    out.write_text(report, encoding="utf-8")
    print(f"Saved to {out.relative_to(ROOT)}")
