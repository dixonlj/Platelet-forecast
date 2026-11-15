# medRxiv form answers (prep only — do not submit)

Paste these answers into the medRxiv submission system yourself. This folder is preparation only. No account was created here, and nothing has been submitted.

**Decisions recorded 14 November 2026 (America/New_York):** the title-page banner and running header no longer use "Educational analysis" or "This is a learning exercise" (the no-clinical-advice warning stays); the licence to select is **CC-BY**; the AI-use statement is approved as written; affiliation remains Independent researcher.

**How this list was built.** Field names and step order below come from medRxiv's public help and policy pages, retrieved on 14 November 2026 (America/New_York):

- Submission guide: https://www.medrxiv.org/submit-a-manuscript
- FAQ: https://www.medrxiv.org/about/FAQ
- Submission help (BenchPress): https://submit.medrxiv.org/help/submissionhelp.dtl
- Screening procedures: https://connect.medrxiv.org/news/2022/06/13/screening_procedures
- Subject collections: https://www.medrxiv.org/collection/%2A
- About medRxiv: https://openrxiv.org/about-medrxiv/
- Funder field note: https://openrxiv.org/updating-funder-information/ (3 September 2026)
- License options: FAQ plus https://openrxiv.org/preprint-licensing-updates/ (20 May 2026)
- AI policy: https://openrxiv.org/approach-to-ai/ (20 October 2026)

The live form at https://submit.medrxiv.org/ could not be opened without creating or signing into an account, which this step does not do. Every field below is marked **Confirmed** (exact label or button in the official help/FAQ) or **Unconfirmed label** (the FAQ or a related openRxiv page says this information is collected, but the exact on-screen label and which page it sits on are not published). If the live form shows a field that is not listed, use the matching statement from the Declarations section rather than inventing text. Do not enter any employer name.

Colored fields on the form are required. You can use **Save/Continue** to stop mid-way; the draft then sits in **Submissions/Revisions in Progress** until files are uploaded. Use **Reset Form** only if you want to clear the page and start that step again.

---

## Step 0. Create an account and open the Author Area

Do this yourself at https://submit.medrxiv.org/. There is no fee.

**Confirmed** buttons and labels on the login page:

| Field / button | Paste or action |
|---|---|
| Email | dixonlj1993@gmail.com |
| Password | (your password; do not store it in this repo) |
| remember my email address | optional |
| Log in | after the account exists |
| Log in with ORCiD | preferred, so the ORCID is linked from the start |
| Create an account with ORCiD | preferred alternative if you have no account yet |
| Create a new account | if you prefer email signup |

