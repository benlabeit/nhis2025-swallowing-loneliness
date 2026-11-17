# Run from repository root with adult25.csv and adultinc25.csv in work/raw/.
stopifnot(file.exists('work/raw/adult25.csv'),file.exists('work/raw/adultinc25.csv'))
for(pkg in c('survey','mitools')) if(!requireNamespace(pkg,quietly=TRUE))stop('Install required package: ',pkg)
rscript<-file.path(R.home('bin'),if(.Platform$OS.type=='windows')'Rscript.exe' else 'Rscript')
base<-'outputs/revision_2026-11-17/scripts'
for(script in c('02_Analyse.R','10_Extended_Analysis.R','20_Expanded_Adjustment.R','21_Manuscript_Tables.R','08_Figures_EN.R','12_Extended_Figures_EN.R','30_Validate.R')) {
 cat('Running',script,'\n')
 status<-system2(rscript,shQuote(file.path(base,script)))
 if(status!=0)stop('Failed: ',script)
}
cat('Revision analyses, figures and validation completed. See README for artifact rebuilding.\n')
