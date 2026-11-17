# Expanded sensitivity analyses on self-reports. Explicit coding; ten income imputations.
# This implements the proposal; it does not claim exact reproduction of its unavailable script.
library(survey)
library(mitools)
options(survey.lonely.psu='fail')
d <- readRDS('work/revision_2026-11-17/prepared.rds')
inc <- read.csv('work/raw/adultinc25.csv',colClasses=c(HHX='character'))
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
cancers <- c(setdiff(grep('CAN_A$',names(d),value=TRUE),'SKNNMCAN_A'),'OTHERCANP_A')
cm <- sapply(d[cancers],yn)
other_yes <- rowSums(cm==1,na.rm=TRUE)>0
other_no <- rowSums(is.na(cm))==0 & rowSums(cm)==0
d$cancer <- ifelse(d$CANEV_A==2,0,ifelse(d$CANEV_A==1 & other_yes,1,ifelse(d$CANEV_A==1 & other_no,0,NA)))
d$score <- d$mi+d$lung+d$arthritis+d$diabetes+2*d$cancer
d$comorb <- factor(pmin(d$score,3),levels=0:3)
d$comorb_no_arthritis <- factor(pmin(d$score-d$arthritis,3),levels=0:3)
extra <- c('dementia','cognition','communication','vision','comorb','voice','speech')
d$extended <- d$cc4 & complete.cases(d[extra])
d$extended_m3 <- d$cc3 & complete.cases(d[extra])
d$extended_self <- d$extended & d$PROXYFLAG_A %in% 2
d$extended_dep <- d$extended & !is.na(d$depression)
f3 <- lonely~swallow+agegrp+sex+education+poverty+partner+alone+mobility+hearing+stroke+contact1+contact2
f_cog <- update(f3,.~.+dementia+cognition+communication)
f_sens <- update(f_cog,.~.+vision)
f_full <- update(f_sens,.~.+comorb)
poverty <- function(x) cut(x,c(-Inf,1,2,4,Inf),right=FALSE)
keep <- unique(c('HHX','WTFA_A','PSTRAT','PPSU','PROXYFLAG_A',all.vars(f_full),'comorb_no_arthritis','voice','speech','vision_exposure','depression','cc4','extended','extended_m3','extended_self','extended_dep'))
keep <- setdiff(keep,'poverty')
dd <- d[keep]
designs <- lapply(1:10,function(k) {
  ik<-inc[inc$IMPNUM_A==k,]; z<-dd; z$poverty<-poverty(ik$POVRATTC_A[match(z$HHX,ik$HHX)])
  svydesign(ids=~PPSU,strata=~PSTRAT,weights=~WTFA_A,nest=TRUE,data=z)
})
z<-dd;z$poverty<-poverty(d$POVRATTC_A)
single<-svydesign(ids=~PPSU,strata=~PSTRAT,weights=~WTFA_A,nest=TRUE,data=z)
out <- list()
run <- function(f,label,flag='extended',term='swallow',mode='ten') {
  ds<-if(mode=='ten') designs else list(single)
  fits<-lapply(ds,function(x) svyglm(f,design=x[x$variables[[flag]],],family=quasipoisson()))
  stopifnot(all(sapply(fits,function(x)x$converged && !anyNA(coef(x)))))
  df<-min(sapply(fits,function(x)x$df.residual))
  if(length(fits)>1) {po<-MIcombine(lapply(fits,coef),lapply(fits,vcov),df.complete=df);b<-coef(po)[term];se<-sqrt(diag(vcov(po)))[term];df<-po$df[match(term,names(coef(po)))]}
  else {b<-coef(fits[[1]])[term];se<-sqrt(diag(vcov(fits[[1]])))[term]}
  row<-data.frame(model=label,income=mode,sample=flag,n=nrow(model.frame(fits[[1]])),events=sum(model.response(model.frame(fits[[1]]))),PR=exp(b),lower=exp(b-qt(.975,df)*se),upper=exp(b+qt(.975,df)*se),row.names=NULL)
  out[[length(out)+1]]<<-row
  print(row)
}
for(mode in 'ten') {
  run(f3,'M3_same_sample',mode=mode)
  run(f_cog,'cognitive',mode=mode)
  run(f_sens,'sensory',mode=mode)
  run(f_full,'full',mode=mode)
  run(f_full,'full_dep_matched','extended_dep',mode=mode)
  run(update(f_full,.~.+depression),'full_depression','extended_dep',mode=mode)
  for(ex in c('voice','speech','vision_exposure')) {
    base<-update(f3,paste('.~.-swallow+',ex))
    full<-update(f_full,paste('.~.-swallow+',ex,if(ex=='vision_exposure') '-vision' else ''))
    run(base,paste(ex,'M3'),term=ex,mode=mode)
    run(full,paste(ex,'full'),term=ex,mode=mode)
  }
}
run(f_full,'full_M3_available','extended_m3')
run(update(f_full,.~.-communication),'full_without_communication')
run(update(f_full,.~.-swallow+speech-communication),'speech_without_communication',term='speech')
run(update(f_full,.~.-comorb+comorb_no_arthritis),'full_without_arthritis_score')
write.table(do.call(rbind,out),'outputs/revision_2026-11-17/expanded_adjustment.tsv',sep='\t',row.names=FALSE,quote=FALSE)
audit<-data.frame(variable=extra,missing_in_main=sapply(d[extra],function(x)sum(d$cc4 & is.na(x))))
write.table(audit,'outputs/revision_2026-11-17/expanded_missingness.tsv',sep='\t',row.names=FALSE,quote=FALSE)
cat('EXTENDED COUNTS: ',sum(d$extended),sum(d$extended & d$swallow==1),sum(d$extended & d$swallow==1 & d$lonely==1),'\n')
capture.output(sessionInfo(),file='outputs/revision_2026-11-17/expanded_session.txt')
saveRDS(d,'work/revision_2026-11-17/proposal_prepared.rds')
