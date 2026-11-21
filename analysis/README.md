# Statistical analysis

These scripts reproduce the analyses in **Self-Reported Swallowing Problems Are Associated With Frequent Loneliness in Older US Adults**.

## Models

All models include swallowing problems as the exposure. The common sample comprises 7,636 self-responding adults aged 65 years or older with complete exposure, outcome and non-income covariate responses. All ten official NHIS income imputations are used.

| Model | Additional adjustment |
| --- | --- |
| M0 | None |
| M1 | Age group, sex, education, income-to-poverty ratio, married/cohabiting status and living alone |
| M2 | Mobility, hearing and vision difficulties; stroke; dementia; memory/concentration difficulties; myocardial infarction; COPD/current asthma; arthritis; diabetes; cancer excluding nonmelanoma skin cancer |
| M3, primary | In-person contact, telephone/video contact, religious-service attendance and group participation |
| M4 | Daily or weekly depressive feelings |

Models are cumulative. Each chronic condition is represented by a separate indicator. Communication difficulty is assessed separately in matched-sample sensitivity analyses. Voice, speech, communication and severity measurements do not restrict the main sample.

## Reproduction

Run these commands from the repository root:

```sh
python analysis/00_Download_Public_Data.py
Rscript analysis/RunAnalysis.R --independent
```

The Python downloader uses only the standard library, downloads the original public-use files from the CDC and verifies their SHA256 checksums. It places the CSVs in `work/raw/`. Source URLs and checksums are recorded in `results/source_checksums.json`.

Required R packages are `survey` and `mitools`. The analysis was run with R 4.5.0, survey 4.4.2 and mitools 2.4; exact session information is in `results/R_session_info.txt`. Omit `--independent` to skip the additional independent reconstruction and refit. All temporary R objects are written to `work/analysis/`.

The runner executes:

1. `01_Models.R`: source-data checks, variable coding, analytic samples, main models, severity and sensitivity models, full coefficients and diagnostics.
2. `02_Descriptives_Robustness.R`: descriptive tables, predictive margins, response weighting and cumulative-threshold analyses.
3. `03_Validate.R`: internal consistency checks.
4. `90_Independent_Validation.R` when requested: independent predictor reconstruction and ten-imputation M3 refit, plus logistic predictive-margin checks.

## Results

`results/tables/` contains the model estimates, complete coefficient tables, sample flow, variable missingness, design diagnostics and manuscript inputs. `results/extended_tables/` contains survey-logistic standardized prevalences and contrasts, response-weighted estimates, descriptive results and ordinal diagnostics. Workbook values are generated from these aggregate tables.

The survey design is specified in the complete adult sample before domain restriction. It uses NHIS weights, public-use strata and nested primary sampling units. Regression coefficients and covariance matrices are combined across ten income imputations using Rubin's rules with finite design degrees of freedom. The standardized prevalences use survey-weighted logistic models and design-based uncertainty.

M4 contains 40 nonintercept parameters for 396 outcomes (9.90 outcomes per parameter). Model convergence, sparse categories, coefficient estimability and covariance matrices are checked; the modest number of outcomes remains relevant to interpretation. Some Poisson fitted values exceed one, so absolute probabilities are estimated using logistic models.

All analyses describe cross-sectional associations. Changes between models do not quantify mediation or establish causal effects. The ordinal diagnostic family uses Bonferroni adjustment; supplementary confidence intervals otherwise describe uncertainty without a global multiplicity adjustment.
