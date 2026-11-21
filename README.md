# Swallowing problems and loneliness in older US adults

Reproducible secondary analysis of NHIS 2025 public-use data among adults aged 65 or older, examining the association between self-reported swallowing problems and frequent loneliness after adjustment for social contact frequency. This cross-sectional study describes associations, not causal effects; swallowing problems are not clinically confirmed dysphagia.

## Manuscript analysis

- [Methods and reproduction instructions](outputs/revision_2026-11-17/README.md)
- [Main and supplementary figures (1–3 and S1–S3)](outputs/revision_2026-11-17/figures_en/)
- [Supplement S1 — model comparisons and figures](outputs/revision_2026-11-17/NHIS2025_Supplement_S1.pdf)
- [Supplement S2 — aggregate tables and variable definitions](outputs/revision_2026-11-17/NHIS2025_Supplement_S2.xlsx)

To reproduce the manuscript results, extract the two CDC data archives listed below into `work/raw/` and run from the root of this repository with the R packages `survey` and `mitools` installed:

```sh
Rscript outputs/revision_2026-11-17/scripts/RunRevision.R
```

## Original data and terms

| Source | Contents |
|---|---|
| [CDC Adult CSV ZIP](https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adult25csv.zip) | 24,215 adults; 577 variables |
| [CDC imputed-income CSV ZIP](https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adultinc25csv.zip) | Ten income imputations per adult |
| [CDC documentation](https://www.cdc.gov/nchs/nhis/documentation/2025-nhis.html) | Codebooks and survey methods |

Source notes and checksums are retained under `outputs/source_data/` in the complete archive. Original CSVs and ZIPs are downloaded from the CDC rather than distributed in the current project package. Earlier Git revisions retain the previous archive; history has not been rewritten.

The [NCHS Data User Agreement](https://www.cdc.gov/nchs/policy/data-user-agreement.html) applies, including statistical use only and no attempted identification or linkage to individually identifiable records. No new license is applied to CDC materials. No project-wide license has been assigned to the original code or manuscript; see [RIGHTS.md](RIGHTS.md).

## Archived materials

The root-level [complete project archive](NHIS2025_Complete_Project.zip), journal and figure ZIPs, and the materials in [outputs/dysphagia](outputs/dysphagia/) accompany the earlier analysis including proxy interviews. The root-level `RunAll.ps1` reproduces that analysis. The manuscript uses the self-report analysis linked above.
