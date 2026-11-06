# Journal artwork derived from the existing, verified result tables.
# Run from the project root: Rscript outputs/manuscript_sources/figures_dysphagia.R
# No statistical model is refitted and no original figure is overwritten.
library(grid)
out <- 'outputs/dysphagia/figures'
dir.create(out, recursive=TRUE, showWarnings=FALSE)
width_in <- 174/25.4
height_in <- 110/25.4
dpi <- 600
m <- read.delim('outputs/tables/model_results.tsv', check.names=FALSE)
p <- read.delim('outputs/tables/weighted_prevalence.tsv', check.names=FALSE)
s <- read.delim('outputs/tables/severity_outcome_complete.tsv', check.names=FALSE)
margins <- read.delim('outputs/extended_tables/standardized_prevalence_and_contrasts.tsv')
distribution <- read.delim('outputs/extended_tables/loneliness_five_categories.tsv')
stopifnot(all(m$lower <= m$estimate), all(m$upper >= m$estimate))
C <- list(ink='#17252E', muted='#44535C', grid='#DCE2E5',
          blue='#426A8B', teal='#007F86', white='#FFFFFF')
fmt <- function(x, n=2) formatC(x, format='f', digits=n, decimal.mark='.')
ci <- function(a,b,c) paste0(fmt(a),' [',fmt(b),', ',fmt(c),']')
tx <- function(x,y,label,size=9,colour=C$ink,bold=FALSE,just='left') {
  grid.text(label,x,y,just=just,
    gp=gpar(fontfamily='Arial',fontsize=size,col=colour,
            fontface=if(bold) 'bold' else 'plain',lineheight=1.12))
}
ln <- function(x1,y1,x2,y2,colour=C$grid,lwd=.7,lty=1) {
  grid.lines(c(x1,x2),c(y1,y2),gp=gpar(col=colour,lwd=lwd,lty=lty))
}
newplot <- function() {
  grid.newpage()
  grid.rect(gp=gpar(fill=C$white,col=NA))
}
point_ci <- function(xp,y,estimate,lower,upper,colour=C$blue,shape=16) {
  stopifnot(lower<=estimate,estimate<=upper)
  ln(xp(lower),y,xp(upper),y,colour,1.1)
  ln(xp(lower),y-.010,xp(lower),y+.010,colour,.8)
  ln(xp(upper),y-.010,xp(upper),y+.010,colour,.8)
  grid.points(unit(xp(estimate),'npc'),unit(y,'npc'),pch=shape,
              size=unit(if(shape==18) 2.4 else 2.1,'mm'),gp=gpar(col=colour))
}
pr_axis <- function(xl=.48,xr=.765,y=.135,top=.87,max=4.5) {
  xp <- function(z) xl+(log(z)-log(.8))/(log(max)-log(.8))*(xr-xl)
  for(t in c(1,1.5,2,3,4)) {
    ln(xp(t),y,xp(t),top,if(t==1) '#7F8C94' else C$grid,
       lwd=if(t==1) .9 else .6,lty=if(t==1) 2 else 1)
    tx(xp(t),y-.040,as.character(t),size=9,colour=C$muted,just='centre')
  }
  ln(xl,y,xr,y,C$muted,.8)
  tx((xl+xr)/2,.035,'Prevalence ratio (log scale)',size=9,just='centre')
  xp
}
prevalence_axis <- function(max=15,ticks=seq(0,15,5),
                            label='Weighted prevalence of frequent loneliness (%)') {
  xp <- function(z) .385+z/max*.38
  for(t in ticks) {
    ln(xp(t),.19,xp(t),.83,C$grid,.6)
    tx(xp(t),.145,as.character(t),size=9,colour=C$muted,just='centre')
  }
  ln(xp(0),.19,xp(max),.19,C$muted,.8)
  tx(.575,.065,label,size=9,just='centre')
  xp
}
fig1 <- function() {
  q <- p[match(c('no_swallowing_problem','swallowing_problem'),p$group),]
  stopifnot(sum(q$n_valid)==8231,sum(q$n_events)==438)
  newplot()
  tx(.025,.93,'Swallowing problems',bold=TRUE)
  tx(.89,.93,'Percent [95% CI]',bold=TRUE,just='centre')
  xp <- prevalence_axis()
  ys <- c(.66,.36)
  for(i in 1:2) {
    tx(.025,ys[i],c('No swallowing problems','Swallowing problems')[i],size=9.5)
    point_ci(xp,ys[i],100*q$prevalence[i],100*q$lower[i],100*q$upper[i],
             c(C$blue,C$teal)[i],c(16,18)[i])
    tx(.89,ys[i],ci(100*q$prevalence[i],100*q$lower[i],100*q$upper[i]),
       size=9,just='centre')
  }
}
fig2 <- function() {
  q <- m[match(c('M0','M1','M2','M3_primary','M4_participation'),m$model),]
  stopifnot(all(q$n==8094),all(q$events==429),all(q$measure=='PR'))
  newplot()
  tx(.025,.94,'Model / additional adjustment',bold=TRUE)
  tx(.89,.94,'PR [95% CI]',bold=TRUE,just='centre')
  xp <- pr_axis()
  ys <- seq(.805,.245,length.out=5)
  labels <- c('M0  Unadjusted','M1  Age and sex',
              'M2  Social and health\n       characteristics',
              'M3  In-person and phone/video\n       contact',
              'M4  Religious and group\n       participation')
  for(i in 1:5) {
    primary <- i==4
    colour <- if(primary) C$teal else C$blue
    tx(.025,ys[i],labels[i],size=9,bold=primary)
    point_ci(xp,ys[i],q$estimate[i],q$lower[i],q$upper[i],colour,if(primary)18 else 16)
    tx(.89,ys[i],ci(q$estimate[i],q$lower[i],q$upper[i]),size=9,
       bold=primary,just='centre')
  }
}
fig3 <- function() {
  q <- m[match(c('severitylittle','severitymiddle','severitya_lot'),m$term),]
  stopifnot(all(q$n==8093),all(q$events==429),sum(s$Freq)==8093)
  newplot()
  tx(.025,.94,'Swallowing difficulty',bold=TRUE)
  tx(.89,.94,'Adjusted PR\n[95% CI]',bold=TRUE,just='centre')
  xp <- pr_axis()
  ys <- seq(.79,.25,length.out=4)
  for(i in 1:4) {
    tx(.025,ys[i],c('No swallowing problems','A little difficulty',
                    'Somewhere in between','A lot of difficulty')[i],size=9.5)
    if(i==1) {
      grid.points(unit(xp(1),'npc'),unit(ys[i],'npc'),pch=1,
                  size=unit(2.1,'mm'),gp=gpar(col=C$muted,lwd=.9))
      tx(.89,ys[i],'1.00 (reference)',size=9,just='centre')
    } else {
      point_ci(xp,ys[i],q$estimate[i-1],q$lower[i-1],q$upper[i-1],C$teal)
      tx(.89,ys[i],ci(q$estimate[i-1],q$lower[i-1],q$upper[i-1]),size=9,just='centre')
    }
  }
}
esm1 <- function() {
  ids <- c('M3_primary','M3_available','M3_no_proxy','M3_depression_matched',
           'M3_depression','M3_broad_endpoint')
  q <- m[match(ids,m$model),]
  stopifnot(all(q$measure=='PR'))
  newplot()
  tx(.025,.95,'Analysis',bold=TRUE)
  tx(.89,.95,'PR [95% CI]',bold=TRUE,just='centre')
  xp <- pr_axis(y=.115,top=.89)
  ys <- seq(.83,.22,length.out=6)
  labels <- c('Primary model M3','All complete cases for M3','Excluding proxy interviews',
              'Without adjustment for\ndepressive feelings',
              'Adjusted for depressive feelings',
              'Broader outcome: includes sometimes')
  for(i in 1:6) {
    primary <- i==1
    tx(.025,ys[i],labels[i],size=9,bold=primary)
    point_ci(xp,ys[i],q$estimate[i],q$lower[i],q$upper[i],
             if(primary) C$teal else C$blue,if(primary)18 else 16)
    tx(.89,ys[i],ci(q$estimate[i],q$lower[i],q$upper[i]),size=9,
       bold=primary,just='centre')
  }
}
esm2 <- function() {
  q <- margins[margins$model=='M3',]
  q <- q[match(c('prevalence_no_problem','prevalence_problem'),q$measure),]
  stopifnot(all(q$n==8094),all(q$events==429))
  newplot()
  tx(.025,.93,'Swallowing problems',bold=TRUE)
  tx(.89,.93,'Percent [95% CI]',bold=TRUE,just='centre')
  xp <- prevalence_axis(max=12,ticks=seq(0,12,3),
    label='Standardized prevalence of frequent loneliness (%)')
  ys <- c(.66,.36)
  for(i in 1:2) {
    tx(.025,ys[i],c('No swallowing problems','Swallowing problems')[i],size=9.5)
    point_ci(xp,ys[i],100*q$estimate[i],100*q$lower[i],100*q$upper[i],
             c(C$blue,C$teal)[i],c(16,18)[i])
    tx(.89,ys[i],ci(100*q$estimate[i],100*q$lower[i],100*q$upper[i]),
       size=9,just='centre')
  }
}
esm3 <- function() {
  newplot()
  # Two keyed legend entries; no figure title or methodological footnotes.
  grid.points(unit(.34,'npc'),unit(.95,'npc'),pch=16,size=unit(2.1,'mm'),gp=gpar(col=C$blue))
  tx(.365,.95,'No swallowing problems',size=9)
  grid.points(unit(.34,'npc'),unit(.90,'npc'),pch=18,size=unit(2.4,'mm'),gp=gpar(col=C$teal))
  tx(.365,.90,'Swallowing problems',size=9)
  tx(.025,.88,'Loneliness frequency',bold=TRUE)
  tx(.91,.88,'Percent\n(no / yes)',size=9,bold=TRUE,just='centre')
  xp <- function(z) .34+z/65*.43
  for(t in seq(0,60,15)) {
    ln(xp(t),.14,xp(t),.83,C$grid,.6)
    tx(xp(t),.10,as.character(t),size=9,colour=C$muted,just='centre')
  }
  ln(xp(0),.14,xp(65),.14,C$muted,.8)
  ys <- seq(.76,.24,length.out=5)
  for(i in 1:5) {
    category <- c('Never','Rarely','Sometimes','Usually','Always')[i]
    q <- distribution[distribution$category==category,]
    q <- q[match(c('swallow_0','swallow_1'),q$label),]
    stopifnot(nrow(q)==2)
    tx(.025,ys[i],category,size=9.5)
    for(j in 1:2) {
      point_ci(xp,ys[i]+c(.018,-.018)[j],100*q$prevalence[j],
               100*q$lower_KG[j],100*q$upper_KG[j],
               c(C$blue,C$teal)[j],c(16,18)[j])
    }
    tx(.91,ys[i],paste0(fmt(100*q$prevalence[1],1),' / ',fmt(100*q$prevalence[2],1)),
       size=9,just='centre')
  }
  tx(.56,.035,'Weighted percentage within each exposure group (%)',size=9,just='centre')
}

