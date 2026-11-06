# Run from project root: Rscript outputs/10_Extended_Analysis.R
# Supplementary analyses, planned in 09_Analyseplan_Nachtrag.txt.
options(warn=1,survey.lonely.psu='fail')
.libPaths(c('work/R-library',.libPaths()))
library(survey); library(mitools)
od <- 'outputs/extended_tables'; dir.create(od,recursive=TRUE,showWarnings=FALSE)
put <- function(x,n) write.table(x,file.path(od,paste0(n,'.tsv')),sep='\t',row.names=FALSE,quote=FALSE,na='NA')
d <- readRDS('work/prepared.rds'); inc <- read.csv('work/raw/adultinc25.csv',colClasses=c(HHX='character'))
stopifnot(nrow(d)==24215,sum(d$older)==8492,sum(d$cc4)==8094)
vars <- c('HHX','WTFA_A','PPSU','PSTRAT','older','age','agegrp','swallow','lonely','lonely_broad','sex','education','partner','alone','mobility','hearing','stroke','contact1','contact2','contact3','contact4','depression','severity','cc4','ccdep','LONELY_A','REGION','PCNT18UPTC','PCNTLT18TC','PROXYFLAG_A')
d <- d[vars]
d$eligible <- !is.na(d$age) & d$age>=65
d$response <- as.integer(d$cc4)
d$region <- factor(d$REGION)
d$adult_count <- factor(d$PCNT18UPTC)
d$children <- as.integer(d$PCNTLT18TC>0)
d$proxy <- as.integer(d$PROXYFLAG_A==1)
d$lonely5 <- factor(ifelse(d$LONELY_A %in% 1:5,6-d$LONELY_A,NA),levels=1:5,labels=c('Never','Rarely','Sometimes','Usually','Always'),ordered=TRUE)
full <- svydesign(ids=~PPSU,strata=~PSTRAT,weights=~WTFA_A,nest=TRUE,data=d)
older <- subset(full,older)
f3 <- lonely~swallow+agegrp+sex+education+poverty+partner+alone+mobility+hearing+stroke+contact1+contact2
poverty <- function(x) cut(x,c(-Inf,1,2,4,Inf),right=FALSE,labels=c('Below 100%','100 to <200%','200 to <400%','400% or more'))
designs <- lapply(1:10,function(k) {ik<-inc[inc$IMPNUM_A==k,]; idx<-match(d$HHX,ik$HHX); stopifnot(!anyNA(idx)); dk<-d;dk$poverty<-poverty(ik$POVRATTC_A[idx]);svydesign(ids=~PPSU,strata=~PSTRAT,weights=~WTFA_A,nest=TRUE,data=dk)})
pool <- function(q,v,dfc) MIcombine(q,v,df.complete=dfc)
pooled_rows <- function(po,model,transforms=NULL) {
 b<-coef(po); se<-sqrt(diag(vcov(po))); lo<-b-qt(.975,po$df)*se; hi<-b+qt(.975,po$df)*se
 if(is.null(transforms)) transforms<-rep('none',length(b))
 for(i in seq_along(b)) {fn<-switch(transforms[i],log=exp,logit=plogis,none=identity); b[i]<-fn(b[i]);lo[i]<-fn(lo[i]);hi[i]<-fn(hi[i])}
 data.frame(model=model,measure=names(b),estimate=unname(b),lower=unname(lo),upper=unname(hi),df=unname(po$df),row.names=NULL)
}

