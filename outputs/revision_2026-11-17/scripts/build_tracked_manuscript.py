"""Revise the supplied SSK manuscript with true Word revisions by Cinja.

Run from the repository root. Pass the original DOCX as the first argument.
Existing citation fields, comments, relationships and unrelated text are preserved.
The accepted/rejected views are structurally verified; clean view is internal QA only.
"""
import copy, csv, difflib, json, re, sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

BASE=Path('outputs/revision_2026-11-17')
SRC=Path(sys.argv[1])
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+NS['w']+'}'
DATE='2026-11-17T12:00:00Z'
def read(name):
    with (BASE/name).open() as f:return list(csv.DictReader(f,delimiter='\t'))
def select(rows,**kw):return next(r for r in rows if all(r[k]==str(v) for k,v in kw.items()))
def fmt(x,d=2):return f'{float(x):.{d}f}'
def ci(r,d=2,scale=1,key='estimate'):
    return f'{float(r[key])*scale:.{d}f} ({float(r["lower"])*scale:.{d}f}–{float(r["upper"])*scale:.{d}f})'
def tx(p):return ''.join(p.xpath('.//w:t[not(ancestor::w:del)]/text()',namespaces=NS))
def flat(r):return [tx(p) for p in r.xpath('//w:p',namespaces=NS)]
with ZipFile(SRC) as z: parts={n:z.read(n) for n in z.namelist()}
root=E.fromstring(parts['word/document.xml']); original=copy.deepcopy(root)
ps=root.xpath('//w:body/w:p',namespaces=NS);oldps=[tx(p) for p in ps]
ids=[int(i) for i in root.xpath('//@w:id',namespaces=NS) if i.isdigit()]
revision=max(ids+[0])+1
changes=[]
def run(text,props,deleted=False):
    r=E.Element(W+'r')
    if props is not None:r.append(copy.deepcopy(props))
    t=E.SubElement(r,W+('delText' if deleted else 't'));t.text=text;t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    return r
def rev(kind,text,props):
    global revision
    el=E.Element(W+kind,{W+'id':str(revision),W+'author':'Cinja',W+'date':DATE});revision+=1
    el.append(run(text,props,kind=='del'));return el
def replace_span(p,start,end,new):
    nodes=[];pos=0
    for t in p.xpath('.//w:t[not(ancestor::w:del)]',namespaces=NS):
        s=t.text or '';nodes.append((t,pos,pos+len(s)));pos+=len(s)
    affected=[x for x in nodes if x[1]<end and x[2]>start] if end>start else [x for x in nodes if x[1]<=start<=x[2]][-1:]
    assert affected,(start,end,new,tx(p))
    first=True
    for t,a,b in affected:
        r=t.getparent();assert r.tag==W+'r'
        assert len(r.findall(W+'t'))==1
        props=r.find(W+'rPr');s=t.text or '';lo=max(0,start-a);hi=min(len(s),end-a)
        parent=r.getparent();idx=parent.index(r);pieces=[]
        if s[:lo]:pieces.append(run(s[:lo],props))
        if hi>lo:pieces.append(rev('del',s[lo:hi],props))
        if first and new:pieces.append(rev('ins',new,props))
        if s[hi:]:pieces.append(run(s[hi:],props))
        for q in pieces:parent.insert(idx,q);idx+=1
        r.remove(t)
        if all(c.tag==W+'rPr' for c in r):parent.remove(r)
        first=False
def change(p,new):
    old=tx(p)
    if old==new:return
    aa=re.findall(r'\S+\s*|\s+',old);bb=re.findall(r'\S+\s*|\s+',new)
    apos=[0];bpos=[0]
    for t in aa:apos.append(apos[-1]+len(t))
    for t in bb:bpos.append(bpos[-1]+len(t))
    for op,a,b,c,d in reversed(difflib.SequenceMatcher(None,aa,bb,autojunk=False).get_opcodes()):
        if op!='equal':replace_span(p,apos[a],apos[b],''.join(bb[c:d]))
    assert tx(p)==new,(old,new,tx(p))
    changes.append({'old':old,'new':new})
