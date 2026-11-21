# Independent verification from original raw files; does not source analysis code.
library(survey)
library(mitools)
options(survey.lonely.psu='fail')
base <- 'results'
raw <- read.csv('work/raw/adult25.csv', colClasses=c(HHX='character'))
income <- read.csv('work/raw/adultinc25.csv',colClasses=c(HHX='character'))
yn <- function(x) {y<-rep(NA_integer_,length(x));y[x %in% 1]<-1L;y[x %in% 2]<-0L;y}
diff3 <- function(x) factor(ifelse(x %in% 1:4,pmin(x,3),NA),levels=1:3)
z <- data.frame(HHX=raw$HHX,PPSU=raw$PPSU,PSTRAT=raw$PSTRAT,WTFA_A=raw$WTFA_A)
z$agegrp <- cut(ifelse(raw$AGEP_A %in% 18:85,raw$AGEP_A,NA),c(64,74,84,Inf),labels=c('65-74','75-84','85+'))
z$sex <- factor(ifelse(raw$SEX_A %in% 1:2,raw$SEX_A,NA),levels=1:2)
z$swallow <- yn(raw$VSLSWYR_A)
z$lonely <- ifelse(raw$LONELY_A %in% 1:5,as.integer(raw$LONELY_A<=2),NA)
z$education <- factor(ifelse(raw$EDUCP_A %in% 1:2,'lt_HS',ifelse(raw$EDUCP_A %in% 3:4,'HS',ifelse(raw$EDUCP_A %in% 5:7,'some_college',ifelse(raw$EDUCP_A %in% 8:10,'BA_plus',NA)))),levels=c('lt_HS','HS','some_college','BA_plus'))
z$partner <- ifelse(raw$MARITAL_A %in% 1:3,as.integer(raw$MARITAL_A<3),NA)
z$alone <- ifelse(raw$PCNT18UPTC %in% 1:3 & raw$PCNTLT18TC %in% 0:3,as.integer(raw$PCNT18UPTC==1 & raw$PCNTLT18TC==0),NA)
z$mobility <- diff3(raw$DIFF_A)
z$hearing <- diff3(raw$HEARINGDF_A)
z$vision <- diff3(raw$VISIONDF_A)
z$stroke <- yn(raw$STREV_A)
z$dementia <- yn(raw$DEMENEV_A)
z$cognition <- diff3(raw$COGMEMDFF_A)
z$mi <- yn(raw$MIEV_A)
z$arthritis <- yn(raw$ARTHEV_A)
z$diabetes <- yn(raw$DIBEV_A)
asthma <- rep(NA_integer_,nrow(raw))
asthma[raw$ASEV_A %in% 2] <- 0L
asthma[raw$ASEV_A %in% 1] <- yn(raw$ASTILL_A[raw$ASEV_A %in% 1])
copd <- yn(raw$COPDEV_A)
z$lung <- rep(NA_integer_,nrow(raw))
z$lung[(copd %in% 0) & (asthma %in% 0)] <- 0L
z$lung[(copd %in% 1) | (asthma %in% 1)] <- 1L
cancer_cols <- c('BLADDCAN_A','BLOODCAN_A','BONECAN_A','BRAINCAN_A','BREASCAN_A','CERVICAN_A','COLONCAN_A','COLRCCAN_A','ESOPHCAN_A','GALLBCAN_A','HDNCKCAN_A','LARYNCAN_A','LEUKECAN_A','LIVERCAN_A','LUNGCAN_A','LYMPHCAN_A','MELANCAN_A','MOUTHCAN_A','OVARYCAN_A','PANCRCAN_A','PROSTCAN_A','RECTUCAN_A','SKNMCAN_A','STOMACAN_A','THROACAN_A','THYROCAN_A','UTERUCAN_A','OTHERCANP_A')
ctype <- sapply(raw[cancer_cols],yn)
ctype[raw$SEX_A %in% 1,c('CERVICAN_A','OVARYCAN_A','UTERUCAN_A')] <- 0L
ctype[raw$SEX_A %in% 2,'PROSTCAN_A'] <- 0L
qualifying_cancer <- rowSums(ctype==1,na.rm=TRUE)>0
only_nmsc <- rowSums(is.na(ctype))==0 & rowSums(ctype,na.rm=TRUE)==0 & raw$SKNDKCAN_A %in% 2 & raw$SKNNMCAN_A %in% 1
z$cancer <- rep(NA_integer_,nrow(raw))
z$cancer[raw$CANEV_A %in% 2 | raw$CANEV_A %in% 1 & only_nmsc] <- 0L
z$cancer[raw$CANEV_A %in% 1 & qualifying_cancer] <- 1L
for(j in 1:4)z[[paste0('contact',j)]] <- factor(ifelse(raw[[paste0('SCONNECT',j,'_A')]] %in% 0:3,raw[[paste0('SCONNECT',j,'_A')]],NA),levels=0:3)
z$depression <- ifelse(raw$DEPFREQ_A %in% 1:5,as.integer(raw$DEPFREQ_A<=2),NA)
form <- lonely~swallow+agegrp+sex+education+poverty+partner+alone+mobility+hearing+vision+stroke+dementia+cognition+mi+lung+arthritis+diabetes+cancer+contact1+contact2+contact3+contact4
required <- setdiff(all.vars(update(form,.~.+depression)),'poverty')
z$eligible <- (raw$AGEP_A %in% 65:85) & raw$PROXYFLAG_A %in% 2
z$common <- z$eligible & complete.cases(z[required])
prepared <- readRDS('work/analysis/prepared.rds')
stopifnot(identical(z$common,prepared$common))
for(v in required)stopifnot(identical(as.character(z[[v]]),as.character(prepared[[v]])))
stopifnot(!anyDuplicated(raw$HHX),!anyDuplicated(income[c('HHX','IMPNUM_A')]),setequal(income$IMPNUM_A,1:10))
fits <- lapply(1:10,function(k){
  inc <- income[income$IMPNUM_A==k,]
  ix <- match(raw$HHX,inc$HHX)
  stopifnot(!anyNA(ix),all(inc$POVRATTC_A[ix]>=0 & inc$POVRATTC_A[ix]<=12))
  zz <- z
  zz$poverty <- cut(inc$POVRATTC_A[ix],c(-Inf,1,2,4,Inf),right=FALSE,labels=c('lt1','1to2','2to4','4plus'))
  des <- svydesign(ids=~PPSU,strata=~PSTRAT,weights=~WTFA_A,nest=TRUE,data=zz)
  des <- subset(des,common)
  svyglm(form,des,family=quasipoisson(link='log'),control=glm.control(epsilon=1e-10,maxit=100))
})
pool <- MIcombine(lapply(fits,coef),lapply(fits,vcov),df.complete=min(sapply(fits,function(x)x$df.residual)))
b <- coef(pool)['swallow']; se <- sqrt(diag(vcov(pool)))['swallow']; df <- pool$df[match('swallow',names(coef(pool)))]
out <- data.frame(model='M3',n=sum(z$common),events=sum(z$lonely[z$common]),exposed=sum(z$swallow[z$common]),exposed_events=sum(z$lonely[z$common & z$swallow==1]),PR=exp(b),lower=exp(b-qt(.975,df)*se),upper=exp(b+qt(.975,df)*se),SE_log=se,df=df,row.names=NULL)
write.table(out,file.path(base,'independent_M3_refit.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
print(out)
main <- read.delim(file.path(base,'tables/model_results.tsv'))
main <- main[main$model=='M3' & main$term=='swallow',]
stopifnot(nrow(main)==1,abs(out$PR-main$estimate)<1e-10,abs(out$lower-main$lower)<1e-10,abs(out$upper-main$upper)<1e-10)
cat('PASS: independently reconstructed all required main predictors, identical common sample, ten-imputation M3 coefficient and CI match to numerical tolerance.\n')

# Independently check survey-logistic predictive margins against direct
# survey-weighted standardization in the first income imputation.
obj <- readRDS('work/analysis/analysis_objects.rds')
margin_checks <- lapply(3:4,function(i) {
  des <- obj$designs[[1]]
  des <- subset(des,common)
  ff <- obj$formulas[[i+1]]
  full_fit <- svyglm(ff,design=des,family=quasibinomial())
  base_fit <- svyglm(update(ff,.~.-swallow),design=des,family=quasibinomial())
  margins <- svypredmeans(base_fit,~swallow,predictat=c(0,1))
  direct <- sapply(0:1,function(a) {
    nd <- des$variables; nd$swallow <- a
    weighted.mean(predict(full_fit,newdata=nd,type='response',se.fit=FALSE),weights(des))
  })
  discrepancy <- max(abs(unname(coef(margins))-direct))
  stopifnot(discrepancy<1e-10)
  data.frame(model=paste0('M',i),imputation=1,
    predicted_no_problem=direct[1],predicted_problem=direct[2],
    maximum_absolute_difference=discrepancy)
})
write.table(do.call(rbind,margin_checks),file.path(base,'independent_margins_check.tsv'),
  sep='\t',quote=FALSE,row.names=FALSE)
cat('PASS: independent logistic predictive-margin checks for M3 and M4.\n')
