# Run from repository root. Public-use data; ten official income imputations.
# Models M0–M4 use four cumulative adjustment blocks.
options(warn=1, survey.lonely.psu='fail')
.libPaths(c('work/R-library', .libPaths()))
library(survey)
library(mitools)
od <- 'results/tables'
wd <- 'work/analysis'
dir.create(od,recursive=TRUE,showWarnings=FALSE)
dir.create(wd,recursive=TRUE,showWarnings=FALSE)
put <- function(x,n) write.table(x,file.path(od,paste0(n,'.tsv')),sep='\t',row.names=FALSE,quote=FALSE,na='NA')
d <- read.csv('work/raw/adult25.csv', colClasses=c(HHX='character'))
inc <- read.csv('work/raw/adultinc25.csv', colClasses=c(HHX='character'))
stopifnot(nrow(d)==24215L, ncol(d)==577L, !anyDuplicated(d$HHX), all(d$SRVY_YR==2025), all(d$WTFA_A>0), !anyNA(d[c('PSTRAT','PPSU','WTFA_A')]))
stopifnot(nrow(inc)==10*nrow(d), !anyDuplicated(inc[c('HHX','IMPNUM_A')]), setequal(inc$IMPNUM_A,1:10))
# Compare with official full-adult codebook frequencies, before recoding.
stopifnot(sum(d$VSLSWYR_A==1,na.rm=TRUE)==1463, sum(d$LONELY_A==1,na.rm=TRUE)==692, sum(d$VSLSWDIF_A==2,na.rm=TRUE)==264)
valid <- function(x, values) ifelse(x %in% values,x,NA)
d$age <- valid(d$AGEP_A,18:85)
d$older <- (!is.na(d$age) & d$age>=65) | (is.na(d$age) & d$AGE65 %in% 2)
d$older_all <- d$older
d$self <- d$PROXYFLAG_A %in% 2
d$older <- d$older_all & d$self
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

yn <- function(x) ifelse(x %in% 1:2,as.integer(x==1),NA)
dif <- function(x) factor(ifelse(x %in% 1:4,pmin(x,3),NA))
d$dementia <- yn(d$DEMENEV_A)
d$cognition <- dif(d$COGMEMDFF_A)
d$communication <- dif(d$COMDIFF_A)
d$vision <- dif(d$VISIONDF_A)
d$vision_exposure <- ifelse(d$VISIONDF_A %in% 1:4,as.integer(d$VISIONDF_A>1),NA)
d$voice <- yn(d$VSLVYR1_A)
d$speech <- yn(d$VSLSPYR_A)
d$mi <- yn(d$MIEV_A)
d$arthritis <- yn(d$ARTHEV_A)
d$diabetes <- yn(d$DIBEV_A)
asthma <- ifelse(d$ASEV_A==2,0,ifelse(d$ASEV_A==1,yn(d$ASTILL_A),NA))
copd <- yn(d$COPDEV_A)
d$lung <- ifelse(copd==1 | asthma==1,1,ifelse(copd==0 & asthma==0,0,NA))
# NHIS Sample Adult cancer-type indicators, including the public-use other category.
cancers <- c('BLADDCAN_A', 'BLOODCAN_A', 'BONECAN_A', 'BRAINCAN_A', 'BREASCAN_A',
             'CERVICAN_A', 'COLONCAN_A', 'COLRCCAN_A', 'ESOPHCAN_A', 'GALLBCAN_A',
             'HDNCKCAN_A', 'LARYNCAN_A', 'LEUKECAN_A', 'LIVERCAN_A', 'LUNGCAN_A',
             'LYMPHCAN_A', 'MELANCAN_A', 'MOUTHCAN_A', 'OVARYCAN_A', 'PANCRCAN_A',
             'PROSTCAN_A', 'RECTUCAN_A', 'SKNMCAN_A', 'STOMACAN_A', 'THROACAN_A',
             'THYROCAN_A', 'UTERUCAN_A', 'OTHERCANP_A')
