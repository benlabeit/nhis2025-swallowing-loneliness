# Run from project root: Rscript outputs/02_Analyse.R
# Public-use data only. No output contains individual records.
options(warn=1, survey.lonely.psu='fail')
.libPaths(c('work/R-library', .libPaths()))
library(survey)
library(mitools)
dir.create('outputs/tables', recursive=TRUE, showWarnings=FALSE)
save_table <- function(x, name) write.table(x, paste0('outputs/tables/',name,'.tsv'), sep='\t', row.names=FALSE, quote=FALSE, na='NA')
d <- read.csv('work/raw/adult25.csv', colClasses=c(HHX='character'))
inc <- read.csv('work/raw/adultinc25.csv', colClasses=c(HHX='character'))
stopifnot(nrow(d)==24215L, ncol(d)==577L, !anyDuplicated(d$HHX), all(d$SRVY_YR==2025), all(d$WTFA_A>0), !anyNA(d[c('PSTRAT','PPSU','WTFA_A')]))
stopifnot(nrow(inc)==10*nrow(d), !anyDuplicated(inc[c('HHX','IMPNUM_A')]), setequal(inc$IMPNUM_A,1:10))
# Compare with official full-adult codebook frequencies, before recoding.
stopifnot(sum(d$VSLSWYR_A==1,na.rm=TRUE)==1463, sum(d$LONELY_A==1,na.rm=TRUE)==692, sum(d$VSLSWDIF_A==2,na.rm=TRUE)==264)
valid <- function(x, values) ifelse(x %in% values,x,NA)
d$age <- valid(d$AGEP_A,18:85)
d$older <- (!is.na(d$age) & d$age>=65) | (is.na(d$age) & d$AGE65 %in% 2)
d$agegrp <- factor(ifelse(d$age>=85,'85+',ifelse(d$age>=75,'75-84',ifelse(d$age>=65,'65-74',NA))),levels=c('65-74','75-84','85+'))
d$swallow <- ifelse(d$VSLSWYR_A %in% 1:2, as.integer(d$VSLSWYR_A==1), NA)
d$lonely <- ifelse(d$LONELY_A %in% 1:5,as.integer(d$LONELY_A %in% 1:2),NA)
d$lonely_broad <- ifelse(d$LONELY_A %in% 1:5,as.integer(d$LONELY_A %in% 1:3),NA)
d$severity <- factor(ifelse(d$swallow %in% 0,'none',ifelse(d$swallow %in% 1 & d$VSLSWDIF_A %in% 1,'little',ifelse(d$swallow %in% 1 & d$VSLSWDIF_A %in% 3,'middle',ifelse(d$swallow %in% 1 & d$VSLSWDIF_A %in% 2,'a_lot',NA)))),levels=c('none','little','middle','a_lot'))
d$sex <- factor(valid(d$SEX_A,1:2))
d$education <- factor(ifelse(d$EDUCP_A %in% 1:2,'lt_HS',ifelse(d$EDUCP_A %in% 3:4,'HS',ifelse(d$EDUCP_A %in% 5:7,'some_college',ifelse(d$EDUCP_A %in% 8:10,'BA_plus',NA)))),levels=c('lt_HS','HS','some_college','BA_plus'))
d$partner <- ifelse(d$MARITAL_A %in% 1:3,as.integer(d$MARITAL_A %in% 1:2),NA)
d$alone <- ifelse(d$PCNT18UPTC %in% 1:3 & d$PCNTLT18TC %in% 0:3,as.integer(d$PCNT18UPTC==1 & d$PCNTLT18TC==0),NA)
d$mobility <- factor(ifelse(d$DIFF_A %in% 1:4,pmin(d$DIFF_A,3),NA))
d$hearing <- factor(ifelse(d$HEARINGDF_A %in% 1:4,pmin(d$HEARINGDF_A,3),NA))
d$stroke <- ifelse(d$STREV_A %in% 1:2,as.integer(d$STREV_A==1),NA)
d$depression <- ifelse(d$DEPFREQ_A %in% 1:5,as.integer(d$DEPFREQ_A %in% 1:2),NA)
for(j in 1:4) d[[paste0('contact',j)]] <- factor(valid(d[[paste0('SCONNECT',j,'_A')]],0:3),levels=0:3)
core <- c('lonely','swallow','agegrp','sex','education','partner','alone','mobility','hearing','stroke','contact1','contact2')
d$cc3 <- complete.cases(d[core]) & d$older
d$cc4 <- complete.cases(d[c(core,'contact3','contact4')]) & d$older
d$ccdep <- d$cc4 & !is.na(d$depression)
d$ccself <- d$cc4 & d$PROXYFLAG_A %in% 2
d$ccseverity <- d$cc4 & !is.na(d$severity)
saveRDS(d,'work/prepared.rds')