def setp(i,new):change(ps[i],new)
def exact(p,old,new):
    if old==new:return
    before=tx(p);assert before.count(old)==1,(old,before)
    start=before.index(old);replace_span(p,start,start+len(old),new)
    assert tx(p)==before.replace(old,new)
    changes.append({'old':before,'new':tx(p)})
def edit(i,pairs):
    text=oldps[i]
    for a,b in pairs:
        assert a in text,(i,a)
        text=text.replace(a,b)
    setp(i,text)
def append_para(after,text):
    p=E.Element(W+'p');pr=after.find(W+'pPr')
    if pr is not None:p.append(copy.deepcopy(pr))
    # Track the inserted paragraph mark as well as its content.
    pr=p.find(W+'pPr')
    if pr is None:pr=E.SubElement(p,W+'pPr')
    rp=pr.find(W+'rPr')
    if rp is None:rp=E.SubElement(pr,W+'rPr')
    global revision
    E.SubElement(rp,W+'ins',{W+'id':str(revision),W+'author':'Cinja',W+'date':DATE});revision+=1
    props=after.find('.//'+W+'rPr');p.append(rev('ins',text,props))
    after.addnext(p);changes.append({'old':'','new':text});return p

setp(20,'Results: Among 7,959 self-respondents with valid exposure and outcome data, weighted frequent loneliness prevalence was 10.8% with swallowing problems and 4.0% without. The common regression sample included 7,829 respondents. The primary adjusted PR was 1.99 (95% confidence interval [CI] 1.55–2.56). Standardized prevalence was 8.4% versus 4.1%, with a difference of 4.3 percentage points (95% CI 2.3–6.2). Adjusted PRs increased across swallowing-difficulty categories. Additional cognitive, sensory, and comorbidity adjustment yielded a PR of 1.68 (1.29–2.17).')
edit(19,[('Exposure was a self-reported','Primary analyses excluded proxy interviews. Exposure was a self-reported')])
edit(29,[('depressive feelings, participation, missing-data selection, proxy responses, and the full loneliness response distribution.','depressive feelings, participation, missing-data selection, inclusion of proxy responses, additional cognitive, sensory, and comorbidity adjustment, comparison exposures, and the full loneliness response distribution.')])
edit(34,[('Of 8,492 eligible respondents, 8,231 had valid swallowing and loneliness responses. Sequential models used the same 8,094 respondents','Of 8,492 age-eligible respondents, 288 had proxy interviews. Primary analyses were restricted to the remaining 8,204 self-respondents because loneliness is subjective; 7,959 had valid swallowing and loneliness responses. Sequential models used the same 7,829 respondents')])
edit(41,[('Weighted descriptive estimates used valid responses for each measure.','Primary descriptive and regression analyses were restricted to self-respondents (PROXYFLAG_A=2). Weighted descriptive estimates used valid responses for each measure.')])
edit(43,[('R 4.6.0, survey 4.5, and mitools 2.7','R 4.5.3, survey 4.5, and mitools 2.4')])
edit(45,[('We also excluded proxy interviews','We also reintroduced proxy interviews')])
append_para(ps[45], 'We added three cumulative adjustment blocks to M3: cognitive (diagnosed dementia, difficulty remembering or concentrating, and difficulty communicating), sensory (vision difficulty; hearing was already included), and comorbidity. Difficulty measures were grouped as none, some, or a lot/unable. A custom comorbidity score assigned one point each for myocardial infarction, COPD or current asthma, the broad NHIS arthritis item, and diabetes, and two points for cancer other than nonmelanoma skin cancer; categories were 0, 1, 2, and at least 3 points. Stroke and dementia were modeled separately. This partially observed score is not a validated Charlson index. Unknown responses remained missing; questionnaire skips were handled according to the item universe. All block models used the same complete sample and all ten income imputations. Voice, speech, and vision problems were examined as comparison exposures on that sample; vision was omitted as a covariate when it was the exposure. Voice and speech symptoms were not added as covariates to the swallowing model because they may represent overlapping manifestations of disease. These exploratory comparisons do not identify causal specificity; communication adjustment may particularly attenuate speech associations. Sensitivities omitted communication adjustment or the arthritis score component. Exact recoding and results are provided in Supplementary Material S2.')
edit(47,[('among 8,468 respondents with known numeric age of at least 65 years.','among 8,180 self-respondents with known numeric age of at least 65 years.'),('presence of any children, and proxy status.','presence of any children. Proxy status was constant after restriction to self-respondents and was therefore omitted.')])
setp(54,'The age-eligible sample comprised 8,468 respondents with numeric age of at least 65 years and 24 whose age eligibility was established only by AGE65. Excluding 288 proxy interviews left 8,204 self-respondents. Swallowing status was valid for 7,965 and loneliness for 7,970; both were valid for 7,959. The common regression sample included 7,829 respondents, with 411 frequent-loneliness events; 265 proxy interviews had been excluded from the otherwise complete sample of 8,094. Of the self-respondents, 628 reported swallowing problems, including 78 with frequent loneliness; 7,201 reported no swallowing problems, including 333 with frequent loneliness. The older self-respondent domain included 46 strata and 608 primary sampling units. The common regression domain retained 607 primary sampling units and 561 design degrees of freedom. Income had been imputed for 1,911 respondents (24.4%, unweighted) in the common analytic sample.')
edit(55,[('8.1% (95% CI 7.5–8.8)','7.6% (95% CI 6.9–8.2)'),('4.7% (4.2–5.2)','4.5% (4.0–5.1)'),('10.3% (8.2–13.0)','10.8% (8.4–13.7)'),('4.2% (3.7–4.7)','4.0% (3.5–4.6)')])
edit(56,[('39.5% versus 54.8%','39.3% versus 55.4%'),('25.1% versus 18.2%','24.8% versus 17.8%'),('4.5% versus 1.8%','5.0% versus 1.7%'),('5.9% versus 2.4%','5.8% versus 2.3%')])
edit(58,[('2.48 (95% CI 1.90–3.24)','2.68 (95% CI 2.03–3.53)'),('PR 2.47','PR 2.66'),('1.94 (1.49–2.53)','2.12 (1.64–2.74)'),('1.83 (1.42–2.38)','1.99 (1.55–2.56)'),('1.85 (1.43–2.38)','2.00 (1.56–2.56)')])
edit(59,[('8,093','7,828'),('1.49 (95% CI 1.01–2.19)','1.55 (95% CI 1.07–2.26)'),('1.92 (1.33–2.77)','2.04 (1.40–2.97)'),('2.69 (1.76–4.11)','3.21 (2.17–4.75)'),('361, 199, and 113','338, 188, and 101'),('33, 27, and 22','31, 25, and 22')])
setp(61,'In the primary logistic standardization, estimated frequent loneliness prevalence was 4.1% (95% CI 3.6–4.7) under the no-problem exposure setting and 8.4% (6.6–10.5) under the swallowing-problem setting. The pooled prevalence difference was 4.3 percentage points (2.3–6.2), and the marginal PR was 2.03 (1.57–2.63) (Table 2; Supplementary Material S1, Figure S2).')
setp(62,'The depression-complete sample included 7,796 respondents. Within this sample, the PR was 2.00 (95% CI 1.56–2.57) before and 1.61 (1.26–2.06) after adding frequent depressive feelings. Depression-adjusted logistic standardization gave a prevalence difference of 2.9 percentage points (1.1–4.6). This attenuation is compatible with overlapping or shared psychosocial processes but does not quantify mediation. Including proxy interviews yielded a PR of 1.83 (1.42–2.38; n=8,094). The broader loneliness definition yielded a PR of 1.30 (1.15–1.46), and its standardized prevalence difference was 7.3 percentage points (3.6–11.0). The primary logistic conditional odds ratio was 2.21 (1.65–2.98); it is a different estimand from the prevalence ratio (Supplementary Material S1, Figure S1).')
append_para(ps[62],'Expanded adjustment used 7,773 self-respondents with complete additional covariates and comparison exposures, including 623 with swallowing problems and 405 frequent-loneliness events overall (77 among those with swallowing problems). On this same sample, the M3 PR was 2.01 (95% CI 1.56–2.59), decreasing to 1.77 (1.38–2.26) after cognitive adjustment, 1.73 (1.34–2.24) after sensory adjustment, and 1.68 (1.29–2.17) after the comorbidity score. Fully adjusted PRs were 1.31 (0.99–1.73) for voice problems, 0.94 (0.67–1.30) for speech problems, and 1.16 (0.91–1.47) for vision problems. No formal between-exposure comparison was performed. Omitting communication adjustment yielded a speech PR of 1.12 (0.79–1.58); omitting arthritis from the score yielded a swallowing PR of 1.69 (1.31–2.20). Additional depressive-feelings adjustment on 7,741 respondents yielded a PR of 1.48 (1.14–1.92), versus 1.68 (1.29–2.18) before depression adjustment on that sample (Supplementary Material S1, Tables S2–S3; Supplementary Material S2).')
edit(63,[('95.3%','95.5%'),('0.980 to 1.230','0.982 to 1.128'),('1.83 (95% CI 1.41–2.37)','2.00 (95% CI 1.55–2.57)'),('1.83 (1.41–2.38)','2.00 (1.55–2.57)')])
setp(64,'Two of 69 proportional-odds diagnostic contrasts rejected equality after Bonferroni adjustment. We therefore did not report a single common ordinal odds ratio. Exposure-specific cumulative odds ratios were 1.56 (95% CI 1.27–1.94) for at least rarely, 1.54 (1.25–1.90) for at least sometimes, 2.21 (1.65–2.98) for at least usually, and 2.03 (1.39–2.97) for always. Rejection was not itself evidence that the swallowing coefficient differed across thresholds. Some supplementary Poisson models produced fitted values above one; probability estimates were consequently taken from logistic standardization.')
edit(68,[('In this national survey of older noninstitutionalized US adults,','Among self-respondents in this national survey of older noninstitutionalized US adults,'),('1.83 and standardized difference of approximately 3.7','1.99 and standardized difference of approximately 4.3'),('proxy-exclusion analysis','proxy-inclusion sensitivity analysis')])
append_para(ps[75],'The association also persisted after additional adjustment for measured cognitive, sensory, and comorbidity characteristics, which argues against complete explanation by these particular measured factors. This does not exclude residual confounding or establish a swallowing-specific causal effect. The comparison exposures had different measurement properties, and communication adjustment may remove relevant variation from the speech comparison. Differences in statistical significance are not evidence of differences between associations; the confidence intervals overlap and no formal contrast was tested.')
edit(79,[('Proxy exclusion addresses one aspect of reporting but does not eliminate measurement error.','Restricting the primary analyses to self-respondents avoids substituting another person’s judgment for subjective loneliness but may underrepresent people unable to respond because of illness or cognitive impairment. It does not eliminate measurement error.')])
edit(80,[('Residual confounding, overadjustment, and measurement error remain possible.','The custom comorbidity score is incomplete and not a validated Charlson index; the broad arthritis item does not isolate inflammatory connective-tissue disease. Residual confounding, overadjustment, and measurement error remain possible.')])
edit(82,[('among older noninstitutionalized US adults','among self-responding older noninstitutionalized US adults'),('Additional adjustment for participation produced a similar prevalence ratio.','Additional adjustment for participation produced a similar prevalence ratio, and the association persisted after further cognitive, sensory, and comorbidity adjustment.')])
edit(105,[('Figures S1–S3, Table S1, and Text S1','Figures S1–S3, Tables S1–S3, and Text S1')])
edit(139,[('7,386 and 669 because 34 and 5','7,171 and 625 because 30 and 3')])
edit(143,[('8,055','7,796')])
edit(147,[('8,231 adults','7,959 self-responding adults'),('7,545 adults and 355 events','7,321 adults and 340 events'),('686 adults and 83 events','638 adults and 79 events')])
edit(149,[('8,094 adults','7,829 self-responding adults'),('429 frequent-loneliness events','411 frequent-loneliness events')])
edit(151,[('8,093 adults and 429 events','7,828 self-responding adults and 411 events'),('7,420/347','7,201/333'),('361/33','338/31'),('199/27','188/25'),('113/22','101/22')])
edit(153,[('Table S1, sequential adjustment models;','Table S1, sequential adjustment models; Table S2, additional adjustment blocks; Table S3, comparison exposures;')])

