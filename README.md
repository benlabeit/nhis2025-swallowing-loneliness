# Swallowing problems and loneliness in older US adults

Materials for the initial submission of **Self-Reported Swallowing Problems Are Associated With Frequent Loneliness in Older US Adults**.

This study analyzes the public-use 2025 National Health Interview Survey (NHIS) among self-responding adults aged 65 years or older. The exposure is a swallowing problem during the previous 12 months; the primary outcome is always or usually feeling lonely. Estimates describe cross-sectional associations.

## Manuscript and supporting materials

| Material | Location |
| --- | --- |
| Manuscript with native Zotero citation fields | [Manuscript.docx](manuscript/Manuscript.docx) |
| Manuscript PDF | [Manuscript.pdf](manuscript/Manuscript.pdf) |
| Supplementary tables, figures and methods | [Supplement S1](supplement/Supplement_S1.pdf) |
| Complete numerical results and variable definitions | [Supplement S2](supplement/Supplement_S2.xlsx) |
| Main figures 1–3 | [Main figures PDF](figures/Main_Figures.pdf) |
| Supplementary figures S1–S3 | [Supplementary figures PDF](figures/Supplementary_Figures.pdf) |
| Individual publication graphics in PNG, PDF and SVG | [figures/](figures/) |
| Reproducible analysis scripts | [analysis/](analysis/) |
| Aggregate estimates and diagnostics | [results/](results/) |

## Statistical models

All models use the same 7,636 respondents, including 396 frequent-loneliness outcomes. There are 603 respondents with swallowing problems, including 74 with frequent loneliness. Each model includes the swallowing-problem exposure and retains all covariates from the preceding model.

| Model | Covariates added | PR (95% CI) |
| --- | --- | --- |
| M0 | None | 2.69 (2.02–3.57) |
| M1 | Age, sex, education, income-to-poverty ratio, partnership, living alone | 2.48 (1.92–3.22) |
| M2 | Mobility, hearing and vision difficulties; stroke; dementia; memory/concentration difficulties; myocardial infarction; COPD/current asthma; arthritis; diabetes; cancer excluding nonmelanoma skin cancer | 1.78 (1.36–2.33) |
| M3, primary | In-person and telephone/video contact; religious-service attendance; group participation | 1.72 (1.33–2.23) |
| M4 | Daily or weekly depressive feelings | 1.51 (1.16–1.96) |

The standardized prevalence difference is 3.2 percentage points (95% CI 1.4–5.0) in M3 and 2.4 percentage points (0.7–4.1) in M4. Logistic standardization supplies absolute estimates; its marginal PRs can differ from the Poisson PRs above.

## Reproduce the analyses

Requirements: Python 3 for downloading the public data; R with the `survey` and `mitools` packages for the statistical analyses. The calculations used R 4.5.0, survey 4.4.2 and mitools 2.4; session information accompanies the results.

Run from the repository root:

```sh
python analysis/00_Download_Public_Data.py
Rscript analysis/RunAnalysis.R
```

The download script obtains the two original CDC CSV archives, verifies their SHA-256 checksums and places the CSVs in `work/raw/`. The R scripts use the NHIS weights, public-use strata and primary sampling units, fit each model in all ten official income imputations, and combine estimates using Rubin's rules with finite survey degrees of freedom. They regenerate the numerical tables in `results/`.

The Excel supplement is a formatted report of the calculated results. Its numerical source tables are provided in TSV format. Figure and supplementary-PDF generation is implemented in `analysis/BuildFigures.py` using standard Python packages, including matplotlib, pandas, reportlab, pypdf and Pillow.

## Data and rights

| Source | Contents |
| --- | --- |
| [NHIS Sample Adult CSV archive](https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adult25csv.zip) | 24,215 adults; 577 variables |
| [NHIS imputed-income CSV archive](https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adultinc25csv.zip) | Ten official income imputations per adult |
| [CDC documentation](https://www.cdc.gov/nchs/nhis/documentation/2025-nhis.html) | Questionnaires, codebooks and survey methods |

Original respondent data are obtained directly from the CDC. The repository contains aggregate results. Source checksums and recoding definitions accompany the analysis scripts. See [RIGHTS.md](RIGHTS.md) for attribution and data-use information.