# 1. Predictive margins with the official survey implementation.
marginal_fit <- function(form,label,flag) {
 vals<-vars<-list(); dfs<-numeric(10); diag<-list()
 for(k in 1:10) {
  des<-designs[[k]][designs[[k]]$variables[[flag]],]
  base<-svyglm(update(form,.~.-swallow),design=des,family=quasibinomial())
  pm<-svypredmeans(base,~swallow,predictat=c(0,1))
  pr<-unname(coef(pm)); V<-unname(vcov(pm)); stopifnot(all(pr>0 & pr<1))
  J<-rbind(c(1/(pr[1]*(1-pr[1])),0),c(0,1/(pr[2]*(1-pr[2]))),c(-1,1),c(-1/pr[1],1/pr[2]))
  q<-c(qlogis(pr),pr[2]-pr[1],log(pr[2]/pr[1])); names(q)<-c('prevalence_no_problem','prevalence_problem','prevalence_difference','marginal_PR')
  vals[[k]]<-q;vars[[k]]<-J%*%V%*%t(J)
  fit<-svyglm(form,design=des,family=quasibinomial())
  stopifnot(fit$converged)
  # Verify direct survey-weighted standardization agrees with svypredmeans.
  direct<-vapply(0:1,function(a) {nd<-des$variables;nd$swallow<-a;weighted.mean(predict(fit,newdata=nd,type='response',se.fit=FALSE),weights(des))},numeric(1))
  stopifnot(max(abs(direct-pr))<1e-7)
  dfs[k]<-fit$df.residual
  diag[[k]]<-data.frame(model=label,imputation=k,n=nrow(des$variables),events=sum(model.response(model.frame(fit))),min_prediction=min(fitted(fit)),max_prediction=max(fitted(fit)))
 }
 po<-pool(vals,vars,min(dfs)); r<-pooled_rows(po,label,c('logit','logit','none','log'))
 r$n<-diag[[1]]$n;r$events<-diag[[1]]$events
 put(do.call(rbind,diag),paste0('diagnostics_',label))
 list(table=r,pooled=po)
}
mspec <- list(M3=list(f3,'cc4'),M3_depression_matched=list(f3,'ccdep'),M3_depression=list(update(f3,.~.+depression),'ccdep'),M3_broad=list(update(f3,lonely_broad~.),'cc4'))
margins <- lapply(names(mspec),function(nm) marginal_fit(mspec[[nm]][[1]],nm,mspec[[nm]][[2]])); names(margins)<-names(mspec)
put(do.call(rbind,lapply(margins,`[[`,'table')),'standardized_prevalence_and_contrasts')
saveRDS(margins,'work/extended_margins.rds')
cat('STANDARDIZED MARGINS COMPLETE\n'); print(do.call(rbind,lapply(margins,`[[`,'table')))

# NCHS proportion standards. Effective n is capped at nominal n before KG limits.
precision <- function(p,v,n,df,events) {
 ne<-if(p>0 && p<1 && v>0) min(n,p*(1-p)/v) else n
 nadj<-ne*(qt(.025,n-1)/qt(.025,df))^2
 lo<-if(p==0) 0 else qbeta(.025,nadj*p,nadj*(1-p)+1)
 hi<-if(p==1) 1 else qbeta(.975,nadj*p+1,nadj*(1-p))
 width<-hi-lo; rel<-if(p>0) width/p else Inf; comprel<-if(p<1) width/(1-p) else Inf
 classify<-function(rel,event) {
  if(n<30 || ne<30) return('suppress_small_denominator')
  if(width>=.30) return('suppress_wide_CI')
  if(width>.05 && rel>1.30) return('suppress_relative_CI_width')
  if(event==0 || event==n) return('statistical_review_boundary')
  if(df<8) return('statistical_review_low_df')
  'present'
 }
 data.frame(prevalence=p,se=sqrt(v),lower_KG=lo,upper_KG=hi,denominator_n=n,numerator_n=events,effective_n=ne,effective_n_df_adjusted=nadj,design_df=df,CI_width=width,relative_CI_width=rel,status=classify(rel,events),complement_status=classify(comprel,n-events))
}
oneprop <- function(des,var,value,label) {
 valid<-!is.na(des$variables[[var]]); ds<-des[valid,]
 y<-as.numeric(ds$variables[[var]]==value); ds<-update(ds,.binary=y)
 st<-svymean(~.binary,ds); p<-as.numeric(coef(st)); v<-as.numeric(vcov(st))
 data.frame(label=label,variable=var,category=as.character(value),precision(p,v,length(y),degf(ds),sum(y)),row.names=NULL)
}
# 2. Included/excluded characteristics, retaining missingness.
characteristics<-c('agegrp','sex','education','partner','alone','mobility','hearing','stroke','contact1','contact2','contact3','contact4','depression','region','proxy')
descriptive<-function(des,group,vars) do.call(rbind,lapply(vars,function(v) {
 z<-des$variables[[v]]; cats<-if(is.factor(z)) levels(z) else sort(unique(z[!is.na(z)]))
 r<-do.call(rbind,lapply(cats,function(ca) oneprop(des,v,ca,group)))
 r$missing_n<-sum(is.na(z));r$group_n<-length(z);r$missing_weighted_percent<-100*sum(weights(des)[is.na(z)])/sum(weights(des));r
}))
comparison<-rbind(descriptive(subset(older,cc4),'Included',characteristics),descriptive(subset(older,!cc4),'Excluded',characteristics))
put(comparison,'included_excluded_characteristics')