tables=root.xpath('//w:tbl',namespaces=NS)
for p in tables[0].xpath('.//w:p',namespaces=NS):
    if 'primary adjusted prevalence ratio' in tx(p):change(p,tx(p).replace('1.83','1.99').replace('3.7','4.3'))
def cell_change(cell,new):
    pp=cell.xpath('./w:p',namespaces=NS);assert len(pp)==1
    change(pp[0],new)
rows=tables[1].xpath('./w:tr',namespaces=NS)
for j,n in [(1,'7,201'),(2,'628')]:
    cell=rows[0].xpath('./w:tc',namespaces=NS)[j]
    exact(cell.find(W+'p'),'7,420' if j==1 else '674',n)
data=read('manuscript_table1.tsv');income=read('extended_tables/table1_income_ten_imputations.tsv')
mapping={1:'age65',2:'age75',3:'age85',4:'female',5:'edu1',6:'edu2',7:'edu3',8:'edu4',13:'partner',14:'alone',15:'mobility',16:'hearing',17:'stroke',18:'contact1',19:'contact2',20:'depression',21:'proxy'}
for ri,key in mapping.items():
    cells=rows[ri].xpath('./w:tc',namespaces=NS)
    for a in (0,1):
        rr=select(data,variable=key,swallow=a)
        cell_change(cells[a+1],f'{float(rr["percent"]):.1f} ({int(rr["count"]):,})')
