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

**10/10 passed** in 0.1 s (saved answers)