cm <- sapply(d[cancers], yn)
# Items outside the sex-specific question universe cannot establish another cancer.
cm[d$SEX_A %in% 1, c('CERVICAN_A', 'OVARYCAN_A', 'UTERUCAN_A')] <- 0
cm[d$SEX_A %in% 2, 'PROSTCAN_A'] <- 0
other_yes <- rowSums(cm==1,na.rm=TRUE)>0
other_no <- rowSums(is.na(cm))==0 & rowSums(cm)==0 & d$SKNDKCAN_A %in% 2 & d$SKNNMCAN_A %in% 1
d$cancer <- ifelse(d$CANEV_A==2,0,ifelse(d$CANEV_A==1 & other_yes,1,ifelse(d$CANEV_A==1 & other_no,0,NA)))

# Current common sample depends only on variables in M0--M4. Comparison exposures,
# communication difficulties and severity do not restrict this sample.
f0 <- lonely~swallow
f1 <- update(f0,.~.+agegrp+sex+education+poverty+partner+alone)
f2 <- update(f1,.~.+mobility+hearing+vision+stroke+dementia+cognition+mi+lung+arthritis+diabetes+cancer)
f3 <- update(f2,.~.+contact1+contact2+contact3+contact4)
f4 <- update(f3,.~.+depression)
needed <- setdiff(all.vars(f4),'poverty')
needed_m3 <- setdiff(all.vars(f3),'poverty')
d$common_all <- d$older_all & complete.cases(d[needed])
d$common <- d$common_all & d$self
d$available_m3 <- d$older & complete.cases(d[needed_m3])
d$severity_common <- d$common & !is.na(d$severity)
d$communication_common <- d$common & !is.na(d$communication)
d$comparison_common <- d$common & complete.cases(d[c('voice','speech','vision_exposure')])
d$eligible <- !is.na(d$age) & d$age>=65 & d$self
d$response <- as.integer(d$common)
d$region <- factor(d$REGION)
d$adult_count <- factor(d$PCNT18UPTC)
d$children <- as.integer(d$PCNTLT18TC>0)
d$proxy <- as.integer(d$PROXYFLAG_A==1)
d$lonely5 <- factor(ifelse(d$LONELY_A %in% 1:5,6-d$LONELY_A,NA),levels=1:5,labels=c('Never','Rarely','Sometimes','Usually','Always'),ordered=TRUE)
saveRDS(d,file.path(wd,'prepared.rds'))
saveRDS(list(M0=f0,M1=f1,M2=f2,M3=f3,M4=f4),file.path(wd,'formulas.rds'))
model_spec <- data.frame(model=c('M0','M1','M2','M3','M4'),role=c('Unadjusted','Sociodemographic and household','Health','Primary: social connection','Additional: depressive feelings'),formula=vapply(list(f0,f1,f2,f3,f4),function(f)paste(deparse(f),collapse=' '),character(1)))
put(model_spec,'model_specification')
flow <- data.frame(stage=c('all_adults','all_numeric_age_65plus','all_age65_fallback','all_age_eligible_including_proxy','proxy_age_eligible','self_report_age_eligible','self_report_valid_exposure_and_outcome','common_M0_to_M4','available_M3_without_depression_restriction','severity_common','communication_matched','comparison_exposure_matched','common_including_proxy','proxy_in_otherwise_complete_sample'),n=c(nrow(d),sum(d$age>=65,na.rm=TRUE),sum(d$older_all & is.na(d$age)),sum(d$older_all),sum(d$older_all & !d$self),sum(d$older),sum(d$older & complete.cases(d[c('swallow','lonely')])),sum(d$common),sum(d$available_m3),sum(d$severity_common),sum(d$communication_common),sum(d$comparison_common),sum(d$common_all),sum(d$common_all & !d$self)))
put(flow,'participant_flow'); print(flow)
put(data.frame(variable=needed,n_older=sum(d$older),missing=sapply(d[needed],function(x)sum(d$older & is.na(x)))), 'missingness')
rawvars <- c('AGEP_A','AGE65','VSLSWYR_A','VSLSWDIF_A','LONELY_A',paste0('SCONNECT',1:4,'_A'),'SEX_A','EDUCP_A','MARITAL_A','PCNT18UPTC','PCNTLT18TC','DIFF_A','HEARINGDF_A','STREV_A','DEPFREQ_A','PROXYFLAG_A','IMPINCFLG_A','DEMENEV_A','COGMEMDFF_A','COMDIFF_A','VISIONDF_A','MIEV_A','ARTHEV_A','DIBEV_A','ASEV_A','ASTILL_A','COPDEV_A','CANEV_A','SKNDKCAN_A','SKNNMCAN_A')
put(do.call(rbind,lapply(rawvars,function(v){t<-as.data.frame(table(d[d$older,v],useNA='always'));names(t)<-c('code','n');data.frame(variable=v,t)})),'raw_frequencies_65plus')
put(as.data.frame(table(swallow=d$swallow[d$common],lonely=d$lonely[d$common])),'exposure_outcome_common')
put(as.data.frame(table(severity=d$severity[d$severity_common],lonely=d$lonely[d$severity_common])),'severity_outcome_common')
inc_one <- inc[inc$IMPNUM_A==1,]
imputation_flag <- if('IMPINCFLG_A' %in% names(inc)) inc_one$IMPINCFLG_A[match(d$HHX,inc_one$HHX)] else d$IMPINCFLG_A
# Flag 1 means fully imputed; flag 2 means income imputed within reported brackets.
put(data.frame(population=c('older_self','common'),n=c(sum(d$older),sum(d$common)),income_fully_imputed_n=c(sum(d$older & imputation_flag %in% 1),sum(d$common & imputation_flag %in% 1)),income_bracket_imputed_n=c(sum(d$older & imputation_flag %in% 2),sum(d$common & imputation_flag %in% 2)),income_imputed_n=c(sum(d$older & imputation_flag %in% 1:2),sum(d$common & imputation_flag %in% 1:2))), 'income_imputation_counts')

