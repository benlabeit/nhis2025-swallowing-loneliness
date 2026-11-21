# Self-report primary analysis and expanded adjustment

The primary descriptive and regression analyses use interviews answered by the participants themselves. Regression estimates account for the survey design and pool all ten official income imputations.

The primary sample is 7,829 self-respondents (411 frequent-loneliness events), compared with 8,094 when proxies are included. The primary PR is 1.99 (95% CI 1.55–2.56). The expanded complete sample is 7,658 self-respondents; its fully adjusted PR is 1.68 (1.30–2.19). These are cross-sectional associations, not causal effects.

## Results

- [Supplement S1](NHIS2025_Supplement_S1.pdf): sequential models, cumulative adjustment blocks, comparison exposures and supplementary figures.
- [Supplement S2](NHIS2025_Supplement_S2.xlsx): aggregate tables, coefficients, missingness and definitions.
- [Main and supplementary figures](figures_en/).
- [Primary results](tables/model_results.tsv), [expanded results](expanded_adjustment.tsv), and [absolute estimates](extended_tables/standardized_prevalence_and_contrasts.tsv).
- [Validation](validation.txt) and session information in `03_R_SessionInfo.txt`, `expanded_session.txt` and `extended_tables/session_info.txt`.

The Word manuscript with revisions attributed to Cinja is delivered separately. Existing reviewer comments and the supplied source manuscript are not published in this analysis revision. The builder accepts that original manuscript as a local input and verifies that rejection of all revisions recovers its text and that citation fields and comments remain intact.

## Reproduce

From the repository root, with the original public-use `adult25.csv` and `adultinc25.csv` in `work/raw/`:

```sh
Rscript outputs/revision_2026-11-17/scripts/RunRevision.R
```

Requires `survey` and `mitools`; tested with R 4.5.3, survey 4.5, mitools 2.4. Data download links and checksum verification are documented in the repository README. No individual respondent records are included here. Derived record-level objects remain in ignored `work/revision_2026-11-17/`.

To rebuild document artifacts after the R analysis:

```sh
python outputs/revision_2026-11-17/scripts/build_supplement.py
node outputs/revision_2026-11-17/scripts/build_workbook.mjs
python outputs/revision_2026-11-17/scripts/build_tracked_manuscript.py /path/to/NHIS2025_JAGS_Manuscript_SSK.docx
```

The PDF builder requires reportlab and pypdf; the manuscript builder requires lxml. The workbook builder uses `@oai/artifact-tool`. Rendering and final visual review are separate from statistical reproduction. The manuscript builder is specific to the supplied SSK document and fails validation if its expected content has changed.

## Analysis choices

- Primary restriction: `PROXYFLAG_A=2`; the full adult survey design is constructed before domain restriction. Including proxies remains a sensitivity analysis.
- Age eligibility retains the original AGE65 fallback for descriptive statistics. Exact age is still required for regression.
- The common primary sample retains complete participation variables so M0–M4 can be compared on identical respondents.
- The response-propensity analysis is restricted to 8,180 self-respondents with numerical age. Proxy status is constant and is omitted from that response model.
- Expanded adjustment adds dementia, cognition and communication, then vision, then a custom comorbidity score. Difficulty variables use three categories. The common expanded sample also requires valid comparison exposures.
- The custom score uses myocardial infarction, COPD/current asthma, broad arthritis and diabetes (one point each), and cancer other than nonmelanoma-only skin cancer (two). Stroke and dementia remain separate. This is not a validated Charlson index; the arthritis item includes noninflammatory disease.
- Structural skips are handled separately from missing/unknown responses. Other cancer (`OTHERCANP_A`) is included. A documented qualifying malignancy contributes two points, including when reported alongside nonmelanoma skin cancer. Nonmelanoma skin cancer alone contributes zero. Skin cancer of unknown type without a documented qualifying malignancy leaves the component missing. Sex-specific cancer indicators are evaluated within their questionnaire universe.
- Voice, speech and vision replace the exposure in comparison models; vision is removed as a covariate when it is the exposure. These are exploratory comparisons, not negative controls. Communication adjustment can particularly affect speech associations. No formal test of differences between exposure coefficients was performed.
- Sensitivities omit communication adjustment or arthritis scoring, use the M3-available sample, and add depressive feelings on a matched sample.