for ri,cat in enumerate(['Below 100%','100 to <200%','200 to <400%','400% or more'],9):
    cells=rows[ri].xpath('./w:tc',namespaces=NS)
    for a in (0,1):
        rr=select(income,population='common',swallow=a,category=cat)
        cell_change(cells[a+1],f'{float(rr["weighted_percent"]):.1f} ({int(rr["n_min"]):,}-{int(rr["n_max"]):,})')
marg=read('extended_tables/standardized_prevalence_and_contrasts.tsv')
for ri,model in enumerate(['M3','M3_depression_matched','M3_depression','M3_broad'],1):
    cells=tables[2].xpath('./w:tr',namespaces=NS)[ri].xpath('./w:tc',namespaces=NS)
    rr=select(marg,model=model,measure='prevalence_no_problem');cell_change(cells[1],f'{int(rr["n"]):,}')
    for j,measure in enumerate(['prevalence_no_problem','prevalence_problem','prevalence_difference','marginal_PR'],2):
        rr=select(marg,model=model,measure=measure)
        p=cells[j].find(W+'p');before=tx(p)
        old_est,old_ci=before.split('(',1)
        new_est,new_ci=ci(rr,d=2 if j==5 else 1,scale=1 if j==5 else 100).split(' (',1)
        exact(p,'('+old_ci,'('+new_ci)
        # Replace only the leading estimate so the original line break remains in place.
        if old_est!=new_est:
            before=tx(p);replace_span(p,0,len(old_est),new_est)
            changes.append({'old':before,'new':tx(p)})

