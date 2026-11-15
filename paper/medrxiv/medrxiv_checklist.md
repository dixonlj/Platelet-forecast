# medRxiv checklist and self-review (draft v11)

Prep only. Retrieved official requirements on 14 November 2026 (America/New_York) from the pages listed in `medrxiv_form_answers.md`. The live submission form was not opened (no account was created). Status means whether draft v11 and this package meet the published requirement, not whether the paper has already been submitted.

Files in this folder:

- `draft_v11_layout.pdf` — manuscript to upload (16 pages, US letter; copy of `paper/draft_v11_layout.pdf`, rebuilt 14 November 2026, 10:33 PM ET)
- `supplement_v11_layout.pdf` — supplement to upload (8 pages; copy of `paper/supplement_v11_layout.pdf`, same rebuild)
- `medrxiv_form_answers.md` — field-by-field paste answers
- this checklist

The banner and running header were updated in v11 on 14 November 2026 (America/New_York), as recorded below. No numbers were changed. `scripts/45_check_v11_numbers.py` was re-run after the rebuild: Part A 64/64 pass.

---

## Requirements versus draft v11

| Requirement | Status | Where it is met or what is missing |
|---|---|---|
| Account at submit.medrxiv.org; no fee | met (action left to you) | You create or sign in yourself. Answers use dixonlj1993@gmail.com and ORCID 0009-0003-0610-197X. |
| Work is complete but unpublished; not already posted on another preprint server; not accepted or published in a journal | met, with a note | Not posted on medRxiv, bioRxiv, or another preprint server. Not journal-accepted. OSF is an analysis-plan registration, not a preprint of this manuscript. The public GitHub repo and Zenodo archive already contain the paper files. That is not a second preprint server, but automated screening "for material that has already appeared online" may flag it. The cover note explains this. |
| In-scope article type: research article with new data (or protocol / systematic review with meta-analysis) | met | Retrospective simulation with methods, results, tables and figures. Not a narrative review, commentary, case report, standalone protocol, or tool announcement. |
| Computational / public-data studies accepted if they are full research papers with methods and results | met, with a note | FAQ: computational papers are welcome when they are full research papers; "simple automated/computational analyses of public data" are generally not sufficient. This paper has a pre-specified question, a calibrated simulator, two data sources, a failed validation, and planned comparisons. That is more than a simple re-tabulation, but a screener could still ask. The cover note states that it is a complete research article. |
| Teaching / instructive materials are out of scope | met (applied 14 November 2026) | "Educational analysis" and "This is a learning exercise" were removed. Running header is now "Not clinical or ordering advice." Draft banner is now "This is not a clinical tool, not blood-bank ordering advice and not a recommendation for any hospital. Nothing here should be used to decide whether a patient receives a unit, or how many units a real blood bank should order or keep." Supplement banner is now "This is not a clinical tool and not ordering advice." Affiliation remains Independent researcher. |
| Must not give clinical or public-health advice that could cause harm; not dual-use | met | Title page and running header say it is not a clinical tool and not ordering advice. No infectious-disease or immunization claims. medRxiv will also stamp posted PDFs with its own "not for clinical decision-making" notice. |
| English language | met | Entire manuscript is in English. |
| Title, author names and affiliations, and abstract on the title page | met | Layout PDF page 1. |
| Single PDF of text, tables and figures, or Word plus figures; LaTeX not accepted as source | met | `draft_v11_layout.pdf` is a complete letter-size PDF. Separate figure files are not needed. |
| Line numbers | met (not required) | Help mentions line numbers only as a WordPerfect conversion warning. None added. |
| Supplement as a separate file | met | `supplement_v11_layout.pdf`. |
| Abstract in both the form and the PDF | met | 250 words; same text in source and PDF. No official medRxiv word limit found. This also meets the *Transfusion Medicine* cap of 250 words. |
| Author identity and contact | met | Liam Dixon; Independent researcher; Medical Laboratory Technician; dixonlj1993@gmail.com; ORCID 0009-0003-0610-197X. |
| Affiliation as an independent author | met in the paper; possible screening issue | The byline is "Independent researcher," which is accurate. Do not add an employer. openRxiv's 20 October 2026 AI note says authors must be "affiliated with an organization to which we can turn if there are allegations of fraud or misconduct." That may be applied at screening. It cannot be fixed by inventing an institution. |
| Institutional email recommended | note only | openRxiv recommends an institutional email, or adding one as a second email. Use the Gmail address already on the paper. Do not use an employer email. |
| Co-author approval | met | Sole author. Form answer: yes, I approve. |
| License selected by the author | met (CC-BY chosen) | Menu confirmed: No reuse; CC-BY-NC-ND; CC-BY-ND; CC-BY-NC; CC-BY; CC0. Author decision 14 November 2026: select **CC-BY** (CC BY 4.0). |
| Competing interest statement | met | Statements in v11. Paste-ready copy in the form-answers file. No employer name. |
| Funding statement | met | "Funding. None." Do not add a funder or grant number. |
| Ethics / IRB statement | met | v11: public, de-identified, aggregate daily counts; no participants; no patient-level data; ethics review and consent not required. This matches the FAQ exception for data that are already openly available. |
| Patient / participant consent | met (not applicable) | No participants, no patient-level data, no photographs, no exact ages or other identifiers. |
| No identifying information | met | Only published hospital-level daily counts (Aachen; Stanford pip example data). |
| Clinical trial registration | met (not applicable) | Not a trial or other prospective interventional study. Do not put the OSF DOI in a trial-ID box. |
| Data availability statement, with links | met | Aachen (CC BY 4.0) and Stanford pip (GPL-2 or later) cited; code and results at https://github.com/dixonlj/Platelet-forecast and https://doi.org/10.5281/zenodo.24237979. |
| Analysis plan / study registration disclosed | met | Retrospective OSF registration, 14 November 2026, https://doi.org/10.17605/OSF.IO/PHQ42, also https://osf.io/phq42/. Timing is in the abstract and the paper. |
| EQUATOR / reporting checklist (STRESS) | met | Not a confirmed upload field on the medRxiv form. The paper says reporting follows STRESS (Monks 2019); the completed checklist is Supplement S8. |
| Generative-AI use disclosed; AI not listed as an author | met (wording approved 14 November 2026) | Full "Use of AI tools" statement in the Statements. Verbatim copy in the form-answers file. The author approved this wording as written. |
| Author contributions | met | In the Statements. Not a confirmed form field; paste if a box appears. |
| Target journal allows preprints | met, as far as the journal pages go | *Transfusion Medicine* (Wiley) considers articles previously available as preprints on non-commercial servers. medRxiv is not named, but is the same kind of non-profit server as bioRxiv in the examples. Declare the preprint later, at journal submission. |
| Article Category dropdown | gap in the public docs | Help confirms the field exists; the option list is not published. Pick the original research / research-article option. See form answers. |
| Exact labels for license, funding, ethics, trial, and co-author approval boxes | gap in the public docs | FAQ confirms these are collected; help does not name the boxes or the page. Answers are grouped in form-answers Step 4. |

