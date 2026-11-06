param([string]$Rscript = 'C:/Program Files/R/R-4.6.0/bin/Rscript.exe')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (!(Test-Path -LiteralPath $Rscript)) { throw 'Rscript executable not found; supply its path using -Rscript.' }
# The complete archive stores original data once under outputs/source_data.
# Restore the canonical paths expected by the original scripts before validation.
New-Item -ItemType Directory -Force work/raw | Out-Null
foreach ($name in @('adult25.csv','adult25csv.zip','adultinc25.csv','adultinc25csv.zip')) {
    $rawTarget = Join-Path 'work/raw' $name
    $rawSource = Join-Path 'outputs/source_data' $name
    if (!(Test-Path -LiteralPath $rawTarget)) {
        if (!(Test-Path -LiteralPath $rawSource)) { throw "Missing original data file: $rawSource. Extract the complete project archive first." }
        Copy-Item -LiteralPath $rawSource -Destination $rawTarget
    }
}
& ./outputs/04_Download_und_Start.ps1 -Rscript $Rscript
if ($LASTEXITCODE -ne 0) { throw 'Original analysis failed.' }
& $Rscript outputs/10_Extended_Analysis.R
if ($LASTEXITCODE -ne 0) { throw 'Supplementary analysis failed.' }
& $Rscript -e "Sys.setlocale('LC_ALL','English_United States.utf8'); source('outputs/08_Figures_EN.R',encoding='UTF-8')"
if ($LASTEXITCODE -ne 0) { throw 'English figure generation failed.' }
& $Rscript outputs/12_Extended_Figures_EN.R
if ($LASTEXITCODE -ne 0) { throw 'Supplementary English figure generation failed.' }
Write-Output 'Original and supplementary analyses and English figures completed.'
