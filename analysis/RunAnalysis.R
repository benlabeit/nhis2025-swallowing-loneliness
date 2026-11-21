# Run from the repository root with the original public-use CSVs in work/raw/.
stopifnot(file.exists('work/raw/adult25.csv'),file.exists('work/raw/adultinc25.csv'))
for(pkg in c('survey','mitools')) if(!requireNamespace(pkg,quietly=TRUE)) stop('Install package: ',pkg)
for(script in c('01_Models.R','02_Descriptives_Robustness.R','03_Validate.R')) {
  cat('Running', script, '\n')
  source(file.path('analysis', script),local=.GlobalEnv)
}
if('--independent' %in% commandArgs(trailingOnly=TRUE)) {
  source(file.path('analysis','90_Independent_Validation.R'),local=.GlobalEnv)
}
cat('Analysis and consistency checks completed.\n')