# Response model: known numerical age only. No missing baseline propensity inputs.
elig<-subset(full,eligible)
rf <- response~agegrp+region+adult_count+children+proxy
propfit<-svyglm(rf,design=elig,family=quasibinomial(),control=glm.control(epsilon=1e-12,maxit=100))
stopifnot(propfit$converged,all(is.finite(coef(propfit))))
pr<-as.numeric(predict(propfit,type='response'));stopifnot(all(pr>0 & pr<1))
X<-model.matrix(propfit); w<-weights(elig); R<-elig$variables$response; respbar<-weighted.mean(R,w)
mult<-respbar/pr; cuts<-quantile(mult[R==1],c(.01,.99));mult_trim<-pmax(cuts[1],pmin(cuts[2],mult))
rowselig<-which(d$eligible); rowscc<-which(d$cc4); cc_in_elig<-which(R==1)
Hgg<-crossprod(X,w*pr*(1-pr)*X)
scoreg<-X*as.numeric(w*(R-pr)); IFg<-scoreg%*%solve(Hgg)
propV<-svyrecvar(IFg,elig$cluster,elig$strata,elig$fpc)
stopifnot(max(abs(propV-vcov(propfit)))<1e-7)
diagn<-data.frame(statistic=c('eligible_n','unknown_numeric_age_excluded','included_n','weighted_response_fraction','propensity_min','propensity_max','multiplier_min','multiplier_p01','multiplier_p50','multiplier_p99','multiplier_max','trimmed_below_n','trimmed_above_n','combined_weight_min','combined_weight_max','kish_effective_n'),value=c(nrow(elig$variables),sum(d$older & !d$eligible),sum(R),respbar,min(pr),max(pr),min(mult[R==1]),cuts[1],median(mult[R==1]),cuts[2],max(mult[R==1]),sum(mult[R==1]<cuts[1]),sum(mult[R==1]>cuts[2]),min(w[R==1]*mult[R==1]),max(w[R==1]*mult[R==1]),sum(w[R==1]*mult[R==1])^2/sum((w[R==1]*mult[R==1])^2)))
put(diagn,'response_weight_diagnostics')
put(data.frame(term=names(coef(propfit)),coefficient=coef(propfit),se=sqrt(diag(vcov(propfit)))),'response_model_coefficients')
ipq<-ipv<-tq<-tv<-list(); dfc<-numeric(10); checks<-numeric(10)
for(k in 1:10) {
 dk<-designs[[k]]$variables; dk$ipw<-dk$WTFA_A; dk$ipw[rowselig]<-dk$WTFA_A[rowselig]*mult
 iwfull<-svydesign(ids=~PPSU,strata=~PSTRAT,weights=~ipw,nest=TRUE,data=dk)
 iw<-subset(iwfull,cc4); fit<-svyglm(f3,design=iw,family=quasipoisson(link='log'),control=glm.control(epsilon=1e-12,maxit=100));stopifnot(fit$converged)
 Z<-model.matrix(fit); yy<-model.response(model.frame(fit)); mu<-fitted(fit)
 # Use un-stabilized weights; the global stabilizing constant cancels.
 wo<-w[R==1]/pr[R==1]; Xcc<-X[R==1,,drop=FALSE]
 Hbb<-crossprod(Z,as.numeric(wo*mu)*Z)
 Cbg<-crossprod(Z,as.numeric(wo*(1-pr[R==1])*(yy-mu))*Xcc)
 scoreb<-matrix(0,nrow(X),ncol(Z));scoreb[R==1,]<-Z*as.numeric(wo*(yy-mu))
 IFfixed<-scoreb%*%solve(Hbb)
 IFadjusted<-(scoreb-IFg%*%t(Cbg))%*%solve(Hbb)
 VVfixed<-svyrecvar(IFfixed,elig$cluster,elig$strata,elig$fpc)
 VV<-svyrecvar(IFadjusted,elig$cluster,elig$strata,elig$fpc)
 checks[k]<-max(abs(VVfixed-vcov(fit)))
 stopifnot(checks[k]<1e-7)
 ipq[[k]]<-coef(fit);ipv[[k]]<-VV;dfc[k]<-fit$df.residual
 dk$ipw[rowselig]<-dk$WTFA_A[rowselig]*mult_trim
 twfull<-svydesign(ids=~PPSU,strata=~PSTRAT,weights=~ipw,nest=TRUE,data=dk)
 tf<-svyglm(f3,design=subset(twfull,cc4),family=quasipoisson(link='log'))
 tq[[k]]<-coef(tf);tv[[k]]<-vcov(tf)
}
ip<-pooled_rows(pool(ipq,ipv,min(dfc)),'Response_IPW_joint_linearization',rep('log',length(ipq[[1]])))
tr<-pooled_rows(pool(tq,tv,min(dfc)),'Response_IPW_winsorized_conditional_CI',rep('log',length(tq[[1]])))
put(rbind(ip[ip$measure=='swallow',],tr[tr$measure=='swallow',]),'response_weighted_M3_PR')
put(data.frame(imputation=1:10,max_covariance_difference=checks),'joint_score_validation')
cat('RESPONSE WEIGHTING COMPLETE\n');print(rbind(ip[ip$measure=='swallow',],tr[tr$measure=='swallow',]))

