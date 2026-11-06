# Run from project root: Rscript outputs/12_Extended_Figures_EN.R
# Figures use already computed supplementary results; no models are refitted.
library(grid)
out<-'outputs/figures_en';dir.create(out,recursive=TRUE,showWarnings=FALSE)
m<-read.delim('outputs/extended_tables/standardized_prevalence_and_contrasts.tsv')
d<-read.delim('outputs/extended_tables/loneliness_five_categories.tsv')
C<-list(ink='#17313F',muted='#526674',grid='#DEE5E9',teal='#007F86',blue='#426A8B',tint='#EAF5F4')
tx<-function(x,y,s,size=12,col=C$ink,bold=FALSE,just='left') grid.text(s,x,y,just=just,gp=gpar(fontfamily='Arial',fontsize=size,col=col,fontface=if(bold)'bold' else 'plain',lineheight=1.12))
ln<-function(x1,y1,x2,y2,col=C$grid,lwd=1)grid.lines(c(x1,x2),c(y1,y2),gp=gpar(col=col,lwd=lwd))
dot<-function(x,y,lo,hi,col,shape=16){ln(lo,y,hi,y,col,2);ln(lo,y-.008,lo,y+.008,col);ln(hi,y-.008,hi,y+.008,col);grid.points(unit(x,'npc'),unit(y,'npc'),pch=shape,size=unit(3,'mm'),gp=gpar(col=col))}
f<-function(x,n=2)formatC(x,format='f',digits=n)
head<-function(no,title,sub){grid.newpage();grid.rect(gp=gpar(fill='white',col=NA));tx(.045,.955,paste('NHIS 2025 /',no,'/ ADULTS AGED 65+'),10.5,C$teal,TRUE);tx(.045,.895,title,21,bold=TRUE);tx(.045,.842,sub,11.5,C$muted)}
foot<-function(lines){for(i in seq_along(lines))tx(.045,.12-(i-1)*.027,lines[i],9.5,C$muted);tx(.955,.025,'Source: NHIS 2025 public-use data; supplementary survey analysis',8.5,C$muted,just='right')}
fig2<-function(){
 q<-m[m$model=='M3',];p<-q[match(c('prevalence_no_problem','prevalence_problem'),q$measure),]
 pd<-q[q$measure=='prevalence_difference',];pr<-q[q$measure=='marginal_PR',]
 stopifnot(all(p$n==8094),all(p$events==429))
 head('SUPPLEMENTARY FIGURE S2','Model-standardized prevalence of loneliness','M3 logistic standardization | common analytic sample: N = 8,094; 429 events')
 tx(.045,.753,'Swallowing problems',11,C$muted,TRUE);tx(.88,.753,'Percent [95% CI]',11,C$muted,TRUE,just='centre')
 xp<-function(z).39+z/12*.36
 for(t in seq(0,12,3)){ln(xp(t),.40,xp(t),.71);tx(xp(t),.37,paste0(t,'%'),11,C$muted,just='centre')}
 ln(xp(0),.40,xp(12),.40,C$muted)
 ys<-c(.635,.48)
 for(i in 1:2){tx(.045,ys[i],c('No swallowing problems','Swallowing problems')[i],13,bold=TRUE);dot(xp(p$estimate[i]*100),ys[i],xp(p$lower[i]*100),xp(p$upper[i]*100),c(C$blue,C$teal)[i],c(16,18)[i]);tx(.88,ys[i],paste0(f(p$estimate[i]*100),' [',f(p$lower[i]*100),', ',f(p$upper[i]*100),']'),12,bold=TRUE,just='centre')}
 tx(.57,.317,'Standardized prevalence of frequent loneliness',11,C$muted,just='centre')
 grid.rect(.5,.235,.91,.10,gp=gpar(fill=C$tint,col=NA))
 tx(.065,.25,'Absolute prevalence difference',11,C$ink,TRUE)
 tx(.065,.215,paste0(f(pd$estimate*100),' percentage points [95% CI ',f(pd$lower*100),', ',f(pd$upper*100),']'),12,C$teal,TRUE)
 tx(.60,.25,'Marginal prevalence ratio',11,C$ink,TRUE)
 tx(.60,.215,paste0(f(pr$estimate),' [95% CI ',f(pr$lower),', ',f(pr$upper),']'),12,C$teal,TRUE)
 foot(c('Frequent loneliness: always or usually lonely. Predictions standardized over the same weighted covariate distribution.',
 'M3 adjusts for demographic, social and health characteristics plus in-person and phone/video contact.',
 'Survey-logistic models; ten income imputations; predictive-margin uncertainty. Associations, not causal effects.'))
}
fig3<-function(){
 head('SUPPLEMENTARY FIGURE S3','The full distribution of loneliness responses','Available exposure and outcome responses: N = 8,231 | survey-weighted percentages')
 tx(.045,.765,'Loneliness frequency',11,C$muted,TRUE)
 tx(.39,.779,'No swallowing problems (n = 7,545)',10.5,C$blue,TRUE)
 tx(.39,.747,'Swallowing problems (n = 686)',10.5,C$teal,TRUE)
 tx(.89,.765,'Percent: no / yes',10.5,C$muted,TRUE,just='centre')
 xp<-function(z).39+z/65*.37;ys<-seq(.675,.315,length.out=5)
 for(t in seq(0,60,15)){ln(xp(t),.247,xp(t),.71);tx(xp(t),.22,paste0(t,'%'),10.5,C$muted,just='centre')}
 ln(xp(0),.247,xp(65),.247,C$muted)
 for(i in 1:5){cat<-c('Never','Rarely','Sometimes','Usually','Always')[i];q<-d[d$category==cat,];q<-q[match(c('swallow_0','swallow_1'),q$label),];tx(.045,ys[i],cat,13,bold=TRUE)
  for(j in 1:2)dot(xp(100*q$prevalence[j]),ys[i]+c(.016,-.016)[j],xp(100*q$lower_KG[j]),xp(100*q$upper_KG[j]),c(C$blue,C$teal)[j],c(16,18)[j])
  tx(.89,ys[i],paste0(f(100*q$prevalence[1],1),' / ',f(100*q$prevalence[2],1)),12,bold=TRUE,just='centre')}
 tx(.575,.173,'Weighted percentage within each exposure group',10.5,C$muted,just='centre')
 foot(c('Points: survey-weighted percentages. Lines: Korn-Graubard 95% confidence intervals; sample sizes are unweighted.',
 'All five categories are shown without covariate adjustment. Each exposure group sums to 100% before rounding.',
 'All ten proportions pass the implemented NCHS precision criteria. Cross-sectional, self-reported responses.'))
}
figs<-list(FigureS2_Standardized_Prevalence=fig2,FigureS3_Loneliness_Distribution=fig3)
for(n in names(figs)){png(file.path(out,paste0(n,'.png')),width=10,height=6.4,units='in',res=300,type='cairo',bg='white');figs[[n]]();dev.off();svg(file.path(out,paste0(n,'.svg')),width=10,height=6.4,bg='white');figs[[n]]();dev.off()}
cairo_pdf(file.path(out,'NHIS2025_Extended_Figures_EN.pdf'),width=10,height=6.4,family='Arial',onefile=TRUE);for(fn in figs)fn();dev.off()
cat('Two supplementary figures created without changing existing figures.\n')