keep <- unique(c('HHX','PPSU','PSTRAT','WTFA_A','older','older_all','self',needed,needed_m3,'communication','voice','speech','vision_exposure','lonely_broad','severity','common','common_all','available_m3','severity_common','communication_common','comparison_common','eligible','response','region','adult_count','children','proxy','lonely5'))
dd <- d[keep]
poverty <- function(x) cut(x,breaks=c(-Inf,1,2,4,Inf),right=FALSE,labels=c('lt1','1to2','2to4','4plus'))
designs <- lapply(1:10,function(k){ik<-inc[inc$IMPNUM_A==k,];ix<-match(d$HHX,ik$HHX);stopifnot(!anyNA(ix),all(ik$POVRATTC_A[ix]>=0 & ik$POVRATTC_A[ix]<=12));dk<-dd;dk$poverty<-poverty(ik$POVRATTC_A[ix]);svydesign(ids=~PPSU,strata=~PSTRAT,weights=~WTFA_A,nest=TRUE,data=dk)})
full <- designs[[1]]; older <- subset(full,older); common <- subset(full,common)
audit_design <- function(des,nm)data.frame(population=nm,n=nrow(des$variables),strata=length(unique(des$variables$PSTRAT)),psus=length(unique(interaction(des$variables$PSTRAT,des$variables$PPSU,drop=TRUE))),df=degf(des),weight_total=sum(weights(des)))
put(rbind(audit_design(full,'all'),audit_design(older,'older_self'),audit_design(common,'common')),'design_audit')