ORCID to link: **0009-0003-0610-197X** (https://orcid.org/0009-0003-0610-197X). Cross-checked against draft v11 title page.

openRxiv recommends registering with an institutional email, or adding one as a second email. Use the Gmail address already printed on the paper. Do not use an employer email. If the form asks for a second email and you have no non-employer institutional address, leave it blank.

After login, the home page says: enter the **Author Area** to **Submit a New/Revised Manuscript**.

The **Personal Info Area** can be used later to **Update your Contact Information** and **Update your Expertise Areas**. That is optional and is not part of the manuscript form.

---

## Step 1. Start the submission

**Confirmed** (Submission Help, "General Submission Steps"):

1. Enter the **Author Area**.
2. Click **Submit a new manuscript**.

You will then be taken through this published sequence:

1. Manuscript Metadata
2. Author Information
3. File Upload Metadata
4. Supplemental File Upload
5. Manuscript File Upload
6. Submission Approval
7. Confirmation

The FAQ also says that, after you click "Submit a new manuscript", you "provide article and author metadata, confirm you have approval from all co-authors, select a license, add relevant funding information, ethical approvals (if applicable) and clinical trial registration details (if applicable), and upload your manuscript file(s)." Those extra declaration fields are real, but the help file does not say which page they appear on or what the boxes are called. Answers for them are in Step 4.

---

## Step 2. Manuscript Metadata

**Confirmed** fields, in the order the Submission Help lists them.

### Number of Authors

**1**

(You are the only author. Include yourself. You can change this later on the Author Information page if needed.)

### Article Category

Use the pull-down menu.

**Exact menu options are not published.** The help page only says: "Use the pull-down menu provided to indicate the Article Category for your paper."

Choose the option that means an original **research article / research manuscript with new data**. That is the in-scope type in the FAQ ("Research articles with new data"). Do not choose a review, commentary, opinion, case report, protocol-only, or withdrawal option if any of those appear.

The title page of draft v11 says "Article type: Original Article (prepared for *Transfusion Medicine*)." That is the target-journal category, not a confirmed medRxiv menu label. Do not type that phrase into a dropdown.

### Subject Area

Use the pull-down menu. Only one subject area can be selected (FAQ).

**Recommended: Health Informatics**

Reason: the paper tests whether demand forecasts waste fewer platelet units than a standing order, in a calibrated computer simulation of public daily counts. The methods are forecasting, simulation and inventory rules. That sits most naturally in Health Informatics. The category is on medRxiv's public subject list (https://www.medrxiv.org/collection/%2A).

Close alternatives, if you prefer a transfusion-medicine audience:

- **Hematology** — the clinical setting is platelet supply, but the contribution is the simulation, not a hematologic disease study.
- **Health Systems and Quality Improvement** — a fair third choice, because the outcome is waste and shortage in a blood-bank inventory.

The FAQ notes that subject categories are for feeds, not a formal ontology, and that a paper may fit more than one. Pick one and stay with it.

### Special Characters

Not a data field. If you paste the title, abstract or cover letter and the form garbles en dashes, minus signs or ≥, use the **Special Characters** window on that page and replace them with the codes it lists. A form-safe abstract (ASCII hyphens and `>=`) is provided under Abstract below. The PDF itself can keep the typographic characters.

### Title

Paste exactly (24 words, 165 characters including spaces). Cross-checked against `draft_v11.src.md` YAML title and the PDF title page.

```
Demand forecasts versus a standing order for platelet ordering: a simulation study of public data from two hospitals, with a retrospectively registered analysis plan
```

No special characters in this title.

### Abstract

The abstract you enter here is displayed online. The same abstract is already in the manuscript PDF (required).

**Official medRxiv word limit: none found** on the submit guide, FAQ or help pages as of 14 November 2026. This abstract is **250 words**, which also meets the *Transfusion Medicine* cap of 250. Do not add or cut words.

Cross-checked against draft v11 Abstract (source and layout PDF). Headings: Objectives; Background; Methods/Materials; Results; Conclusion.

**Form-safe version (recommended for the web form).** En dashes, minus signs and ≥ from the PDF are replaced with ASCII `-` and `>=` so the form does not mangle them. Word count remains 250.

```
Objectives. To test, in a pre-specified re-analysis of previously analysed data, whether platelet-use forecasts waste fewer units than a standing order based on last year's use, at matched shortage frequency.

Background. Platelets expire within days; forecasting is often proposed to reduce waste.

Methods/Materials. Simulation of public daily counts from a German university hospital (test years 2012-2018) and two US hospitals (2014-2015). Four forecasts drove a simulation calibrated on 2009-2011. The primary outcome was waste (% of units transfused) at each year's recorded shortage days, forecast minus standing order, Holm-corrected. Per the author's file time stamps, the plan preceded the analyses but was registered afterwards; this order is unverifiable. Comparator and forecasts were chosen after these test years were analysed.

Results. The calibrated simulation failed all three preset checks: waste 5.22% simulated against 9.74% recorded, 5.00 against 8.82 emergency units per shortage day, and a weekday-pattern distance of 0.226 (limit 0.20). At the German hospital (standing order waste 5.30%), no forecast was shown to differ from, or be equivalent to, the standing order: seasonal model -0.33 points (95% confidence interval -0.88 to +0.22), pretrained -0.12, detrended boosting +0.07, boosting +0.17. Exploratory: under the hospital's documented Tuesday-Saturday delivery calendar, the seasonal model wasted 2.47 points less (-3.52 to -1.42). At the US site, estimates favoured the forecasts by 1.40 to 2.29 points but were uncertain after correction (Holm-adjusted p >= 0.10).

Conclusion. No forecast advantage was demonstrated, but this depends on the simulated delivery calendar and on a simulation that failed validation.
```

After pasting, look at the form preview. If it offers a special-character window and you would rather match the PDF typography, you can put the typographic dashes back using that window; do not change any numbers.

### Cover letter

**Unconfirmed as a required field.** The Submission Help mentions "your title, abstract or cover letter" in the Special Characters instructions, which suggests a cover-letter box may appear on this page. The FAQ does not list a cover letter as required. If the box appears, paste the cover note at the end of this file. If it does not appear, you do not need to upload a separate letter.

### Short title / running title (only if a field appears)

**Not a confirmed form field.** The manuscript already has this on the title page. If the form asks for a short title or running title, paste:

```
Platelet forecasts versus a standing order.
```

(43 characters including the period; 6 words.)

### Keywords (only if a field appears)

**Not a confirmed form field.** The manuscript already lists keywords under the abstract. If the form asks for keywords, paste:

```
platelet inventory; demand forecasting; waste; simulation; analysis plan; public data
```

(6 terms.)

### Save/Continue or Reset Form

Click **Save/Continue** when this page is complete.

---

## Step 3. Author Information

**Confirmed** labels from Submission Help.

### Corresponding Author

Please choose one author as the corresponding author.

**Liam Dixon** (the only author). Check the email carefully; the help says it is used for all correspondence.

Email: **dixonlj1993@gmail.com**

### "This is me. Insert my information here"

Check this box on your own author row so the account details fill the required fields. Then check that they match the paper, as follows.

### Lookup

Not needed for your own row if you used "This is me." The **Lookup** button is for filling a co-author from an email address already in the system. There are no co-authors.

### Author details to check or type

The help says "required fields" must be filled for each author, but it does not name those fields one by one. Use these values, which match the draft v11 title page. If a box appears that is not listed, fill only what is true and public; do not invent an institution.

| Likely contents of a required field | Value |
|---|---|
| First / given name | Liam |
| Middle name | (leave blank; none used on the paper) |
| Last / family name | Dixon |
| Full name as on the PDF | Liam Dixon |
| Email | dixonlj1993@gmail.com |
| Affiliation / institution | Independent researcher |
| Department | (leave blank) |
| ORCID iD | 0009-0003-0610-197X |
| Corresponding author | Yes (this is the only author) |

If the form asks for city, state, country, postal code, phone, or street address, enter your own home details. Do not use a hospital or employer address, and do not type any employer name.

If the form forces you to pick an organization from a ROR registry and "Independent researcher" is not in the list, type it as free text if the form allows, or stop and do not attach an employer. See the checklist for the openRxiv affiliation note.

A job title is not required by the published help. The paper byline is: "Medical Laboratory Technician, Independent researcher." Use that wording only if a title or credentials box appears.

### Inserting or Deleting Authors

Leave the author count at **1**.

### Save/Continue or Reset Form

Click **Save/Continue**.

---

## Step 4. License, funding, ethics, trial, and co-author approval

**These are collected during submission (FAQ), but exact field labels and page order are unconfirmed.** They may appear on the metadata page, after the author page, or on a later declarations page. Paste the answers below into the matching box.

### Confirm you have approval from all co-authors

**Yes.** I am the sole author and I approve posting this manuscript on medRxiv.

### License

Authors keep copyright (FAQ). The published menu, using the FAQ labels, is:

1. **No reuse/adaptation without permission**
2. **CC-BY-NC-ND**
3. **CC-BY-ND**
4. **CC-BY-NC**
5. **CC-BY** — selected
6. **CC0** (public-domain dedication; the license-update note says this is mainly for US government / NIH employee work)

**Select: CC-BY** (Creative Commons Attribution 4.0). This is the author's chosen licence as of 14 November 2026. It matches how the Aachen source data are licensed (CC BY 4.0), and the analysis code is already MIT. You can later change a posted preprint to a *less* restrictive license, but not to a more restrictive one.

### Funding information

**None.**

The paper statement, which you can paste if a free-text box appears: `None.`

If the form has **Add another funder** (the label used in the 3 September 2026 openRxiv funder note) or asks for a ROR funder ID or grant number, do not add a funder. There was no funding. Do not list an employer as a funder.

### Ethical approvals (if applicable)

Paste this (same sense as draft v11, "Ethics approval and patient consent"):

```
The study used only public, de-identified, aggregate daily counts that are already openly available. It involved no human participants and no patient-level data, so ethics review and consent were not required. The Aachen data are Multimedia Appendix 1 of Schilling and colleagues (CC BY 4.0). The Stanford data are the example data in the pip package (GPL-2 or later).
```

This follows the medRxiv FAQ: a statement of IRB/ethics-committee oversight is required when human subjects, samples or data were used, **unless the data are already openly available**. Do not cite an online decision tool, an audit body, or an employer committee.

If the form is only yes/no checkboxes, the intended answers are: no IRB approval because the data are already openly available; no participant consent because there were no participants and no patient-level data.

### Clinical trial registration details (if applicable)

**Not applicable.**

This is a retrospective simulation of already public daily counts. It is not a clinical trial and not any other prospective interventional study: it does not assign people to an intervention. OSF registration DOI 10.17605/OSF.IO/PHQ42 is an analysis-plan registration, not a clinical-trial ID. Do not enter the OSF DOI in a trial-ID box.

If a free-text box appears:

```
Not applicable. This is a retrospective simulation study of already public, de-identified daily counts. It is not a clinical trial or other prospective interventional study.
```

### Competing interests (only if a field appears)

**Not named as a separate submission-form field in the help file**, but the submit guide requires a competing-interest statement in the work, and it is already in the PDF. If a box appears, paste this verbatim from draft v11:

```
The author works as a medical laboratory technician in a hospital blood bank. This project was done independently, on personal time and equipment, using only public data. It was not funded, requested, reviewed or endorsed by the author's employer, and no employer data, systems or resources were used. The author declares no financial competing interests.
```

Do not add an employer name.

### Data availability (only if a field appears)

Already in the PDF. If a box appears, paste:

```
The Aachen data are Multimedia Appendix 1 of Schilling and colleagues, used under CC BY 4.0. The Stanford data are the example data in the pip package (GPL-2 or later). The analysis code (MIT licence) and all result files are available at https://github.com/dixonlj/Platelet-forecast and archived on Zenodo https://doi.org/10.5281/zenodo.24237979.
```

### Analysis plan / study registration (only if a field appears, and only if it is not a clinical-trial box)

```
The analysis plan was registered retrospectively on OSF Registries on 14 November 2026, after the analyses were run: https://osf.io/phq42/, https://doi.org/10.17605/OSF.IO/PHQ42.
```

### Use of AI / generative AI (only if a field appears)

If a box appears, paste the verbatim **Use of AI tools** statement from draft v11 (copied again at the end of this file). Please read that statement before you submit. Do not list any AI tool as an author.

---

## Step 5. File Upload Metadata

**Confirmed** labels, in help order.

### Number of Files to Upload

The help says: "The number of manuscript files to upload is always set at 1. You must enter the number of other types of files - supplemental or image - you need to upload." It also says: "If your manuscript file is a complete PDF file with images included, you do not need to send any other files" as *image* files.

| Field | Value |
|---|---|
| Manuscript files | 1 (usually fixed) |
| Image Files | 0 (figures and tables are already inside the manuscript PDF) |
| Supplemental Files | 1 |

### Manuscript File

Upload the single PDF that already contains the text, tables and figures:

**`paper/medrxiv/draft_v11_layout.pdf`**

(16 pages, US letter, title / author / affiliation / abstract are on the title page.) This is the copy to upload. You do not need a separate Word file or separate figure files. Line numbers are not required (the help only notes that WordPerfect line numbers may not survive conversion).

Accepted manuscript formats: Word or PDF preferred. We are using PDF.

### Image Files

Leave empty (count 0). Do not upload separate figures.

### Supplemental Files

Select this option and set the count to **1**. Supplemental files are posted as-is and are not converted into the main PDF.

### Save/Continue or Reset Form

Click **Save/Continue**.

---

## Step 6. Supplemental File Upload, then Manuscript File Upload

**Confirmed** order in the help: supplemental files first, then the manuscript.

### Supplemental File(s)

Upload:

**`paper/medrxiv/supplement_v11_layout.pdf`**

If the form asks you to label the file, use:

```
Supplement v11
```

The help says: "Please label your supplemental file(s). Filenames should not include symbols or punctuation (except hyphen, underscore and file-type extensions)." The filename `supplement_v11_layout.pdf` already follows that rule.

### Upload / Save/Continue

Check the pathname, then **Save/Continue**.

### Manuscript File

Upload **`paper/medrxiv/draft_v11_layout.pdf`**.

### Image File(s)

Leave empty.

### Upload / Save/Continue

Check the pathname, then **Save/Continue**. The system will convert the files to a single proof PDF (the supplement stays separate). You will get an email when conversion is done, then the submission appears in the **Ready to Proof** queue.

---

## Step 7. Submission Approval

**Confirmed** labels.

1. Open the **Ready to Proof** queue in the Author Area.
2. Proof every section and the converted manuscript PDF. The help says to examine it carefully, "because once you approve it, it will be sent on to the screening process."
3. Check each **I approve this section** box when that section is correct.
4. If the converted PDF is wrong, use **Reupload your manuscript**, wait for conversion (the help says this generally takes up to 5 minutes), and proof again.
5. When the PDF is right, click **I approve the conversion of my manuscript**.
6. When every section is proofed, click **Approve**.

**Stop before Approve until you are ready to send the paper for screening.** Clicking **Approve** is the act of submitting. This prep package does not do that, and it is not permission to do that on your behalf.

---

## Step 8. Confirmation

After Approve, the help says your official acknowledgment is sent by email. You can check status any time in the Author Area. Screening typically takes 2–4 days (longer on weekends, holidays, or if staff write back). Manuscripts cannot be embargoed to a chosen posting time. Once posted, a preprint cannot be removed; it can only be withdrawn with a notice, or revised later.

If you must change something after Approve, the help says to contact medrxiv@openrxiv.org or use **Feedback**.

---

## Cover note (paste if a cover letter box appears)

```
This manuscript is an original retrospective simulation study of already public, de-identified, aggregate daily platelet counts from two published sources (University Hospital Aachen and the Stanford pip example data). It is a complete research article with methods and results. It is not a clinical trial, not a protocol, not a narrative review, and not advice for clinical practice or blood-bank ordering. A disclaimer to that effect is on the title page.

The analysis plan was written before the analyses, according to the author's file time stamps, and was registered retrospectively on OSF Registries after the analyses were run (https://doi.org/10.17605/OSF.IO/PHQ42). That timing is disclosed in the abstract and the paper. The simulation failed its own pre-specified calibration checks; this is also reported in the abstract.

Code and result files are archived at https://doi.org/10.5281/zenodo.24237979 and https://github.com/dixonlj/Platelet-forecast. Those archives include a copy of the manuscript files. This work has not been posted on another preprint server and has not been published or accepted by a journal.

The author is an independent researcher. Ethics review was not required because the study used only already openly available data.

The author has read and takes responsibility for the manuscript, including text and code produced with an AI assistant as disclosed in the Statements.
```

---

## AI-use statement (verbatim from draft v11 — approved 14 November 2026)

This is the exact "Use of AI tools" paragraph from `paper/draft_v11.src.md`. It is already in the layout PDF. If the form has an AI box, paste this text. The author approved this wording on 14 November 2026.

```
Grok Bot (an AI assistant app; the app does not report an underlying model version) was used on 13–14 November 2026 in every part of this work. Under the author's direction it drafted the analysis plan, including several locked choices that the author reviewed and accepted (among them the Stanford matching target and minimum meaningful difference); wrote most of the analysis code and ran the analyses (Methods, Section 2.1); searched for and summarised public sources; drafted the manuscript text, tables and figures; and checked the numbers against the result files. A separate AI reviewer bot, run in the same app, reviewed the drafts, and its reviews led to revisions, including this version. The author set the question and the rules (public data only, honest reporting), directed each step, checked the results against the output files, decided which suggestions to accept and takes full responsibility for the content. No AI tool is an author.
```

---

## What you must do yourself

These decisions are already recorded: licence **CC-BY**; AI-use statement approved as written; banner and running header updated in the PDFs in this folder; affiliation remains Independent researcher.

1. Create or sign in to your own account at https://submit.medrxiv.org/ (ORCID login recommended). Do not use an employer email.
2. Fill the form with the answers above, upload the two PDFs in this folder, proof the converted PDF, and click **Approve** only when you are ready to submit.
3. If the live form shows a field that is not listed here, use the matching declaration from this file, or stop and check rather than guessing.

medRxiv will add its own "not certified by peer review / not for clinical decision-making" stamp to posted PDFs. That is expected.
