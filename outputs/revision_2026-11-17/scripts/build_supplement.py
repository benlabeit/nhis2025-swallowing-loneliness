"""Build supplementary PDF tables and machine-readable workbook inputs from R outputs."""
import csv,json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader,PdfWriter
B=Path('outputs/revision_2026-11-17');Q=Path('work/revision_2026-11-17');Q.mkdir(parents=True,exist_ok=True)
def rd(p):
 with (B/p).open() as f:return list(csv.DictReader(f,delimiter='\t'))
def find(rows,**kw):return next(r for r in rows if all(r[k]==v for k,v in kw.items()))
def ci(r,key='estimate'):return f'{float(r[key]):.2f} ({float(r["lower"]):.2f}-{float(r["upper"]):.2f})'
s=getSampleStyleSheet();s['Normal'].fontName='Helvetica';s['Normal'].fontSize=10;s['Normal'].leading=14
s['Title'].fontName='Helvetica-Bold';s['Title'].fontSize=17;s['Title'].leading=21
flow=[]
def p(text,style='Normal'):flow.append(Paragraph(escape(text),s[style]));flow.append(Spacer(1,8))
def table(rows,widths):
 data=[[Paragraph(escape(str(c)),s['Normal']) for c in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eaf0')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#c8cdd2')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));flow.append(t);flow.append(Spacer(1,12))
m=rd('tables/model_results.tsv');e=rd('expanded_adjustment.tsv')
p('Supplementary Material S1','Title')
p('Swallowing problems and frequent loneliness in NHIS 2025. Revision using self-reports as the primary sample and ten official income imputations.')
p('Table S1. Sequential adjustment models','Heading2')
rows=[['Model','N','PR (95% CI)']]
for key,label in [('M0','M0: unadjusted'),('M1','M1: age and sex'),('M2','M2: social and health factors'),('M3_primary','M3: additionally social contact'),('M4_participation','M4: additionally participation')]:
 r=find(m,model=key);rows.append([label,f'{int(r["n"]):,}',ci(r)])
table(rows,[280,65,160])
p('All models use the same 7,829 self-respondents and 411 frequent-loneliness events. M3 is primary. Poisson log-link models use survey weights, strata and PSUs. Coefficients and design-based covariance matrices are pooled across ten income imputations with finite degrees of freedom. PR denotes prevalence ratio.')
p('Text S1. Income imputation counts','Heading2')
p('Income was imputed for 1,911 of 7,829 primary-analysis respondents (24.4%). This includes both fully imputed income (IMPINCFLG_A=1) and income imputed within reported brackets (IMPINCFLG_A=2). Income category counts vary across the ten imputations; the workbook reports their range. Income percentages average the ten completed datasets. Other displayed covariates use complete cases.')
p('Primary descriptive sample: 7,959 self-respondents with valid exposure and outcome. There were 8,204 age-eligible self-respondents after excluding 288 proxy interviews. Within the otherwise complete original regression sample, exclusion of 265 proxy interviews reduced N from 8,094 to 7,829. Reintroducing proxies gave PR 1.83 (1.42-2.38).')
flow.append(PageBreak())
p('Table S2. Additional adjustment blocks','Heading2')
rows=[['Model','N','PR (95% CI)']]
for key,label in [('M3_same_sample','M3 on expanded complete sample'),('cognitive','Plus cognitive block'),('sensory','Plus sensory block'),('full','Plus comorbidity score')]:
 r=find(e,model=key);rows.append([label,f'{int(r["n"]):,}',ci(r,'PR')])
table(rows,[280,65,160])
p('The common expanded sample contains 7,773 self-respondents, 623 with swallowing problems and 405 frequent-loneliness events (77 among respondents with swallowing problems). Missing additional covariates or comparison exposures excluded 56 people from the primary regression sample.')
p('Cognitive block: diagnosed dementia (DEMENEV_A), remembering/concentrating difficulty (COGMEMDFF_A) and communication difficulty (COMDIFF_A). Sensory block: vision difficulty (VISIONDF_A); hearing is already in M3. Difficulty covariates use none, some, or a lot/unable.')
p('The custom comorbidity score assigns one point for myocardial infarction, COPD or current asthma, the broad arthritis item and diabetes, and two points for cancer other than nonmelanoma skin cancer. It is categorized as 0, 1, 2 or at least 3. Stroke and dementia are modeled separately. The score is incomplete and is not a validated Charlson index. The arthritis item includes noninflammatory conditions. Cancer is retained when another malignancy coexists with nonmelanoma skin cancer. Refused/unknown responses remain missing unless a known component establishes a positive composite; valid structural skips are distinguished from missing responses.')
rows=[['Sensitivity analysis','N','PR (95% CI)']]
for key,label in [('full_M3_available','Expanded model, M3-available sample'),('full_without_communication','Swallowing, no communication adjustment'),('full_without_arthritis_score','Swallowing, score without arthritis'),('full_dep_matched','Before depression adjustment, matched sample'),('full_depression','After depression adjustment, matched sample')]:
 r=find(e,model=key);rows.append([label,f'{int(r["n"]):,}',ci(r,'PR')])
table(rows,[280,65,160])
flow.append(PageBreak())
p('Table S3. Comparison exposures','Heading2')
rows=[['Exposure','M3 PR (95% CI)','Expanded PR (95% CI)']]
for name,label in [('swallow','Swallowing problems'),('voice','Voice problems'),('speech','Speech problems'),('vision_exposure','Vision problems')]:
 a=find(e,model='M3_same_sample' if name=='swallow' else name+' M3');b=find(e,model='full' if name=='swallow' else name+' full');rows.append([label,ci(a,'PR'),ci(b,'PR')])
