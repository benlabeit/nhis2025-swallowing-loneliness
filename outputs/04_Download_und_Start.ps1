# In PowerShell aus dem Projektordner starten: & ./outputs/04_Download_und_Start.ps1
param([string]$Rscript = 'C:/Program Files/R/R-4.6.0/bin/Rscript.exe')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force work/raw,work/docs,work/R-library | Out-Null
$files = @(
  @('https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adult25csv.zip','work/raw/adult25csv.zip','94D5477FFC3A03E292A3000DA8EB5AD71626AE8032BBAA98C9711B7A3B572570'),
  @('https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adultinc25csv.zip','work/raw/adultinc25csv.zip','861BD254D29A375AE276539EFE73775374F9205E5B4933ACE2F07AA588D42535'),
  @('https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2025/adult-codebook.pdf','work/docs/adult-codebook.pdf','F0C881AF2859DD1F768141DF6F6B7B5F966D3FC5C6CC6688FE30224027C61E91'),
  @('https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2025/srvydesc-508.pdf','work/docs/srvydesc-508.pdf','D8A8CC998BCDEF46D4408EAAF275373702131042F49EFAD9B28E1C87DCF2106C'),
  @('https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2025/NHIS2025-imputation-techdoc-508.pdf','work/docs/income-techdoc.pdf','199153353EC470FECC491512F1D76A2C9F920E89385C72B59A108B70D07F5600')
)
foreach ($f in $files) {
  if (!(Test-Path -LiteralPath $f[1])) { Invoke-WebRequest -Uri $f[0] -OutFile $f[1] }
  if ((Get-FileHash -LiteralPath $f[1] -Algorithm SHA256).Hash -ne $f[2]) { throw "Dateiversion stimmt nicht mit dem analysierten Stand ueberein: $($f[1])" }
}
Expand-Archive -LiteralPath work/raw/adult25csv.zip -DestinationPath work/raw -Force
Expand-Archive -LiteralPath work/raw/adultinc25csv.zip -DestinationPath work/raw -Force
& $Rscript -e ".libPaths(c('work/R-library',.libPaths())); p<-c('survey','mitools','pdftools'); m<-p[!vapply(p,requireNamespace,logical(1),quietly=TRUE)]; if(length(m)) install.packages(m,lib='work/R-library',repos='https://cloud.r-project.org',type='binary')"
if ($LASTEXITCODE -ne 0) { throw 'Paketinstallation fehlgeschlagen' }
& $Rscript outputs/02_Analyse.R
if ($LASTEXITCODE -ne 0) { throw 'Analyse fehlgeschlagen' }
& $Rscript -e "Sys.setlocale('LC_ALL','English_United States.utf8'); source('outputs/05_Bericht.R',encoding='UTF-8')"
if ($LASTEXITCODE -ne 0) { throw 'Berichtserstellung fehlgeschlagen' }
