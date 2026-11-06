# Swallowing problems and loneliness among older adults: NHIS 2025

Reproducible secondary analysis of public-use National Health Interview Survey
(NHIS) 2025 data among adults aged 65 years or older. The primary question is
whether self-reported swallowing problems are associated with frequent loneliness
after adjustment for measured social contact frequency.

The study is cross-sectional. Swallowing problems are self-reported and are not
clinically confirmed dysphagia. Estimates describe associations, not causal effects.

## Start with the complete archive

Download `NHIS2025_Complete_Project.zip` and extract it before running the project.
The archive contains the complete folder tree, original data, analysis code,
results, literature records, HTML manuscript, actual Zotero citation data and figure files. The
expanded files displayed at the top level of the GitHub repository are a selected
convenience view; they are not a substitute for extracting the complete archive.

Open `outputs/NHIS2025_Manuscript_EN.html` as the primary manuscript deliverable.
Its content and Zotero-rendered references have been reviewed. The editable Word
version is withheld from the archive until Word layout review can be completed;
it will be added after that check. Read `VALIDATION_STATUS.txt` inside the archive
for the current Word-layout and Zotero-refresh status. HTML review does not
constitute a Word application-level Refresh or pagination test.

## Project contents

- `outputs/01_Analyseplan.txt`: the original analysis plan, saved before the original cross-tabulations and regression models.
- `outputs/02_Analyse.R`: original preparation, feasibility checks and survey-weighted main/sensitivity analyses.
- `outputs/09_Analyseplan_Nachtrag.txt`: dated plan for supplementary analyses, after the original results were known.
- `outputs/10_Extended_Analysis.R`: additional analyses, including predictive margins, missing-data sensitivity and descriptive precision checks.
- `outputs/tables/` and `outputs/extended_tables/`: machine-readable results.
- `outputs/figures_en/`: English PNG, SVG and PDF figures, captions and source inputs.
- `outputs/08_Figures_EN.R`: reproducible English figure generator.
- `outputs/12_Extended_Figures_EN.R`: supplementary English figure generator.
- `outputs/literature/`: verified reference metadata and search documentation.
- `outputs/source_data/`: canonical, unchanged downloaded public-use CSV files and CDC ZIP archives.
- `outputs/NHIS2025_Manuscript_EN.html`: primary English manuscript, with references rendered by Zotero.
- `outputs/NHIS2025_Manuscript_EN.docx`: added only after Word layout review; not included while that review is pending.
- `outputs/manuscript_sources/`: manuscript content, builder and Zotero project script.
- `work/raw/`: created by `RunAll.ps1` from the canonical source files when needed; omitted from the archive to avoid duplicated data.
- `work/docs/`: official CDC codebook and methodological documents.
- `FILE_MANIFEST.tsv`: SHA-256 checksums for every archived file other than the manifest itself.

The original German report covers the first analysis stage. Consult
`outputs/11_Extended_Results.txt` and `outputs/extended_tables/` for the subsequent
analyses. Some original plans and audit material remain in German to preserve
the analysis record. No draft has been submitted or peer reviewed.

## Data provenance

Official landing page:
<https://www.cdc.gov/nchs/nhis/documentation/2025-nhis.html>

Original files:

| File | Contents |
|---|---|
| `adult25csv.zip` / `adult25.csv` | Sample Adult 2025 public-use data: 24,215 rows and 577 columns |
| `adultinc25csv.zip` / `adultinc25.csv` | Ten official family-income imputations for each Sample Adult |
| `adult-codebook.pdf` | Adult variable definitions, universes, missing codes and reference frequencies |
| `srvydesc-508.pdf` | Survey design and analytic guidance |
| `income-techdoc.pdf` | Official income-imputation methods |

Raw files are unchanged and stored once in `outputs/source_data/`. `RunAll.ps1`
copies missing raw files into `work/raw/`, preserving the paths expected by the
original reproduction scripts. The original download script then checks
archive/document hashes and stops if CDC replaces a file with another version.

## Reproduce on Windows

Requirements: R, internet access for any missing packages/files, and PowerShell.
The recorded original environment used R 4.6.0, survey 4.5 and mitools 2.7. Exact
session records are provided with the results. The package installation is not
version-locked; preserve the recorded environment for strict long-term replication.

From the repository root:

```powershell
./RunAll.ps1 -Rscript 'C:/Program Files/R/R-4.6.0/bin/Rscript.exe'
```

This first copies any missing original data from `outputs/source_data/` to
`work/raw/`. It verifies/downloads official files, installs required R packages
locally under `work/R-library/`, runs the original analysis and report, then the
supplementary analysis and both English figure generators (`08_Figures_EN.R` and
`12_Extended_Figures_EN.R`). It recreates `work/prepared.rds` before the
supplementary script reads it. Run from the extracted project root, since the
original scripts intentionally use relative `outputs/` and `work/` paths.

For another operating system, provide the same source files under `work/raw/`
and `work/docs/`, install `survey`, `mitools` and `pdftools`, and execute:

```sh
Rscript outputs/02_Analyse.R
Rscript outputs/10_Extended_Analysis.R
Rscript -e "source('outputs/05_Bericht.R', encoding='UTF-8')"
Rscript -e "source('outputs/08_Figures_EN.R', encoding='UTF-8')"
Rscript outputs/12_Extended_Figures_EN.R
```

Figure scripts read saved results; they do not refit models. The figure captions
explain their denominators and distinguish prevalence ratios from odds ratios.
Local package caches, application credentials, temporary renderings and binary
intermediate analysis objects are not tracked.

To build a local editable Word manuscript from the included Zotero export, install `python-docx`
and run `python outputs/manuscript_sources/build_manuscript.py` from the extracted
project root. The builder checks real item keys/URIs and citation sequence. It
does not perform Word/Zotero Refresh or visual pagination review. Any newly
generated Word file still requires those checks before delivery. See
`outputs/literature/Zotero_README.txt` for citation provenance and
`outputs/Manuscript_submission_notes.txt` for author-supplied submission details.
The Zotero developer script contains the original local project path; update
that path for another installation before running it inside Zotero. It is not
needed to use the included citation export and rebuild the manuscript.

## Statistical principles

- Define the full Sample Adult survey design before creating analysis domains.
- Use the final annual adult weight, public-use strata and primary sampling units.
- Handle numeric nonresponse codes and structural skips according to the codebook.
- Fit the income-adjusted models separately in all ten official imputations and pool uncertainty.
- Keep the original primary analysis distinct from supplementary analyses planned after its results were known.
- Report sample sizes, uncertainty, missingness and model limitations without claiming causation or publication novelty.

See the analysis plans, full report and supplementary results for the exact
definitions and limitations. A complete-case analysis does not by itself resolve
item nonresponse bias; additional weighting/model checks also depend on assumptions.

## Rights and attribution

Data and CDC documentation are provided by CDC/NCHS, with their original source
and attribution retained. This repository does not assert ownership of CDC/NCHS
materials or apply a new license to those materials. No project-wide open-source
license has yet been assigned to the original code or manuscript. See `RIGHTS.md`.

Repository: <https://github.com/benlabeit/nhis2025-swallowing-loneliness>
