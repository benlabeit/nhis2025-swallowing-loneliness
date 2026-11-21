library(survey)
options(survey.lonely.psu='fail')
base<-'outputs/revision_2026-11-17'
d<-readRDS('work/revision_2026-11-17/prepared.rds')
inc<-read.csv('work/raw/adultinc25.csv',colClasses=c(HHX='character'))
current<-read.delim(file.path(base,'tables/model_results.tsv'))
original<-read.delim('outputs/tables/model_results.tsv')
new<-subset(current,model=='M3_primary')
old<-subset(original,model=='M3_no_proxy')
stopifnot(new$n==7829,new$events==411,max(abs(unlist(new[c('estimate','lower','upper')])-unlist(old[c('estimate','lower','upper')])))<1e-8)
stopifnot(sum(d$cc4_all & !d$self)==265,sum(d$older_all & !d$self)==288,all(d$self[d$cc4]))
withproxy<-subset(current,model=='M3_including_proxy');oldprimary<-subset(original,model=='M3_primary')
stopifnot(max(abs(unlist(withproxy[c('estimate','lower','upper')])-unlist(oldprimary[c('estimate','lower','upper')])))<1e-8)
i<-inc[inc$IMPNUM_A==1,]
d$poverty<-cut(i$POVRATTC_A[match(d$HHX,i$HHX)],c(-Inf,1,2,4,Inf),right=FALSE,labels=c('lt1','1to2','2to4','4plus'))
f<-lonely~swallow+agegrp+sex+education+poverty+partner+alone+mobility+hearing+stroke+contact1+contact2
des<-svydesign(ids=~PPSU,strata=~PSTRAT,weights=~WTFA_A,nest=TRUE,data=d)
sub<-subset(des,cc4);x<-d[d$cc4,]
control<-glm.control(epsilon=1e-12,maxit=100)
sf<-svyglm(f,design=sub,family=quasipoisson(),control=control)
gf<-glm(f,data=x,weights=WTFA_A/mean(WTFA_A),family=quasipoisson(),control=control)
stopifnot(max(abs(coef(gf)-coef(sf)))<1e-9)
X<-model.matrix(gf);w<-x$WTFA_A;mu<-fitted(gf);y<-x$lonely
H<-crossprod(X,(w*mu)*X);IF<-(X*as.numeric(w*(y-mu)))%*%solve(H)
V<-svyrecvar(IF,sub$cluster,sub$strata,sub$fpc)
stopifnot(max(abs(V-vcov(sf)))<1e-7)
e<-readRDS('work/revision_2026-11-17/proposal_prepared.rds')
# Independently identify single-type histories and a mixed history from raw indicators.
only_nonmelanoma <- with(e, CANEV_A %in% 1 & NUMCAN_A %in% 1 & SKNNMCAN_A %in% 1)
only_unknown_skin <- with(e, CANEV_A %in% 1 & NUMCAN_A %in% 1 & SKNDKCAN_A %in% 1)
mixed_history <- with(e, SKNNMCAN_A %in% 1 & (MELANCAN_A %in% 1 | OTHERCANP_A %in% 1))
stopifnot(any(only_nonmelanoma), all(e$cancer[only_nonmelanoma]==0),
          any(only_unknown_skin), all(is.na(e$cancer[only_unknown_skin])),
          any(mixed_history), all(e$cancer[mixed_history]==1))
stopifnot(sum(e$extended)==7658, all(e$self[e$extended]),
          sum(e$extended & e$swallow==1)==606, sum(e$lonely[e$extended])==399,
          sum(e$extended & e$swallow==1 & e$lonely==1)==75)
expanded<-read.delim(file.path(base,'expanded_adjustment.tsv'))
stopifnot(all(expanded$income=='ten'),all(expanded$lower<=expanded$PR),all(expanded$PR<=expanded$upper))
stopifnot(abs(subset(expanded,model=='full')$PR-1.68495090157365)<1e-8)
precision<-read.delim(file.path(base,'extended_tables/NCHS_precision_primary_prevalences.tsv'))
stopifnot(all(precision$status=='present'),all(precision$complement_status=='present'))
results<-c('Self-report main model reproduces the previous proxy-exclusion sensitivity.', 'Including proxies reproduces the original main model.', 'Excluded proxies: 288 age-eligible; 265 in otherwise complete regression sample.', 'Independent weighted GLM coefficients and score-based survey covariance agree.', 'All expanded models pool ten income imputations and have ordered confidence intervals.', 'Cancer coding and expanded sample counts passed independent checks.', 'All six primary descriptive proportions and complements pass precision checks.')
writeLines(results,file.path(base,'validation.txt'))
cat(paste(results,collapse='\n'),'\n')