figures <- list(Fig1=fig1,Fig2=fig2,Fig3=fig3,
                ESM1_Fig1=esm1,ESM1_Fig2=esm2,ESM1_Fig3=esm3)
stopifnot(capabilities('cairo'),capabilities('png'),capabilities('tiff'))
for(name in names(figures)) {
  png(file.path(out,paste0(name,'.png')),width=width_in,height=height_in,
      units='in',res=dpi,type='cairo',bg='white')
  figures[[name]](); dev.off()
  tiff(file.path(out,paste0(name,'.tiff')),width=width_in,height=height_in,
       units='in',res=dpi,type='cairo',compression='lzw',bg='white')
  figures[[name]](); dev.off()
  cairo_pdf(file.path(out,paste0(name,'.pdf')),width=width_in,height=height_in,
            family='Arial',onefile=FALSE,bg='white',fallback_resolution=dpi)
  figures[[name]](); dev.off()
  cairo_ps(file.path(out,paste0(name,'.eps')),width=width_in,height=height_in,
           family='Arial',onefile=FALSE,bg='white',fallback_resolution=dpi)
  figures[[name]](); dev.off()
}

# Preserve full methodological captions outside the artwork, using journal labels.
original <- paste(readLines('outputs/figures_en/Captions_and_Notes.txt',warn=FALSE),collapse='\n')
main_start <- regexpr('Figure 1. Survey-weighted',original,fixed=TRUE)[1]
main_end <- regexpr('\nGeneral interpretation',original,fixed=TRUE)[1]
captions <- substr(original,main_start,main_end-1)
captions <- sub('Figure 1.','Fig. 1',captions,fixed=TRUE)
captions <- sub('Figure 2.','Fig. 2',captions,fixed=TRUE)
captions <- sub('Figure 3.','Fig. 3',captions,fixed=TRUE)
captions <- sub('Supplementary Figure S1.','Online Resource 1, Fig. S1',captions,fixed=TRUE)
captions <- sub('a diamond, color and row shading','a diamond and color',captions,fixed=TRUE)
captions <- sub('Points and lines indicate PRs and 95% confidence intervals.',
                'Points and lines indicate prevalence ratios (PRs) and 95% confidence intervals.',
                captions,fixed=TRUE)
