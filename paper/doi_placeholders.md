# DOI and date placeholders in draft v11

**Status (14 November 2026, about 22:15 ET): all placeholders have been swapped in.** The OSF registration was approved and made public on 14 November 2026 (registered 16:59 ET, `date_registered` 2026-11-14T21:59 UTC per the OSF API; approved about 21:16 ET). OSF DOI: https://doi.org/10.17605/OSF.IO/PHQ42. The GitHub repository is public. Release v0.11.0 was created and Zenodo minted https://doi.org/10.5281/zenodo.24237979 (record https://zenodo.org/records/24237979). Sections 1–3 below are done and kept as a record.

When OSF approves the registration (https://osf.io/phq42/), check the DOI on the registration page (expected `10.17605/OSF.IO/PHQ42`) and the registration date shown by OSF. Then replace the placeholders below **in the source files** (`*.src.md`, `references.bib`, `README.md`) and rebuild (`cd paper && python3 build_paper.py v11 && python3 build_paper.py v11 --layout`, then `soffice --headless --convert-to pdf draft_v11.docx supplement_v11.docx`). The `.md`, `.docx` and `.pdf` files are generated, so do not edit them by hand.

Quick find: `grep -rn "OSF DOI – pending\|Zenodo DOI – pending\|submitted 14 November 2026" paper/*.src.md paper/references.bib README.md`

## 1. OSF DOI: `[OSF DOI – pending; expected 10.17605/OSF.IO/PHQ42]` (DONE: replaced by https://doi.org/10.17605/OSF.IO/PHQ42)

Replace with `https://doi.org/10.17605/OSF.IO/PHQ42` (or the DOI OSF actually shows).

| # | File | Line (v11 source) | Where |
|---|---|---|---|
| 1 | `paper/draft_v11.src.md` | 14 | title-page line "Analysis plan: …" |
| 2 | `paper/draft_v11.src.md` | 174 | Statements, "Analysis plan and registration" |
| 3 | `paper/supplement_v11.src.md` | 14 | S1 introduction |
| 4 | `paper/references.bib` | 345 | `dixon2026prereg` `howpublished` field (prints as reference 9 in the draft and reference 1 in the supplement) |

The README on GitHub says "OSF DOI pending" in two places (the "Latest" section and the "Licence and citation" section): replace with the DOI link.

## 2. Zenodo DOI: `[Zenodo DOI – pending]` (DONE: replaced by https://doi.org/10.5281/zenodo.24237979)

Done after Liam's explicit yes ("Do all"): repository made public on 14 November 2026, release v0.11.0 created, and the placeholder replaced with https://doi.org/10.5281/zenodo.24237979. The "private at the time of writing" wording listed below was also deleted, and "will be available at" was changed to "are available at".

| # | File | Line | Where |
|---|---|---|---|
| 1 | `paper/draft_v11.src.md` | 176 | Statements, "Data and code availability" (also delete "The repository is private at the time of writing and will be made public before posting.") |
| 2 | `paper/supplement_v11.src.md` | 108 | S8 STRESS table, "Code access" row (also delete "private at the time of writing; to be made public before posting") |
| 3 | `README.md` (GitHub copy) | "Reproduce draft v10 and v11" section, last line | "**Archive:** … [Zenodo DOI – pending]" |
| 4 | `README.md` (GitHub copy) | "Licence and citation" | "A Zenodo DOI will be added when the archive is released." |

## 3. Registration date: "submitted 14 November 2026" (DONE: now "registered retrospectively on 14 November 2026"; the bib entry has `doi` and `url` fields)

The text says the retrospective registration was **submitted** on 14 November 2026 (true today; it is pending admin approval). If OSF shows a later registration date after approval, consider changing "submitted 14 November 2026" to "registered [date]; submitted 14 November 2026" in:

- `paper/draft_v11.src.md`: line 14 (title page), §2.1 (line 44), Table 3 row D8 (line 166), Statements (line 174)
- `paper/supplement_v11.src.md`: S1 introduction (line 14), S1.1 row D8 (line 27)
- `paper/references.bib`: line 345

## 4. Number check after the swap

Re-run `.venv/bin/python scripts/45_check_v11_numbers.py`. The DOI and date are not numbers it checks against results, but it must still report 0 uncovered tokens (the year 2026 and "14" are listed as design constants).
