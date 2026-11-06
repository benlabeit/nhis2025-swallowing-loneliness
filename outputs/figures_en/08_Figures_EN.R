# Reproduce from project root (no refitting, uses verified analysis tables):
# Rscript -e "Sys.setlocale('LC_ALL','English_United States.utf8'); source('outputs/08_Figures_EN.R',encoding='UTF-8')"
library(grid)
out <- 'outputs/figures_en'
dir.create(out, recursive=TRUE, showWarnings=FALSE)
m <- read.delim('outputs/tables/model_results.tsv',check.names=FALSE)
p <- read.delim('outputs/tables/weighted_prevalence.tsv',check.names=FALSE)
s <- read.delim('outputs/tables/severity_outcome_complete.tsv',check.names=FALSE)
stopifnot(all(m$lower <= m$estimate),all(m$upper >= m$estimate))
col <- list(ink='#17313F',muted='#526674',grid='#DEE5E9',teal='#007F86',blue='#426A8B',tint='#EAF5F4',white='#FFFFFF')
f <- function(x,n=2) formatC(x,format='f',digits=n,decimal.mark='.')
nn <- function(x) format(x,big.mark=',',decimal.mark='.',scientific=FALSE,trim=TRUE)
ci <- function(a,b,c) paste0(f(a),' [',f(b),', ',f(c),']')
txt <- function(x,y,label,size=12,colour=col$ink,bold=FALSE,just='left') grid.text(label,x,y,just=just,gp=gpar(fontfamily='Arial',fontsize=size,col=colour,fontface=if(bold) 'bold' else 'plain',lineheight=1.15))
ln <- function(x1,y1,x2,y2,colour=col$grid,lwd=1,lty=1) grid.lines(c(x1,x2),c(y1,y2),gp=gpar(col=colour,lwd=lwd,lty=lty))
bg <- function(x,y,w,h,colour) grid.rect(x,y,w,h,gp=gpar(fill=colour,col=NA))
header <- function(no,title,subtitle) {
 grid.newpage(); bg(.5,.5,1,1,col$white)
 txt(.045,.955,paste0('NHIS 2025  /  ',no,'  /  ADULTS AGED 65+'),10.5,col$teal,TRUE)
 txt(.045,.895,title,21,bold=TRUE)
 txt(.045,.842,subtitle,11.5,col$muted)
}
footer <- function(lines) {
 for(i in seq_along(lines)) txt(.045,.125-(i-1)*.026,lines[i],9.5,col$muted)
 txt(.955,.025,'Source: NHIS 2025 public-use data; survey-weighted analysis',8.5,col$muted,just='right')
}
axis_pr <- function(xl=.445,xr=.765,y=.235,max=4.5) {
 xp <- function(z) xl+(log(z)-log(.8))/(log(max)-log(.8))*(xr-xl)
 ticks <- if(max>4) c(1,1.5,2,3,4) else c(1,1.5,2,3)
 for(t in ticks) {
  ln(xp(t),y,xp(t),.755,if(t==1) '#7F919B' else col$grid,lwd=if(t==1) 1.2 else .7,lty=if(t==1) 2 else 1)
  txt(xp(t),y-.028,format(t,decimal.mark='.'),10.5,col$muted,just='centre')
 }
 ln(xl,y,xr,y,col$muted,.8)
 txt((xl+xr)/2,y-.073,'Prevalence ratio (log scale)',10.5,col$muted,just='centre')
 xp
}
point_ci <- function(xp,y,est,lower,upper,colour=col$blue,primary=FALSE) {
 ln(xp(lower),y,xp(upper),y,colour,2)
 ln(xp(lower),y-.009,xp(lower),y+.009,colour,1.2)
 ln(xp(upper),y-.009,xp(upper),y+.009,colour,1.2)
 grid.points(unit(xp(est),'npc'),unit(y,'npc'),pch=if(primary) 18 else 16,size=unit(if(primary) 3.5 else 2.7,'mm'),gp=gpar(col=colour))
}
fig1 <- function() {
 q <- p[match(c('no_swallowing_problem','swallowing_problem'),p$group),]
 stopifnot(sum(q$n_valid)==8231,sum(q$n_events)==438)
 header('FIGURE 1','Frequent loneliness by swallowing problems','Available responses: N = 8,231 | unadjusted, survey-weighted estimates')
 txt(.045,.752,'Swallowing problems',11,col$muted,TRUE)
 txt(.885,.752,'Percent [95% CI]',11,col$muted,TRUE,just='centre')
 xp <- function(z) .39+z/15*.37
 for(t in seq(0,15,5)) {ln(xp(t),.29,xp(t),.705,col$grid,.8); txt(xp(t),.26,paste0(t,' %'),11,col$muted,just='centre')}
 ln(xp(0),.29,xp(15),.29,col$muted,.8)
 txt(.575,.208,'Weighted prevalence of frequent loneliness',11,col$muted,just='centre')
 ys <- c(.615,.425)
 for(i in 1:2) {
  txt(.045,ys[i]+.018,c('No swallowing problems','Swallowing problems')[i],14,bold=TRUE)
  txt(.045,ys[i]-.025,paste0('n = ',nn(q$n_valid[i]),'; events = ',q$n_events[i]),11,col$muted)
  point_ci(xp,ys[i],100*q$prevalence[i],100*q$lower[i],100*q$upper[i],c(col$blue,col$teal)[i],i==2)
  txt(.885,ys[i],ci(100*q$prevalence[i],100*q$lower[i],100*q$upper[i]),12,bold=TRUE,just='centre')
 }
 footer(c('Frequent loneliness: always or usually lonely. Swallowing problems: self-reported during the past 12 months.',
 'Points: weighted prevalence; lines: design-based 95% confidence intervals (CIs). Counts are unweighted.',
 'No covariate adjustment. Denominators differ from the common regression sample.'))
}
fig2 <- function() {
 q<-m[match(c('M0','M1','M2','M3_primary','M4_participation'),m$model),]
 stopifnot(all(q$n==8094),all(q$events==429),all(q$measure=='PR'))
 header('FIGURE 2','Association after sequential adjustment','Frequent loneliness | swallowing problems vs. none | N = 8,094; 429 events')
 txt(.045,.787,'Model / additional adjustment variables',10.5,col$muted,TRUE)
 txt(.88,.787,'PR [95% CI]',11,col$muted,TRUE,just='centre')
 ys<-c(.713,.616,.519,.422,.325)
 bg(.5,ys[4],.93,.086,col$tint)
 xp<-axis_pr()
 labels<-c('M0  Unadjusted','M1  Age and sex','M2  Social and health characteristics','M3  In-person and phone/video contact','M4  Religious and group participation')
 detail<-c('Survey-weighted, no covariates','Demographic adjustment','Education, income, partnership, etc.','Primary model','Extended sensitivity analysis')
 for(i in 1:5) {
  txt(.045,ys[i]+.012,labels[i],11.6,if(i==4) col$teal else col$ink,TRUE)
  txt(.045,ys[i]-.019,detail[i],10.2,col$muted)
  point_ci(xp,ys[i],q$estimate[i],q$lower[i],q$upper[i],if(i==4) col$teal else col$blue,i==4)
  txt(.88,ys[i],ci(q$estimate[i],q$lower[i],q$upper[i]),12,if(i==4) col$teal else col$ink,TRUE,just='centre')
 }
 footer(c('M2 adds education, family poverty ratio, partnership, living alone, mobility, hearing and history of stroke.',
 'Models build on the preceding model. M3: contact outside the household; M4: participation in the past year.',
 'Survey-weighted Poisson models; 95% CIs; ten income imputations. PR = 1 indicates no prevalence difference.',
 'Frequent loneliness: always or usually lonely. Common sample; cross-sectional associations, not causal effects.'))
}
fig3 <- function() {
 q<-m[match(c('severitylittle','severitymiddle','severitya_lot'),m$term),]
 stopifnot(all(q$n==8093),all(q$events==429))
 ns<-vapply(c('none','little','middle','a_lot'),function(z) sum(s$Freq[s$severity==z]),numeric(1))
 ev<-vapply(c('none','little','middle','a_lot'),function(z) sum(s$Freq[s$severity==z & s$lonely==1]),numeric(1))
 header('FIGURE 3','Association by severity of swallowing problems','Secondary analysis | M3 adjustment | N = 8,093; 429 events')
 txt(.045,.787,'Self-reported swallowing difficulties',11,col$muted,TRUE)
 txt(.88,.787,'Adjusted PR [95% CI]',11,col$muted,TRUE,just='centre')
 xp<-axis_pr(); ys<-c(.698,.58,.462,.344)
 for(i in 1:4) {
  txt(.045,ys[i]+.015,c('No swallowing problems','A little difficulty','Somewhere in between','A lot of difficulty')[i],13,bold=TRUE)
  txt(.045,ys[i]-.02,paste0('n = ',nn(ns[i]),'; events = ',ev[i]),11,col$muted)
  if(i==1) {
   grid.points(unit(xp(1),'npc'),unit(ys[i],'npc'),pch=1,size=unit(2.7,'mm'),gp=gpar(col=col$muted,lwd=1.5))
   txt(.88,ys[i],'1.00 (reference)',12,col$muted,just='centre')
  } else {
   point_ci(xp,ys[i],q$estimate[i-1],q$lower[i-1],q$upper[i-1],col$teal)
   txt(.88,ys[i],ci(q$estimate[i-1],q$lower[i-1],q$upper[i-1]),12,bold=TRUE,just='centre')
  }
 }
 footer(c('Frequent loneliness: always or usually lonely. Categories follow the codebook; severity is not a continuous scale.',
 'M3: demographic, social and health characteristics plus in-person and phone/video contact.',
 'Survey-weighted Poisson models; 95% CIs; ten income imputations. Sample sizes and event counts are unweighted.',
 'Secondary results: only 22 events in the most severe category; no trend test or evidence of causation.'))
}
fig4 <- function() {
 ids<-c('M3_primary','M3_available','M3_no_proxy','M3_depression_matched','M3_depression','M3_broad_endpoint')
 q<-m[match(ids,m$model),]; stopifnot(all(q$measure=='PR'))
 header('SUPPLEMENTARY FIGURE S1','Sensitivity analyses of the primary association','Prevalence ratios | sample composition or outcome definition varies across analyses')
 txt(.045,.787,'Analysis / unweighted counts',11,col$muted,TRUE)
 txt(.88,.787,'PR [95% CI]',11,col$muted,TRUE,just='centre')
 ys<-seq(.715,.31,length.out=6); bg(.5,ys[1],.93,.072,col$tint)
 xp<-axis_pr()
 labs<-c('Primary model M3','All complete cases for M3','Excluding proxy interviews','Without adjustment for depressive feelings','Adjusted for depressive feelings','Broader outcome: includes sometimes')
 for(i in 1:6) {
  txt(.045,ys[i]+.012,labs[i],11.3,if(i==1) col$teal else col$ink,TRUE)
  txt(.045,ys[i]-.019,paste0('N = ',nn(q$n[i]),'; events = ',nn(q$events[i])),10.3,col$muted)
  point_ci(xp,ys[i],q$estimate[i],q$lower[i],q$upper[i],if(i==1) col$teal else col$blue,i==1)
  txt(.88,ys[i],ci(q$estimate[i],q$lower[i],q$upper[i]),12,if(i==1) col$teal else col$ink,TRUE,just='centre')
 }
 footer(c('Matched comparison: identical sample (N = 8,055). Attenuation does not establish mediation.',
 'Primary outcome: always or usually lonely; broader outcome: also sometimes. No multiplicity adjustment.',
 'Models with depressive feelings or the broader outcome: some fitted values > 1; not individual probabilities.',
 'Survey-weighted Poisson models; 95% CIs; ten income imputations. Odds-ratio sensitivity analysis not shown.'))
}
figs<-list('Figure1_Weighted_Prevalence'=fig1,'Figure2_Sequential_Models'=fig2,'Figure3_Severity'=fig3,'FigureS1_Sensitivity'=fig4)
for(n in names(figs)) {
 png(file.path(out,paste0(n,'.png')),width=10,height=6.4,units='in',res=300,type='cairo',bg='white'); figs[[n]](); dev.off()
 svg(file.path(out,paste0(n,'.svg')),width=10,height=6.4,family='Arial',bg='white'); figs[[n]](); dev.off()
}
cairo_pdf(file.path(out,'NHIS2025_Figures_EN.pdf'),width=10,height=6.4,family='Arial',onefile=TRUE,bg='white')
for(fn in figs) fn()
dev.off()
# Save the exact plotted inputs as plain text, without transforming model results.
write.table(p[p$group %in% c('no_swallowing_problem','swallowing_problem'),],file.path(out,'Data_Figure1.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
write.table(m,file.path(out,'Data_Models.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
write.table(s,file.path(out,'Data_Severity.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
cat('Created four PNG/SVG figures and a four-page PDF from verified result tables.\n')