# 3. Table 1; available-data and common regression samples separately.
tablevars<-c('agegrp','sex','education','partner','alone','mobility','hearing','stroke','contact1','contact2','contact3','contact4','depression','proxy')
t1<-list(); idx<-1
for(pop in c('available','common')) for(a in 0:1) {
 ds<-if(pop=='available') subset(older,swallow==a) else subset(full,cc4 & swallow==a)
 r<-descriptive(ds,paste(pop,a,sep='_'),tablevars);r$population<-pop;r$swallow<-a
 t1[[idx]]<-r;idx<-idx+1
}
put(do.call(rbind,t1),'table1_characteristics')
income_rows<-list();idx<-1
for(pop in c('available','common')) for(a in 0:1) {
 ests<-covs<-ns<-list(); dfs<-numeric(10)
 for(k in 1:10) {
  des<-designs[[k]];ds<-if(pop=='available') subset(des,older & swallow==a) else subset(des,cc4 & swallow==a)
  st<-svymean(~poverty,ds);ests[[k]]<-coef(st);covs[[k]]<-vcov(st);ns[[k]]<-table(ds$variables$poverty);dfs[k]<-degf(ds)
 }
 po<-pool(ests,covs,min(dfs));counts<-do.call(rbind,ns)
 income_rows[[idx]]<-data.frame(population=pop,swallow=a,category=levels(ds$variables$poverty),weighted_percent=100*coef(po),se_percent=100*sqrt(diag(vcov(po))),n_min=apply(counts,2,min),n_max=apply(counts,2,max),missing_n=0,group_n=nrow(ds$variables),note='Ten imputations pooled; n varies by imputation',row.names=NULL);idx<-idx+1
}
put(do.call(rbind,income_rows),'table1_income_ten_imputations')

rawprev<-rbind(oneprop(older,'swallow',1,'all_65plus_swallowing'),oneprop(older,'lonely',1,'all_65plus_loneliness'),oneprop(subset(older,swallow==0),'lonely',1,'no_swallowing_problems'),oneprop(subset(older,swallow==1),'lonely',1,'swallowing_problems'),oneprop(subset(full,cc4 & swallow==0),'lonely',1,'common_no_problems'),oneprop(subset(full,cc4 & swallow==1),'lonely',1,'common_problems'))
put(rawprev,'NCHS_precision_primary_prevalences')