---

## Self-review: form answers checked against draft v11

Every paste value in `medrxiv_form_answers.md` was compared with `paper/draft_v11.src.md` and `paper/draft_v11_layout.pdf`. Results:

| Form answer | v11 source | Result |
|---|---|---|
| Title (24 words, 165 characters) | YAML `title` and PDF title page | Match. |
| Short title, if asked: "Platelet forecasts versus a standing order." | Title-page running title | Match (43 characters including the period). |
| Abstract, 250 words, structured headings Objectives / Background / Methods/Materials / Results / Conclusion | `# Abstract` in the source; PDF Abstract | Source word count is 250. PDF text is the same, except a page-2 running header sits in the middle of the PDF text extract; the words of the abstract itself are unchanged. Form-safe paste replaces typographic en dashes, minus signs and ≥ with ASCII `-` and `>=` only; no numbers were changed; word count stays 250. |
| Abstract numbers (5.22%, 9.74%, 5.00, 8.82, 0.226, 0.20, 5.30%, −0.33, −0.88, +0.22, −0.12, +0.07, +0.17, 2.47, −3.52, −1.42, 1.40 to 2.29, p ≥ 0.10) | Abstract Results sentence | Match between source and form-safe copy (ASCII equivalents only). |
| Keywords | Line after the abstract | Match: platelet inventory; demand forecasting; waste; simulation; analysis plan; public data. |
| Author name | Title page: Liam Dixon | Match. First name Liam, last name Dixon, no middle name on the paper. |
| Affiliation | "Medical Laboratory Technician, Independent researcher." | Match. Form uses Independent researcher. No employer names in v11 source, supplement source, or this package (search for the forbidden names was clean). |
| Email | dixonlj1993@gmail.com | Match. |
| ORCID | 0009-0003-0610-197X | Match. https://orcid.org/0009-0003-0610-197X resolved (HTTP 200) on 14 November 2026. |
| Number of authors | Sole author | Match (1). |
| Subject Area recommendation: Health Informatics | Not a field in the paper | Judgement, not a v11 string. Hematology and Health Systems and Quality Improvement recorded as alternatives. All three are on the public medRxiv subject list. |
| Article type on the title page ("Original Article (prepared for Transfusion Medicine)") | Title page | Not used as a medRxiv dropdown value, because that menu is unlisted. Flagged in the form answers so it is not pasted into the wrong box. |
| Ethics / consent | Statements, "Ethics approval and patient consent" | Match in substance. Form paste adds the two public data sources by name so a screener can see the "already openly available" exception. |
| Permission to reproduce / clinical trial | Same Statements paragraph: not applicable | Match. |
| OSF registration DOI 10.17605/OSF.IO/PHQ42 and https://osf.io/phq42/ | Title page, Methods 2.1, Statements | Match. https://doi.org/10.17605/OSF.IO/PHQ42 resolved to https://osf.io/phq42/ (HTTP 200). Registered 14 November 2026, retrospectively, after the analyses — this is disclosed. |
| Zenodo / GitHub | "Data and code availability": https://github.com/dixonlj/Platelet-forecast and https://doi.org/10.5281/zenodo.24237979 | Match. GitHub resolved public (HTTP 200). Zenodo was already confirmed live earlier on 14 November 2026 as https://zenodo.org/records/24237979; a later unauthenticated curl from this environment received HTTP 403, which looks like bot blocking, not a new finding that the record is gone. |
| Funding: None | Statements: "Funding. None." | Match. |
| Competing interests | Statements paragraph | Verbatim paste prepared; no employer name. |
| Author contributions | Statements paragraph | Verbatim available if a box appears. |
| AI-use statement | Statements, "Use of AI tools" | Verbatim copy in the form-answers file, including the en dash in "13–14 November 2026." Approved as written on 14 November 2026. |
| STRESS | Methods 2.1 points to Supplement S8 | S8 table is present in supplement v11 (objectives, model, data, runs/seeds, validation, implementation, code access). Code access in S8 now includes the Zenodo DOI. |
| Display items | Title page: 3 tables, 3 figures; Supplement v11 | Match. |
| Filename rules | Help: no symbols or punctuation except hyphen, underscore, and extension | `draft_v11_layout.pdf` and `supplement_v11_layout.pdf` comply. |