# Audit: full raw code distributions, including nonresponse and out-of-universe blanks.
rawvars <- c('AGEP_A','AGE65','VSLSWYR_A','VSLSWDIF_A','LONELY_A','SUPPORT_A',paste0('SCONNECT',1:4,'_A'),'SEX_A','EDUCP_A','MARITAL_A','PCNT18UPTC','PCNTLT18TC','DIFF_A','HEARINGDF_A','STREV_A','DEPFREQ_A','PROXYFLAG_A','IMPINCFLG_A')
rawfreq <- do.call(rbind,lapply(rawvars,function(v) {t<-as.data.frame(table(d[d$older,v],useNA='always')); names(t)<-c('code','n'); data.frame(variable=v,t)}))
save_table(rawfreq,'raw_frequencies_65plus')
missing <- do.call(rbind,lapply(c(core,'contact3','contact4','depression','severity'),function(v) data.frame(variable=v,n_65plus=sum(d$older),missing=sum(is.na(d[d$older,v])),percent_missing=100*mean(is.na(d[d$older,v])))))
save_table(missing,'missing_65plus')
skip <- data.frame(check=c('severity_blank_exposure_no','severity_blank_exposure_unknown','severity_invalid_among_exposed','severity_recorded_without_yes'), n=c(sum(d$older & d$swallow %in% 0 & is.na(d$VSLSWDIF_A)),sum(d$older & is.na(d$swallow) & is.na(d$VSLSWDIF_A)),sum(d$older & d$swallow %in% 1 & !(d$VSLSWDIF_A %in% 1:3)),sum(d$older & !(d$swallow %in% 1) & !is.na(d$VSLSWDIF_A))))
save_table(skip,'skip_audit')
stopifnot(skip$n[4]==0)
cross <- function(rows, vars, name) save_table(as.data.frame(do.call(table,c(d[rows,vars,drop=FALSE],list(useNA='ifany')))),name)
cross(d$older,c('swallow','lonely'),'exposure_outcome_65plus')
cross(d$older,c('severity','lonely'),'severity_outcome_65plus')
cross(d$cc4,c('swallow','lonely'),'exposure_outcome_complete')
cross(d$ccseverity,c('severity','lonely'),'severity_outcome_complete')
for(j in 1:4) cross(d$cc4,c('swallow',paste0('contact',j),'lonely'),paste0('contact',j,'cells_complete'))
flow <- data.frame(stage=c('all_adults','age_numeric_65plus','age65_fallback','all_confirmed_65plus','valid_exposure_and_outcome','complete_M3','complete_M4_common','complete_depression','complete_self_report','complete_severity'),n=c(nrow(d),sum(d$age>=65,na.rm=TRUE),sum(d$older & is.na(d$age)),sum(d$older),sum(d$older & complete.cases(d[c('swallow','lonely')])),sum(d$cc3),sum(d$cc4),sum(d$ccdep),sum(d$ccself),sum(d$ccseverity)))
save_table(flow,'participant_flow')

dmodel <- d[c('PPSU','PSTRAT','WTFA_A','older',core,'contact3','contact4','depression','severity','lonely_broad','cc3','cc4','ccdep','ccself','ccseverity')]
full <- svydesign(ids=~PPSU,strata=~PSTRAT,weights=~WTFA_A,nest=TRUE,data=dmodel)
domain <- subset(full,older)
common <- subset(full,cc4)
audit_design <- function(des,nm) data.frame(population=nm,n=nrow(des$variables),strata=length(unique(des$variables$PSTRAT)),psus=length(unique(interaction(des$variables$PSTRAT,des$variables$PPSU,drop=TRUE))),df=degf(des),weight_total=sum(weights(des)))
save_table(rbind(audit_design(full,'all'),audit_design(domain,'65plus'),audit_design(common,'common_complete')),'design_audit')
psuperstratum <- aggregate(d$PPSU,list(stratum=d$PSTRAT),function(z)length(unique(z)))
stopifnot(all(psuperstratum$x>=2))

# Descriptive prevalence with design-based logit confidence intervals.
prev <- function(des,var,label) {z<-svyciprop(as.formula(paste0('~',var)),des,method='logit',na.rm=TRUE,df=degf(des)); ci<-confint(z); data.frame(group=label,variable=var,n_valid=sum(!is.na(des$variables[[var]])),n_events=sum(des$variables[[var]]==1,na.rm=TRUE),prevalence=as.numeric(z),lower=ci[1],upper=ci[2])}
pr <- rbind(prev(domain,'swallow','all_65plus'),prev(domain,'lonely','all_65plus'),prev(subset(domain,swallow==0),'lonely','no_swallowing_problem'),prev(subset(domain,swallow==1),'lonely','swallowing_problem'),prev(subset(common,swallow==0),'lonely','complete_no_problem'),prev(subset(common,swallow==1),'lonely','complete_problem'))
save_table(pr,'weighted_prevalence')
# Included/excluded comparison is descriptive; endpoint missingness remains explicit.
compare <- do.call(rbind,lapply(c('included','excluded'),function(g) {s<-if(g=='included') subset(domain,cc4) else subset(domain,!cc4); rbind(prev(s,'swallow',g),prev(s,'lonely',g))}))
save_table(compare,'complete_case_comparison')