# Word counts are computed from the accepted text, including inserted paragraphs.
body=root.find(W+'body');children=list(body)
start=children.index(ps[25]);end=children.index(ps[83])
maintext=' '.join(tx(el) for el in children[start:end] if el.tag==W+'p')
abstract=' '.join(tx(ps[i]) for i in range(18,22))
count=lambda s:len(re.findall(r'\S+',s))
setp(13,f'Word counts: abstract {count(abstract)}; main text {count(maintext)} (excluding abstract, acknowledgments, references, tables, and legends).')

settings=E.fromstring(parts['word/settings.xml'])
if settings.find(W+'trackRevisions') is None:E.SubElement(settings,W+'trackRevisions')
view=settings.find(W+'revisionView')
if view is None:view=E.SubElement(settings,W+'revisionView')
view.set(W+'markup','1');view.set(W+'insDel','1')
def resolve(r,accept):
    r=copy.deepcopy(r)
    # Remove newly inserted paragraphs entirely in the rejected view.
    if not accept:
        for p in list(r.xpath('//w:p[w:pPr/w:rPr/w:ins]',namespaces=NS)):p.getparent().remove(p)
    for el in list(r.xpath('//w:ins|//w:del',namespaces=NS)):
        parent=el.getparent()
        if parent is None:continue
        if (el.tag==W+'ins')==accept:
            idx=parent.index(el)
            for ch in list(el):
                for dt in ch.iter(W+'delText'):dt.tag=W+'t'
                parent.insert(idx,ch);idx+=1
        parent.remove(el)
    return r