# 4. All loneliness categories. Separate cumulative fits assess PO assumptions.
dist<-do.call(rbind,lapply(0:1,function(a) do.call(rbind,lapply(levels(d$lonely5),function(ca) oneprop(subset(older,swallow==a),'lonely5',ca,paste0('swallow_',a))))))
put(dist,'loneliness_five_categories')
diagq<-diagv<-allq<-allv<-list(); odf<-numeric(10); checkcov<-numeric(10)
for(k in 1:10) {
 ds<-subset(designs[[k]],cc4); ff<-infl<-list()
 for(t in 1:4) {
  ds$variables$threshold_outcome<-as.integer(as.numeric(ds$variables$lonely5)>t)
  ff[[t]]<-svyglm(update(f3,threshold_outcome~.),design=ds,family=quasibinomial(),influence=TRUE)
  stopifnot(ff[[t]]$converged)
  infl[[t]]<-attr(ff[[t]],'influence')
 }
 npar<-length(coef(ff[[1]])); slopes<-names(coef(ff[[1]]))[-1]
 bigV<-svyrecvar(do.call(cbind,infl),ds$cluster,ds$strata,ds$fpc)
 checkcov[k]<-max(abs(bigV[1:npar,1:npar]-vcov(ff[[1]])));stopifnot(checkcov[k]<1e-7)
 q<-unlist(lapply(ff,coef));C<-matrix(0,3*(npar-1),4*npar);r<-1;cnames<-character(nrow(C))
 for(t in c(1,2,4)) for(j in 2:npar) {C[r,(t-1)*npar+j]<-1;C[r,2*npar+j]<--1;cnames[r]<-paste0('threshold',t,'_vs3:',slopes[j-1]);r<-r+1}
 cq<-drop(C%*%q);names(cq)<-cnames;diagq[[k]]<-cq;diagv[[k]]<-C%*%bigV%*%t(C)
 si<-which(names(coef(ff[[1]]))=='swallow');inds<-(0:3)*npar+si
 aq<-q[inds];names(aq)<-c('at_least_rarely','at_least_sometimes','at_least_usually','always');allq[[k]]<-aq;allv[[k]]<-bigV[inds,inds]
 odf[k]<-min(vapply(ff,function(z)z$df.residual,numeric(1)))
}
ordtest<-pool(diagq,diagv,min(odf)); bb<-coef(ordtest);ss<-sqrt(diag(vcov(ordtest)));pval<-2*pt(-abs(bb/ss),ordtest$df);padj<-pmin(1,pval*length(bb))
diagtable<-data.frame(contrast=names(bb),log_OR_difference=unname(bb),se=ss,df=ordtest$df,p_unadjusted=pval,p_Bonferroni=padj,reject=padj<.05,row.names=NULL)
put(diagtable,'proportional_odds_diagnostics')
thresholds<-pooled_rows(pool(allq,allv,min(odf)),'Cumulative_logistic_OR',rep('log',4));thresholds$n<-sum(d$cc4)
put(thresholds,'threshold_specific_swallowing_OR')
put(data.frame(imputation=1:10,max_covariance_difference=checkcov),'threshold_covariance_validation')
if(!any(diagtable$reject)) {
 ofits<-lapply(designs,function(des) svyolr(update(f3,lonely5~.),design=subset(des,cc4)))
 os<-lapply(ofits,function(x) coef(x)['swallow']);ov<-lapply(ofits,function(x) vcov(x)['swallow','swallow',drop=FALSE]);oo<-pool(os,ov,min(odf))
 put(pooled_rows(oo,'Exploratory_proportional_odds',transforms='log'),'ordinal_model_if_supported')
 ordinal_status<-'No Bonferroni-adjusted slope contrast rejected; exploratory ordinal model fitted. Limited power of diagnostics remains.'
} else ordinal_status<-paste0('Proportional odds not supported: ',sum(diagtable$reject),' of ',nrow(diagtable),' slope contrasts reject after Bonferroni adjustment. No common ordinal OR fitted.')
writeLines(ordinal_status,file.path(od,'ordinal_model_decision.txt'))
capture.output(sessionInfo(),file='outputs/extended_tables/session_info.txt')
saveRDS(list(margins=margins,ipw=pool(ipq,ipv,min(dfc)),ipw_trimmed=pool(tq,tv,min(dfc)),ordinal_diagnostics=ordtest,thresholds=thresholds),'work/extended_models_summary.rds')
cat('EXTENDED ANALYSES COMPLETE\n',ordinal_status,'\n');print(thresholds)