f0 <- lonely~swallow
f1 <- update(f0,.~.+agegrp+sex)
f2 <- update(f1,.~.+education+poverty+partner+alone+mobility+hearing+stroke)
f3 <- update(f2,.~.+contact1+contact2)
f4 <- update(f3,.~.+contact3+contact4)
poverty <- function(x) cut(x,breaks=c(-Inf,1,2,4,Inf),right=FALSE,labels=c('lt1','1to2','2to4','4plus'))
designs <- lapply(1:10,function(k) {ik<-inc[inc$IMPNUM_A==k,]; idx<-match(d$HHX,ik$HHX); stopifnot(!anyNA(idx),all(ik$POVRATTC_A[idx]>=0 & ik$POVRATTC_A[idx]<=12)); dk<-dmodel; dk$poverty<-poverty(ik$POVRATTC_A[idx]); svydesign(ids=~PPSU,strata=~PSTRAT,weights=~WTFA_A,nest=TRUE,data=dk)})
nc <- ncol(model.matrix(f4,designs[[1]]$variables[d$cc4,]))-1
cells <- table(d$swallow[d$cc4],d$lonely[d$cc4])
gate <- all(cells>=20) && sum(d$lonely[d$cc4])>=10*nc
save_table(data.frame(check=c('minimum_2x2_cell','events_common','nonintercept_parameters_M4','events_per_parameter','proceed'),value=c(min(cells),sum(d$lonely[d$cc4]),nc,sum(d$lonely[d$cc4])/nc,gate)),'feasibility_gate')
cat('FLOW\n'); print(flow); cat('CELLS\n'); print(cells); cat('GATE ',gate,'\n')
if(!gate) stop('Prespecified feasibility gate failed: no regression fitted.')

fits_saved <- list(); diagnostics <- list()
run_model <- function(formula, label, flag='cc4', family=quasipoisson(link='log'), terms='swallow') {
  fits<-lapply(designs,function(des) {ds<-des[des$variables[[flag]],]; svyglm(formula,design=ds,family=family)})
  stopifnot(all(vapply(fits,function(z) z$converged && !anyNA(coef(z)) && all(is.finite(vcov(z))),logical(1))))
  # Residual design degrees of freedom, finite-df Rubin pooling via mitools.
  dfc<-min(vapply(fits,function(z) z$df.residual,numeric(1)))
  pooled<-MIcombine(lapply(fits,coef),lapply(fits,vcov),df.complete=dfc)
  b<-coef(pooled); se<-sqrt(diag(vcov(pooled))); df<-pooled$df; critical<-qt(.975,df)
  out<-data.frame(model=label,term=names(b),measure=if(family$link=='log') 'PR' else 'OR',estimate=exp(b),lower=exp(b-critical*se),upper=exp(b+critical*se),log_estimate=b,se_log=se,df=df,n=nrow(model.frame(fits[[1]])),events=sum(model.response(model.frame(fits[[1]]))),row.names=NULL)
  save_table(out,paste0('coefficients_',label))
  fits_saved[[label]] <<- list(fits=fits,pooled=pooled)
  diagnostics[[label]] <<- data.frame(model=label,df_complete=dfc,n=out$n[1],events=out$events[1],parameters=length(b),min_fitted=min(vapply(fits,function(z) min(fitted(z)),numeric(1))),max_fitted=max(vapply(fits,function(z) max(fitted(z)),numeric(1))),converged=TRUE)
  out[out$term %in% terms,]
}
res <- do.call(rbind,list(run_model(f0,'M0'),run_model(f1,'M1'),run_model(f2,'M2'),run_model(f3,'M3_primary'),run_model(f4,'M4_participation'),run_model(f3,'M3_available','cc3'),run_model(f3,'M3_depression_matched','ccdep'),run_model(update(f3,.~.+depression),'M3_depression','ccdep'),run_model(update(f3,lonely_broad~.),'M3_broad_endpoint'),run_model(f3,'M3_no_proxy','ccself'),run_model(f3,'M3_logistic',family=quasibinomial())))
sevtab<-table(d$severity[d$ccseverity],d$lonely[d$ccseverity])
if(all(sevtab>=20)) res<-rbind(res,run_model(update(f3,.~.-swallow+severity),'M3_severity','ccseverity',terms=c('severitylittle','severitymiddle','severitya_lot')))
save_table(res,'model_results')
save_table(do.call(rbind,diagnostics),'model_diagnostics')
compact <- lapply(fits_saved,function(z) list(pooled=z$pooled,imputations=lapply(z$fits,function(f) list(coefficients=coef(f),covariance=vcov(f),df_residual=f$df.residual))))
saveRDS(compact,'work/models.rds')
capture.output(sessionInfo(),file='outputs/03_R_SessionInfo.txt')
print(res[c('model','term','estimate','lower','upper','n','events')],row.names=FALSE)

