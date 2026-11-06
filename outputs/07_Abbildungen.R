# Reproduce from project root (no refitting, uses verified analysis tables):
# Rscript -e "Sys.setlocale('LC_ALL','English_United States.utf8'); source('outputs/07_Abbildungen.R',encoding='UTF-8')"
library(grid)
out <- 'outputs/abbildungen'
dir.create(out, recursive=TRUE, showWarnings=FALSE)
m <- read.delim('outputs/tables/model_results.tsv',check.names=FALSE)
p <- read.delim('outputs/tables/weighted_prevalence.tsv',check.names=FALSE)
s <- read.delim('outputs/tables/severity_outcome_complete.tsv',check.names=FALSE)
stopifnot(all(m$lower <= m$estimate),all(m$upper >= m$estimate))
col <- list(ink='#17313F',muted='#526674',grid='#DEE5E9',teal='#007F86',blue='#426A8B',tint='#EAF5F4',white='#FFFFFF')
f <- function(x,n=2) formatC(x,format='f',digits=n,decimal.mark=',')
nn <- function(x) format(x,big.mark='.',decimal.mark=',',scientific=FALSE,trim=TRUE)
ci <- function(a,b,c) paste0(f(a),' [',f(b),'; ',f(c),']')
txt <- function(x,y,label,size=12,colour=col$ink,bold=FALSE,just='left') grid.text(label,x,y,just=just,gp=gpar(fontfamily='Arial',fontsize=size,col=colour,fontface=if(bold) 'bold' else 'plain',lineheight=1.15))
ln <- function(x1,y1,x2,y2,colour=col$grid,lwd=1,lty=1) grid.lines(c(x1,x2),c(y1,y2),gp=gpar(col=colour,lwd=lwd,lty=lty))
bg <- function(x,y,w,h,colour) grid.rect(x,y,w,h,gp=gpar(fill=colour,col=NA))
header <- function(no,title,subtitle) {
 grid.newpage(); bg(.5,.5,1,1,col$white)
 txt(.045,.955,paste0('NHIS 2025  /  ',no,'  /  ALTER AB 65 JAHREN'),10.5,col$teal,TRUE)
 txt(.045,.895,title,21,bold=TRUE)
 txt(.045,.842,subtitle,11.5,col$muted)
}
footer <- function(lines) {
 for(i in seq_along(lines)) txt(.045,.125-(i-1)*.026,lines[i],9.5,col$muted)
 txt(.955,.025,'Quelle: NHIS 2025 Public-use; eigene Survey-Analyse',8.5,col$muted,just='right')
}
axis_pr <- function(xl=.445,xr=.765,y=.235,max=4.5) {
 xp <- function(z) xl+(log(z)-log(.8))/(log(max)-log(.8))*(xr-xl)
 ticks <- if(max>4) c(1,1.5,2,3,4) else c(1,1.5,2,3)
 for(t in ticks) {
  ln(xp(t),y,xp(t),.755,if(t==1) '#7F919B' else col$grid,lwd=if(t==1) 1.2 else .7,lty=if(t==1) 2 else 1)
  txt(xp(t),y-.028,format(t,decimal.mark=','),10.5,col$muted,just='centre')
 }
 ln(xl,y,xr,y,col$muted,.8)
 txt((xl+xr)/2,y-.073,'Prävalenzverhältnis (logarithmische Skala)',10.5,col$muted,just='centre')
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
 header('ABBILDUNG 1','Häufige Einsamkeit nach Schluckbeschwerden','Alter ab 65 Jahren | verfügbare Angaben: N = 8.231 | unadjustiert, surveygewichtet')
 txt(.045,.752,'Schluckbeschwerden',11,col$muted,TRUE)
 txt(.885,.752,'Prozent [95%-KI]',11,col$muted,TRUE,just='centre')
 xp <- function(z) .39+z/15*.37
 for(t in seq(0,15,5)) {ln(xp(t),.29,xp(t),.705,col$grid,.8); txt(xp(t),.26,paste0(t,' %'),11,col$muted,just='centre')}
 ln(xp(0),.29,xp(15),.29,col$muted,.8)
 txt(.575,.208,'Gewichteter Anteil häufig einsamer Personen',11,col$muted,just='centre')
 ys <- c(.615,.425)
 for(i in 1:2) {
  txt(.045,ys[i]+.018,c('Keine Beschwerden','Mit Beschwerden')[i],14,bold=TRUE)
  txt(.045,ys[i]-.025,paste0('n = ',nn(q$n_valid[i]),'; Ereignisse = ',q$n_events[i]),11,col$muted)
  point_ci(xp,ys[i],100*q$prevalence[i],100*q$lower[i],100*q$upper[i],c(col$blue,col$teal)[i],i==2)
  txt(.885,ys[i],ci(100*q$prevalence[i],100*q$lower[i],100*q$upper[i]),12,bold=TRUE,just='centre')
 }
 footer(c('Häufig einsam = immer oder meistens. Schluckbeschwerden: Selbstbericht für die vergangenen 12 Monate.',
 'Punkte: gewichtete Prävalenzen; Linien: designbasierte 95%-Konfidenzintervalle (KI). n und Ereignisse ungewichtet.',
 'Ohne Kovariatenadjustierung. Der Nenner unterscheidet sich von der gemeinsamen Modellstichprobe.'))
}
fig2 <- function() {
 q<-m[match(c('M0','M1','M2','M3_primary','M4_participation'),m$model),]
 stopifnot(all(q$n==8094),all(q$events==429),all(q$measure=='PR'))
 header('ABBILDUNG 2','Zusammenhang nach schrittweiser Adjustierung','Häufige Einsamkeit | mit versus ohne Schluckbeschwerden | N = 8.094; 429 Ereignisse')
 txt(.045,.787,'Modell / zusätzlich berücksichtigte Merkmale',10.5,col$muted,TRUE)
 txt(.88,.787,'PR [95%-KI]',11,col$muted,TRUE,just='centre')
 ys<-c(.713,.616,.519,.422,.325)
 bg(.5,ys[4],.93,.086,col$tint)
 xp<-axis_pr()
 labels<-c('M0  Unadjustiert','M1  Alter und Geschlecht','M2  Soziale und gesundheitliche Merkmale','M3  Persönliche und Telefon-/Videokontakte','M4  Gottesdienst- und Vereinsbesuche')
 detail<-c('Surveygewichtet, ohne Kovariaten','Demografische Adjustierung','Bildung, Einkommen, Partnerschaft u. a.','Primäres Modell','Erweiterte Sensitivitätsanalyse')
 for(i in 1:5) {
  txt(.045,ys[i]+.012,labels[i],11.6,if(i==4) col$teal else col$ink,TRUE)
  txt(.045,ys[i]-.019,detail[i],10.2,col$muted)
  point_ci(xp,ys[i],q$estimate[i],q$lower[i],q$upper[i],if(i==4) col$teal else col$blue,i==4)
  txt(.88,ys[i],ci(q$estimate[i],q$lower[i],q$upper[i]),12,if(i==4) col$teal else col$ink,TRUE,just='centre')
 }
 footer(c('M2 ergänzt Bildung, Familienarmutsquotient, Partnerschaft, Alleinleben, Mobilität, Hören und Schlaganfallanamnese.',
 'Jedes Modell ergänzt das vorherige. M3: Kontakte außerhalb des Haushalts; M4: Teilnahme im vergangenen Jahr.',
 'Surveygewichtete Poisson-Modelle; 95%-KI; zehn Einkommensimputationen. PR = 1: kein Prävalenzunterschied.',
 'Häufig einsam = immer oder meistens. Gleiche Stichprobe; Querschnittsassoziationen ohne Kausalnachweis.'))
}
fig3 <- function() {
 q<-m[match(c('severitylittle','severitymiddle','severitya_lot'),m$term),]
 stopifnot(all(q$n==8093),all(q$events==429))
 ns<-vapply(c('none','little','middle','a_lot'),function(z) sum(s$Freq[s$severity==z]),numeric(1))
 ev<-vapply(c('none','little','middle','a_lot'),function(z) sum(s$Freq[s$severity==z & s$lonely==1]),numeric(1))
 header('ABBILDUNG 3','Zusammenhang nach Schwere der Beschwerden','Sekundäre Analyse | M3-Adjustierung | N = 8.093; 429 Ereignisse')
 txt(.045,.787,'Selbstberichtete Schluckbeschwerden',11,col$muted,TRUE)
 txt(.88,.787,'Adjustiertes PR [95%-KI]',11,col$muted,TRUE,just='centre')
 xp<-axis_pr(); ys<-c(.698,.58,.462,.344)
 for(i in 1:4) {
  txt(.045,ys[i]+.015,c('Keine Beschwerden','Wenig Schwierigkeiten','Mittlere Schwierigkeiten','Starke Schwierigkeiten')[i],13,bold=TRUE)
  txt(.045,ys[i]-.02,paste0('n = ',nn(ns[i]),'; Ereignisse = ',ev[i]),11,col$muted)
  if(i==1) {
   grid.points(unit(xp(1),'npc'),unit(ys[i],'npc'),pch=1,size=unit(2.7,'mm'),gp=gpar(col=col$muted,lwd=1.5))
   txt(.88,ys[i],'1,00 (Referenz)',12,col$muted,just='centre')
  } else {
   point_ci(xp,ys[i],q$estimate[i-1],q$lower[i-1],q$upper[i-1],col$teal)
   txt(.88,ys[i],ci(q$estimate[i-1],q$lower[i-1],q$upper[i-1]),12,bold=TRUE,just='centre')
  }
 }
 footer(c('Häufig einsam = immer oder meistens. Kategorien nach dem Codebook geordnet; keine kontinuierliche Schwere-Skala.',
 'M3: demografische, soziale und gesundheitliche Merkmale sowie persönliche und Telefon-/Videokontakte.',
 'Surveygewichtete Poisson-Modelle; 95%-KI; zehn Einkommensimputationen. n und Ereignisse ungewichtet.',
 'Sekundäre Ergebnisse: nur 22 Ereignisse in der stärksten Kategorie; kein Trendtest und kein Kausalnachweis.'))
}
fig4 <- function() {
 ids<-c('M3_primary','M3_available','M3_no_proxy','M3_depression_matched','M3_depression','M3_broad_endpoint')
 q<-m[match(ids,m$model),]; stopifnot(all(q$measure=='PR'))
 header('ERGÄNZUNG S1','Sensitivitätsanalysen zum primären Zusammenhang','Prävalenzverhältnisse | unterschiedliche Stichproben bzw. Endpunktdefinitionen')
 txt(.045,.787,'Analyse / ungewichtete Fallzahlen',11,col$muted,TRUE)
 txt(.88,.787,'PR [95%-KI]',11,col$muted,TRUE,just='centre')
 ys<-seq(.715,.31,length.out=6); bg(.5,ys[1],.93,.072,col$tint)
 xp<-axis_pr()
 labs<-c('Primäres Modell M3','Alle für M3 vollständigen Fälle','Ohne Proxy-Interviews','Vergleich ohne Depressionsadjustierung','Mit zusätzlicher Depressionsadjustierung','Breiter Endpunkt: auch manchmal einsam')
 for(i in 1:6) {
  txt(.045,ys[i]+.012,labs[i],11.3,if(i==1) col$teal else col$ink,TRUE)
  txt(.045,ys[i]-.019,paste0('N = ',nn(q$n[i]),'; Ereignisse = ',nn(q$events[i])),10.3,col$muted)
  point_ci(xp,ys[i],q$estimate[i],q$lower[i],q$upper[i],if(i==1) col$teal else col$blue,i==1)
  txt(.88,ys[i],ci(q$estimate[i],q$lower[i],q$upper[i]),12,if(i==1) col$teal else col$ink,TRUE,just='centre')
 }
 footer(c('Depressionsvergleich: identische Stichprobe (N = 8.055). Abschwächung ist kein Nachweis einer Mediation.',
 'Primär: immer oder meistens einsam; breit: zusätzlich manchmal. Keine Multiplikitätskorrektur.',
 'Depressions- und breites Endpunktmodell: einzelne angepasste Werte > 1; keine individuellen Wahrscheinlichkeiten.',
 'Surveygewichtete Poisson-Modelle; 95%-KI; zehn Einkommensimputationen. OR-Sensitivität hier nicht dargestellt.'))
}
figs<-list('Abb1_Gewichtete_Praevalenz'=fig1,'Abb2_Modellfolge'=fig2,'Abb3_Schweregrade'=fig3,'AbbS1_Sensitivitaet'=fig4)
for(n in names(figs)) {
 png(file.path(out,paste0(n,'.png')),width=10,height=6.4,units='in',res=300,type='cairo',bg='white'); figs[[n]](); dev.off()
 svg(file.path(out,paste0(n,'.svg')),width=10,height=6.4,family='Arial',bg='white'); figs[[n]](); dev.off()
}
cairo_pdf(file.path(out,'NHIS2025_Abbildungen.pdf'),width=10,height=6.4,family='Arial',onefile=TRUE,bg='white')
for(fn in figs) fn()
dev.off()
# Save the exact plotted inputs as plain text, without transforming model results.
write.table(p[p$group %in% c('no_swallowing_problem','swallowing_problem'),],file.path(out,'Daten_Abb1.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
write.table(m,file.path(out,'Daten_Modelle.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
write.table(s,file.path(out,'Daten_Schwere.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
cat('Created four PNG/SVG figures and a four-page PDF from verified result tables.\n')