accepted=resolve(root,True);rejected=resolve(root,False)
assert flat(rejected)==flat(original),'Rejecting changes must recover all original paragraph text'
assert root.xpath('//w:instrText/text()',namespaces=NS)==original.xpath('//w:instrText/text()',namespaces=NS),'Citation fields changed'
assert len(root.xpath('//w:fldChar',namespaces=NS))==len(original.xpath('//w:fldChar',namespaces=NS))
for name in ['commentRangeStart','commentRangeEnd','commentReference']:
    assert root.xpath(f'//w:{name}/@w:id',namespaces=NS)==original.xpath(f'//w:{name}/@w:id',namespaces=NS)
for el in root.xpath('//w:ins|//w:del',namespaces=NS):assert el.get(W+'author')=='Cinja'
newids=root.xpath('//w:ins/@w:id|//w:del/@w:id',namespaces=NS);assert len(set(newids))==len(newids)
assert not root.xpath('//w:del//w:t',namespaces=NS)
def write(path,doc,sett):
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for n,b in parts.items():
            if n=='word/document.xml':b=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
            if n=='word/settings.xml':b=E.tostring(sett,xml_declaration=True,encoding='UTF-8',standalone=True)
            z.writestr(n,b)
out=BASE/'NHIS2025_JAGS_Manuscript_Cinja_Tracked.docx';write(out,root,settings)
qa=Path('work/revision_2026-11-17');qa.mkdir(parents=True,exist_ok=True)
write(qa/'manuscript_accepted_QA.docx',accepted,settings)
(qa/'manuscript_accepted.txt').write_text('\n'.join(flat(accepted)))
(qa/'tracked_changes.json').write_text(json.dumps(changes,indent=2,ensure_ascii=False))
with ZipFile(out) as z:
    for n in parts:
        if n not in ['word/document.xml','word/settings.xml']:assert z.read(n)==parts[n],n
report={'author':'Cinja','changed_paragraphs':len(changes),'revision_elements':len(newids),'rejected_text_matches_original':True,'citation_fields_unchanged':True,'comments_and_other_package_parts_unchanged':True,'abstract_words':count(abstract),'main_words':count(maintext)}
(BASE/'manuscript_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
