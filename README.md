# Swallowing problems and loneliness in older US adults

Reproducible secondary analysis of NHIS 2025 public-use data among adults aged 65 or older, examining the association between self-reported swallowing problems and frequent loneliness after adjustment for social contact frequency. This cross-sectional study describes associations, not causal effects; swallowing problems are not clinically confirmed dysphagia.

## Manuscript and figures

- [Dysphagia authoring master](outputs/dysphagia/NHIS2025_Dysphagia_Master.docx), with live Zotero citation fields.
- [Anonymous reviewer manuscript](outputs/dysphagia/NHIS2025_Dysphagia_Anonymous.docx) and [separate author information](outputs/dysphagia/NHIS2025_Dysphagia_Author_Information.docx).
- [Journal figures](outputs/dysphagia/figures/), [supplementary figures](outputs/dysphagia/ESM1.pdf) and [supplementary tables](outputs/dysphagia/ESM2.xlsx).
- [Submission notes](outputs/dysphagia/Submission_notes.txt) and [journal package instructions](outputs/dysphagia/README.md).
- [English figure gallery and captions](outputs/figures_en/README.md).

Anel Karisik's competing-interest declaration, study-specific author contributions and the applicable local ethics determination remain to be supplied or confirmed. No manuscript has been submitted or accepted. This repository is public, including its author materials; use the separate anonymous copy for reviewer-facing submission files.

## Reproduce the analysis

Download and extract [NHIS2025_Complete_Project.zip](NHIS2025_Complete_Project.zip). It preserves the full project tree, including supplementary results, literature records and manuscript-building inputs that are not all expanded in the repository. **It contains no original respondent data.**

On Windows, install R and run from the extracted project root:

```powershell
./RunAll.ps1 -Rscript 'C:/Program Files/R/R-4.6.0/bin/Rscript.exe'
```

The launcher downloads missing data and documentation directly from the CDC, checks fixed SHA-256 hashes, installs missing R packages locally, and runs the original and supplementary analyses and English figures. Downloads go to `work/raw/` and `work/docs/`; derived individual-record data stay under `work/`. These data are excluded from version control. The downloader stops if a source file differs from the recorded version.

For other operating systems, download and extract the two data archives below into `work/raw/` and obtain the three documents listed in `outputs/04_Download_und_Start.ps1` under `work/docs/`. Install `survey`, `mitools` and `pdftools`, then run from the extracted project root:

```sh
Rscript outputs/02_Analyse.R
Rscript outputs/10_Extended_Analysis.R
Rscript -e "source('outputs/05_Bericht.R', encoding='UTF-8')"
Rscript -e "source('outputs/08_Figures_EN.R', encoding='UTF-8')"
Rscript outputs/12_Extended_Figures_EN.R
```

The original environment used R 4.6.0, survey 4.5 and mitools 2.7. Package installation is not version-locked; consult the recorded session information. Manuscript regeneration is separate from statistical reproduction; see [manuscript source instructions](outputs/manuscript_sources/README.txt) and [validation status](VALIDATION_STATUS.txt).

## Original data and terms

| Source | Contents |
|---|---|
| [CDC Adult CSV ZIP](https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adult25csv.zip) | 24,215 adults; 577 variables |
| [CDC imputed-income CSV ZIP](https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adultinc25csv.zip) | Ten income imputations per adult |
| [CDC documentation](https://www.cdc.gov/nchs/nhis/documentation/2025-nhis.html) | Codebooks and survey methods |

Source notes and checksums are retained under `outputs/source_data/` in the complete archive. Original CSVs and ZIPs are downloaded from the CDC rather than distributed in the current project package. Earlier Git revisions retain the previous archive; history has not been rewritten.

The [NCHS Data User Agreement](https://www.cdc.gov/nchs/policy/data-user-agreement.html) applies, including statistical use only and no attempted identification or linkage to individually identifiable records. No new license is applied to CDC materials. No project-wide license has been assigned to the original code or manuscript; see [RIGHTS.md](RIGHTS.md).

## Project guide

- `outputs/01_Analyseplan.txt` and `09_Analyseplan_Nachtrag.txt`: original plan and later supplementary-analysis plan.
- `outputs/02_Analyse.R` and `10_Extended_Analysis.R`: main and supplementary analyses, using the survey design and all ten income imputations.
- `outputs/tables/` and, in the complete archive, `outputs/extended_tables/`: aggregate results and diagnostics.
- `outputs/dysphagia/`: current journal manuscript and submission materials.
- `outputs/manuscript_sources/` and `outputs/literature/`: manuscript builders and reference metadata; additional inputs are in the complete archive.
- `FILE_MANIFEST.tsv`: checksums for every complete-archive entry except the manifest itself.

Original German plans and audit records are retained. See the manuscript and analysis plans for missing-data assumptions, sensitivity analyses and other limitations.