captions <- gsub('NHIS 2025.\n','NHIS 2025\n',captions,fixed=TRUE)
extended <- paste(readLines('outputs/figures_en/Captions_Extended_Figures_EN.txt',warn=FALSE),collapse='\n')
extended <- substr(extended,1,regexpr('\nReproduction',extended,fixed=TRUE)[1]-1)
extended <- sub('Supplementary Figure S2.','Online Resource 1, Fig. S2',extended,fixed=TRUE)
extended <- sub('Supplementary Figure S3.','Online Resource 1, Fig. S3',extended,fixed=TRUE)
extended <- sub('The displayed sample sizes','The sample sizes',extended,fixed=TRUE)
extended <- gsub('NHIS 2025.\n','NHIS 2025\n',extended,fixed=TRUE)
pd <- margins[margins$model=='M3' & margins$measure=='prevalence_difference',]
pr <- margins[margins$model=='M3' & margins$measure=='marginal_PR',]
contrast <- paste0('Related estimates for Online Resource 1, Fig. S2: absolute prevalence difference ',
                   fmt(100*pd$estimate),' percentage points (95% CI ',
                   fmt(100*pd$lower),', ',fmt(100*pd$upper),'); marginal prevalence ratio ',
                   fmt(pr$estimate),' (95% CI ',fmt(pr$lower),', ',fmt(pr$upper),').')
writeLines(c('DYSPHAGIA FIGURE CAPTIONS - SEPARATE FROM ARTWORK','',captions,'',extended,'',contrast,
             '',paste('Software: R',getRversion(),'with the grid graphics package and Cairo graphics devices.'),
             'Artwork: 174 x 110 mm; PNG and LZW-compressed TIFF at 600 dpi; Cairo PDF and EPS vector files.',
             'File mapping: Fig1-Fig3 = main figures; ESM1_Fig1-Fig3 = Online Resource 1, Figs. S1-S3.',
             'The 174-mm width is an implementation choice, not a verified journal-specific size mandate.'),
           file.path(out,'Figure_captions.txt'),useBytes=TRUE)
inputs <- c('outputs/tables/model_results.tsv','outputs/tables/weighted_prevalence.tsv',
            'outputs/tables/severity_outcome_complete.tsv',
            'outputs/extended_tables/standardized_prevalence_and_contrasts.tsv',
            'outputs/extended_tables/loneliness_five_categories.tsv')
write.table(data.frame(path=inputs,md5=unname(tools::md5sum(inputs))),
            file.path(out,'Source_table_checksums.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
cat('Created 6 journal figures in PNG, TIFF, PDF and EPS, with separate captions; no models refitted.\n')