table(rows,[165,170,170])
p('All comparisons use the same 7,773 self-respondents. The exposure is replaced while other covariates are retained; vision is omitted as a covariate when vision difficulty is the exposure. Voice and speech refer to problems in the previous 12 months; vision exposure is any difficulty. All analyses pool ten income imputations.')
p('The exposure measures differ and may overlap. In particular, communication difficulty can overlap with speech problems. Omitting communication adjustment yields a speech PR of '+ci(find(e,model='speech_without_communication'),'PR')+'. No formal between-exposure test was performed. A significant association for one exposure and a nonsignificant association for another does not establish a difference. The analyses do not rule out unmeasured confounding or demonstrate a swallowing-specific causal effect.')
p('Figures S1-S3 follow. Figure S1 compares primary and sensitivity estimates, including proxy interviews as a sensitivity analysis. Figure S2 displays logistic model-standardized prevalences. Figure S3 shows all five loneliness response categories. Counts are unweighted; estimates account for the survey design. These are cross-sectional associations, not intervention effects.')
tmp=Q/'supplement_tables.pdf'
SimpleDocTemplate(str(tmp),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=40,bottomMargin=40).build(flow)
writer=PdfWriter()
writer.append(tmp)
writer.append(B/'figures_en/NHIS2025_Figures_EN.pdf',pages=[3])
writer.append(B/'figures_en/NHIS2025_Extended_Figures_EN.pdf')
with (B/'NHIS2025_Supplement_S1.pdf').open('wb') as f:writer.write(f)

# Prepare typed data for the artifact-tool workbook, without recalculating R estimates in Excel.
spec=[('Models','tables/model_results.tsv'),('Absolute estimates','extended_tables/standardized_prevalence_and_contrasts.tsv'),('Expanded adjustment','expanded_adjustment.tsv'),('Participant flow','tables/participant_flow.tsv'),('Characteristics','extended_tables/table1_characteristics.tsv'),('Income','extended_tables/table1_income_ten_imputations.tsv'),('Missing values','tables/missing_65plus.tsv'),('Additional missingness','expanded_missingness.tsv'),('Precision','extended_tables/NCHS_precision_primary_prevalences.tsv'),('Included and excluded','extended_tables/included_excluded_characteristics.tsv'),('Response weighting','extended_tables/response_weighted_M3_PR.tsv'),('Response diagnostics','extended_tables/response_weight_diagnostics.tsv'),('Model diagnostics','tables/model_diagnostics.tsv'),('Loneliness categories','extended_tables/loneliness_five_categories.tsv'),('Ordinal diagnostics','extended_tables/proportional_odds_diagnostics.tsv'),('Threshold estimates','extended_tables/threshold_specific_swallowing_OR.tsv'),('Severity counts','tables/severity_outcome_complete.tsv'),('Raw response codes','tables/raw_frequencies_65plus.tsv')]
def typed(rows):
 keys=list(rows[0]);numeric=set()
 for k in keys:
  vals=[r[k] for r in rows if r[k] not in ('NA','')]
  try:
   for v in vals:float(v)
   if vals:numeric.add(k)
  except ValueError:pass
 return [keys]+[[None if r[k] in ('NA','') else (float(r[k]) if k in numeric else r[k]) for k in keys] for r in rows]
sheets=[{'name':name,'source':path,'values':typed(rd(path))} for name,path in spec]
coeff=[]
for path in sorted((B/'tables').glob('coefficients_*.tsv')):coeff.extend(rd(str(path.relative_to(B))))
sheets.append({'name':'All coefficients','source':'tables/coefficients_*.tsv','values':typed(coeff)})
dictionary=[['Variable','Definition'],['Population','Self-respondents aged 65+; PROXYFLAG_A=2. AGE65 fallback retained for descriptive eligibility.'],['Exposure','VSLSWYR_A: 1 yes, 2 no. Refused/unknown missing.'],['Outcome','LONELY_A: 1-2 frequent; 3-5 not frequent. Broad endpoint 1-3 vs 4-5.'],['Primary adjustment','Age group, sex, education, income/poverty, partner, living alone, mobility, hearing, stroke, in-person contact and phone/video contact.'],['Income','Ten official income imputations. Rubin pooling with finite design degrees of freedom.'],['Difficulty coding','1 none; 2 some; 3-4 a lot/unable.'],['Dementia','DEMENEV_A: yes/no.'],['Cognition','COGMEMDFF_A: remembering/concentrating difficulty.'],['Communication','COMDIFF_A: difficulty understanding/being understood.'],['Vision','VISIONDF_A: difficulty; comparison exposure any difficulty.'],['Voice and speech','VSLVYR1_A and VSLSPYR_A, previous 12 months.'],['Custom score','MI, COPD/current asthma, broad arthritis, diabetes: 1 each; cancer excluding nonmelanoma-only skin cancer: 2; groups 0/1/2/3+. Not validated Charlson.'],['Missingness','Unknown/refused not coded as no. Structural skips follow questionnaire universe.'],['Interpretation','Cross-sectional associations. No formal between-exposure test. Different significance statuses do not prove different associations.'],['Source','https://www.cdc.gov/nchs/nhis/documentation/2025-nhis.html'],['Repository','https://github.com/benlabeit/nhis2025-swallowing-loneliness'],['Reproduction','Run scripts/RunRevision.R from repository root. Exact recoding in the R scripts; values are static calculated results.']]
sheets.append({'name':'Definitions and sources','source':'R scripts and CDC codebook','values':dictionary})
(Q/'workbook_inputs.json').write_text(json.dumps(sheets))
print('Supplement PDF pages:',len(PdfReader(B/'NHIS2025_Supplement_S1.pdf').pages),'Workbook sheets:',len(sheets))
