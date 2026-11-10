param([string]$Rscript = 'C:/Program Files/R/R-4.6.0/bin/Rscript.exe')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (!(Test-Path -LiteralPath $Rscript)) { throw 'Rscript executable not found; supply its path using -Rscript.' }
# Download and verify official CDC sources before running analyses.
& ./outputs/04_Download_und_Start.ps1 -Rscript $Rscript
if ($LASTEXITCODE -ne 0) { throw 'Original analysis failed.' }
& $Rscript outputs/10_Extended_Analysis.R
if ($LASTEXITCODE -ne 0) { throw 'Supplementary analysis failed.' }
& $Rscript -e "Sys.setlocale('LC_ALL','English_United States.utf8'); source('outputs/08_Figures_EN.R',encoding='UTF-8')"
if ($LASTEXITCODE -ne 0) { throw 'English figure generation failed.' }
& $Rscript outputs/12_Extended_Figures_EN.R
if ($LASTEXITCODE -ne 0) { throw 'Supplementary English figure generation failed.' }
Write-Output 'Original and supplementary analyses and English figures completed.'
