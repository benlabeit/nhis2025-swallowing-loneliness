# Swallowing problems and loneliness among older adults: NHIS 2025

Reproducible secondary analysis of public-use National Health Interview Survey
(NHIS) 2025 data among adults aged 65 years or older. The primary question is
whether self-reported swallowing problems are associated with frequent loneliness
after adjustment for measured social contact frequency.

The study is cross-sectional. Swallowing problems are self-reported and are not
clinically confirmed dysphagia. Estimates describe associations, not causal effects.

## Project contents

- `outputs/01_Analyseplan.txt`: the original analysis plan, saved before the original cross-tabulations and regression models.
- `outputs/02_Analyse.R`: original preparation, feasibility checks and survey-weighted main/sensitivity analyses.
- `outputs/09_Analyseplan_Nachtrag.txt`: dated plan for supplementary analyses, after the original results were known.
- `outputs/10_Extended_Analysis.R`: additional analyses, including predictive margins, missing-data sensitivity and descriptive precision checks.
- `outputs/tables/` and `outputs/extended_tables/`: machine-readable results.
- `outputs/figures_en/`: English PNG, SVG and PDF figures, captions and source inputs.
- `outputs/08_Figures_EN.R`: reproducible English figure generator.
- `outputs/literature/`: verified reference metadata and search documentation.
- `outputs/source_data/`: convenient user-facing copies of the downloaded public-use data.
- `work/raw/`: canonical raw CSV files and original CDC ZIP archives used by the analysis scripts.
- `work/docs/`: official CDC codebook and methodological documents.
- `FILE_MANIFEST.tsv`: SHA-256 checksums for copied analysis artifacts.

Final manuscript files are added to `outputs/` when the statistical and citation
checks are complete. Their filenames and status should be checked there; this
README does not imply that a draft has been submitted or peer reviewed.

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

Raw files are unchanged. The source CSV copies in `outputs/source_data/` and
`work/raw/` contain the same bytes; the duplicated paths preserve the original
reproduction scripts while making the source tables easy to locate. The original
download script checks archive/document hashes and stops if CDC replaces a file
with another version.

## Reproduce on Windows

Requirements: R, internet access for any missing packages/files, and PowerShell.
The recorded original environment used R 4.6.0, survey 4.5 and mitools 2.7. Exact
session records are provided with the results. The package installation is not
version-locked; preserve the recorded environment for strict long-term replication.

From the repository root:

```powershell
./RunAll.ps1 -Rscript 'C:/Program Files/R/R-4.6.0/bin/Rscript.exe'
```

This verifies/downloads official files, installs required R packages locally under
`work/R-library/`, runs the original analysis and report, then the supplementary
analysis and English figure generator. It recreates `work/prepared.rds` before
the supplementary script reads it. Run from the repository root, since the
original scripts intentionally use relative `outputs/` and `work/` paths.

For another operating system, provide the same source files under `work/raw/`
and `work/docs/`, install `survey`, `mitools` and `pdftools`, and execute:

```sh
Rscript outputs/02_Analyse.R
Rscript outputs/10_Extended_Analysis.R
Rscript -e "source('outputs/05_Bericht.R', encoding='UTF-8')"
Rscript -e "source('outputs/08_Figures_EN.R', encoding='UTF-8')"
```

Figure scripts read saved results; they do not refit models. The figure captions
explain their denominators and distinguish prevalence ratios from odds ratios.
Local package caches, application credentials, temporary renderings and binary
intermediate analysis objects are not tracked.

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