---

## Wording fix (applied 14 November 2026)

The no-clinical-advice warning was kept. "Educational analysis" and "This is a learning exercise" were removed from the draft and supplement sources, then all v11 outputs were rebuilt.

- Running header (draft and supplement layout PDFs): `Not clinical or ordering advice.`
- Draft title-page banner: `This is not a clinical tool, not blood-bank ordering advice and not a recommendation for any hospital. Nothing here should be used to decide whether a patient receives a unit, or how many units a real blood bank should order or keep.`
- Supplement title-page banner: `This is not a clinical tool and not ordering advice.`
- Affiliation unchanged: Independent researcher.

Logged in `paper/changes_v10_to_v11.md`. Number check re-run: Part A 64/64 pass.

## Remaining gaps (decisions above are done)

1. **You have to do the account and the final Approve yourself.** This package does not submit anything. Licence is CC-BY; the AI-use statement is approved; the banner and header wording is in the PDFs in this folder.
2. **Independent-researcher affiliation** versus openRxiv's 20 October 2026 note that authors should be affiliated with an organization. This may come up in screening. Affiliation remains Independent researcher. Do not invent an employer affiliation.
3. **GitHub and Zenodo already host the manuscript files.** Mentioned in the cover note. Not a second preprint posting, but a possible automated flag. After this v11 wording update is pushed, the public copies will match the files in this folder (the Zenodo v0.11.0 snapshot will still be the older wording, which is expected until a later versioned release).
4. **Article Category menu and some declaration box labels** could not be confirmed without logging in. Use Step 2 and Step 4 of the form-answers file, and stop if a box is unclear.