fits_saved <- list(); diagnostics <- list(); results <- list()
run_model <- function(form,label,flag='common',family=quasipoisson(link='log'),terms='swallow'){
  fits <- lapply(designs,function(des){ds<-des[des$variables[[flag]],];svyglm(form,design=ds,family=family,control=glm.control(epsilon=1e-10,maxit=100))})
  stopifnot(all(vapply(fits,function(z)z$converged && !anyNA(coef(z)) && all(is.finite(vcov(z))),logical(1))))
  dfc <- min(vapply(fits,function(z)z$df.residual,numeric(1)))
  po <- MIcombine(lapply(fits,coef),lapply(fits,vcov),df.complete=dfc)
  b<-coef(po);se<-sqrt(diag(vcov(po)));df<-po$df;crit<-qt(.975,df)
  out<-data.frame(model=label,term=names(b),measure=if(family$link=='log')'PR' else 'OR',estimate=exp(b),lower=exp(b-crit*se),upper=exp(b+crit*se),log_estimate=b,se_log=se,df=df,n=nrow(model.frame(fits[[1]])),events=sum(model.response(model.frame(fits[[1]]))),row.names=NULL)
  put(out,paste0('coefficients_',label));fits_saved[[label]]<<-list(fits=fits,pooled=po)
  mm<-model.matrix(fits[[1]]);p<-length(b)-1
  diagrow<-data.frame(model=label,df_complete=dfc,n=out$n[1],events=out$events[1],nonintercept_parameters=p,events_per_parameter=out$events[1]/p,minimum_category_n=min(vapply(as.data.frame(mm[,-1,drop=FALSE]),function(x)sum(x!=0),numeric(1))),min_fitted=min(vapply(fits,function(z)min(fitted(z)),numeric(1))),max_fitted=max(vapply(fits,function(z)max(fitted(z)),numeric(1))),minimum_covariance_eigenvalue=min(vapply(fits,function(z)min(eigen(vcov(z),symmetric=TRUE,only.values=TRUE)$values),numeric(1))),max_glm_iterations=max(vapply(fits,function(z)z$iter,numeric(1))),converged=TRUE)
  diagnostics[[label]]<<-diagrow
  out<-out[out$term %in% terms,]
  results[[label]]<<-out
  cat('\nMODEL',label,'\n');print(out[c('model','term','estimate','lower','upper','n','events')],row.names=FALSE)
  put(do.call(rbind,results),'model_results');put(do.call(rbind,diagnostics),'model_diagnostics')
  invisible(out)
}

for(i in 0:4)run_model(get(paste0('f',i)),paste0('M',i))
cat('\nPRIMARY MODELS COMPLETE\n');flush.console()
run_model(update(f3,.~.-swallow+severity),'M3_severity',flag='severity_common',terms=c('severitylittle','severitymiddle','severitya_lot'))
run_model(update(f4,.~.-swallow+severity),'M4_severity',flag='severity_common',terms=c('severitylittle','severitymiddle','severitya_lot'))
run_model(update(f3,lonely_broad~.),'M3_broad')
run_model(f3,'M3_including_proxy',flag='common_all')
run_model(f3,'M3_available',flag='available_m3')
run_model(f3,'M3_logistic',family=quasibinomial())
run_model(f4,'M4_logistic',family=quasibinomial())
run_model(f3,'M3_communication_matched',flag='communication_common')
run_model(update(f3,.~.+communication),'M3_communication',flag='communication_common')
run_model(f4,'M4_communication_matched',flag='communication_common')
run_model(update(f4,.~.+communication),'M4_communication',flag='communication_common')
run_model(f3,'M3_comparison_matched',flag='comparison_common')
run_model(f4,'M4_comparison_matched',flag='comparison_common')
for(ex in c('voice','speech','vision_exposure')){
  for(i in 3:4){ff<-update(get(paste0('f',i)),paste0('.~.-swallow+',ex,if(ex=='vision_exposure')'-vision' else ''));run_model(ff,paste0('M',i,'_',ex),flag='comparison_common',terms=ex)}
}
compact<-lapply(fits_saved,function(z)list(pooled=z$pooled,imputations=lapply(z$fits,function(f)list(coefficients=coef(f),covariance=vcov(f),df_residual=f$df.residual))))
saveRDS(compact,file.path(wd,'models.rds'))
capture.output(sessionInfo(),file='results/R_session_info.txt')

# Save remaining objects for a separate descriptives / margins / robustness run.
saveRDS(list(d=d,dd=dd,designs=designs,formulas=list(f0,f1,f2,f3,f4)),file.path(wd,'analysis_objects.rds'))
cat('\nREGRESSION ANALYSES COMPLETE\n')
