# Small aggregate tables used by the manuscript builder. Run from repository root.
d<-readRDS('work/revision_2026-11-17/prepared.rds')
inc<-read.csv('work/raw/adultinc25.csv',colClasses=c(HHX='character'))
od<-'outputs/revision_2026-11-17'
put<-function(x,n)write.table(x,file.path(od,paste0(n,'.tsv')),sep='\t',row.names=FALSE,quote=FALSE)
defs<-list(age65=d$agegrp=='65-74',age75=d$agegrp=='75-84',age85=d$agegrp=='85+',female=d$sex=='2',edu1=d$education=='lt_HS',edu2=d$education=='HS',edu3=d$education=='some_college',edu4=d$education=='BA_plus',partner=d$partner==1,alone=d$alone==1,mobility=as.numeric(d$mobility)>1,hearing=as.numeric(d$hearing)>1,stroke=d$stroke==1,contact1=d$contact1=='0',contact2=d$contact2=='0',depression=d$depression==1,proxy=d$PROXYFLAG_A==1)
rows<-list()
for(a in 0:1)for(nm in names(defs)) {
 ix<-d$cc4 & d$swallow %in% a & !is.na(defs[[nm]])
 rows[[length(rows)+1]]<-data.frame(variable=nm,swallow=a,n=sum(ix),count=sum(defs[[nm]][ix]),percent=100*weighted.mean(defs[[nm]][ix],d$WTFA_A[ix]))
}
put(do.call(rbind,rows),'manuscript_table1')
facts<-c(eligible_self=sum(d$older),numeric_self=sum(d$older & !is.na(d$age)),fallback_self=sum(d$older & is.na(d$age)),income_imputed=sum(d$cc4 & d$IMPINCFLG_A %in% 1:2),income_imputed_percent=100*mean(d$IMPINCFLG_A[d$cc4] %in% 1:2),self_valid_both=sum(d$older & complete.cases(d[c('swallow','lonely')])) )
put(data.frame(fact=names(facts),value=unname(facts)),'manuscript_facts')
stopifnot(sum(d$cc4)==7829,sum(d$lonely[d$cc4])==411,sum(d$older)==8204)
cat('Manuscript table checks passed.\n');print(facts)
