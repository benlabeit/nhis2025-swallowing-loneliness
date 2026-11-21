"""Build publication artwork, supplementary PDF, and workbook input tables.

Run from the repository root after analysis/RunAnalysis.R.
All numerical results are read from the R-generated tables in results/.
No individual participant data are copied to a deliverable.
"""
from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

BASE = Path("results")
TABLES = BASE / "tables"
EXT = BASE / "extended_tables"
OUT = Path("supplement")
FIG = Path("figures")
WORK = Path("work/analysis")
for folder in (OUT, FIG, WORK):
    folder.mkdir(parents=True, exist_ok=True)

NAVY = "#23384A"
TEAL = "#147D83"
GRAY = "#65717C"
LIGHT = "#E9F3F3"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.titlesize": 15, "axes.titleweight": "semibold",
    "axes.labelsize": 11, "axes.edgecolor": "#80909D",
    "xtick.color": NAVY, "ytick.color": NAVY,
    "text.color": NAVY, "axes.labelcolor": NAVY,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.facecolor": "white", "figure.facecolor": "white",
})


def read(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def pick(rows, **criteria):
    matches = [row for row in rows if all(row.get(k) == v for k, v in criteria.items())]
    if len(matches) != 1:
        raise ValueError(f"Expected one row for {criteria}, got {len(matches)}")
    return matches[0]


def num(row, key="estimate"):
    return float(row[key])


def ci(row, key="estimate", scale=1, digits=2):
    return f"{num(row,key)*scale:.{digits}f} ({num(row,'lower')*scale:.{digits}f}-{num(row,'upper')*scale:.{digits}f})"


def integer(value):
    return f"{int(float(value)):,}"


models = read(TABLES / "model_results.tsv")
prevalences = read(TABLES / "weighted_prevalence.tsv")
margins = read(EXT / "standardized_prevalence_and_contrasts.tsv")
flow = read(TABLES / "participant_flow.tsv")
diagnostics = read(TABLES / "model_diagnostics.tsv")
flow_map = {r["stage"]: int(r["n"]) for r in flow}
common_n = flow_map["common_M0_to_M4"]
common_events = int(pick(models, model="M3", term="swallow")["events"])


def export(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=600, bbox_inches="tight", pad_inches=.15)
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight", pad_inches=.15)
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight", pad_inches=.15)
    return fig


def style_axis(ax, xlabel, reference=None):
    for key in ("top", "right", "left"):
        ax.spines[key].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=12)
    ax.tick_params(axis="x", length=3)
    ax.xaxis.grid(True, color="#E3E8EC", linewidth=.7, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel, labelpad=10)
    if reference is not None:
        ax.axvline(reference, color="#81919C", linestyle="--", linewidth=1, zorder=1)


def forest(rows, labels, title, footnote, primary=None, size=(8.6, 4.8)):
    fig, ax = plt.subplots(figsize=size)
    fig.subplots_adjust(left=.43, right=.79, top=.80, bottom=.33)
    n = len(rows)
    ys = np.arange(n)[::-1]
    vals = np.array([num(r) for r in rows])
    los = np.array([num(r,"lower") for r in rows])
    his = np.array([num(r,"upper") for r in rows])
    low = min(.8, min(los)*.88)
    high = max(2, max(his)*1.08)
    ax.set_xscale("log")
    ax.set_xlim(low, high)
    ax.set_ylim(-.65, n-.35)
    for i, (r,y) in enumerate(zip(rows,ys)):
        special = i == primary
        if special:
            ax.axhspan(y-.4,y+.4,color=LIGHT,zorder=0)
        color = TEAL if special else NAVY
        ax.errorbar(num(r),y,xerr=[[num(r)-num(r,"lower")],[num(r,"upper")-num(r)]],
                    fmt="D" if special else "o", markersize=7.3 if special else 6,
                    color=color, ecolor=color, elinewidth=1.8, capsize=3.2, zorder=3)
        ax.text(1.055, y, ci(r), transform=ax.get_yaxis_transform(), va="center",
                ha="left", fontsize=10.8, color=color, fontweight="semibold" if special else "normal")
    ax.set_yticks(ys, labels)
    ticks = [v for v in [.5,.75,1,1.5,2,3,4,5,6] if low <= v <= high]
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda value,pos:f"{value:g}"))
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    style_axis(ax,"Prevalence ratio (log scale)",reference=1)
    fig.text(.04,.94,title,ha="left",va="top",fontsize=15,fontweight="semibold")
    ax.text(1.055,1.08,"PR (95% CI)",transform=ax.transAxes,fontsize=10.5,fontweight="semibold",ha="left")
    fig.text(.04,.025,footnote,ha="left",va="bottom",fontsize=9.1,color=GRAY,linespacing=1.5)
    return fig


# Figure 1: descriptive estimates retain the available-response population.
raw = [pick(prevalences,group="no_swallowing_problem",variable="lonely"),
       pick(prevalences,group="swallowing_problem",variable="lonely")]
fig1, ax = plt.subplots(figsize=(8.6,4.0))
fig1.subplots_adjust(left=.30,right=.79,top=.77,bottom=.38)
ys=[1,0]
for r,y,col in zip(raw,ys,[NAVY,TEAL]):
    p=num(r,"prevalence")*100;lo=num(r,"lower")*100;hi=num(r,"upper")*100
    ax.errorbar(p,y,xerr=[[p-lo],[hi-p]],fmt="o",color=col,ecolor=col,
                markersize=8,elinewidth=2,capsize=4,zorder=3)
    ax.text(1.05,y,f"{p:.1f}% ({lo:.1f}-{hi:.1f})",transform=ax.get_yaxis_transform(),
            va="center",ha="left",fontsize=11,color=col)
ax.set_yticks(ys,["No swallowing problems","Swallowing problems"])
ax.set_xlim(0,max(15,max(num(r,"upper")*100 for r in raw)+1))
ax.set_ylim(-.55,1.6)
ax.xaxis.set_major_locator(mticker.MultipleLocator(5))
style_axis(ax,"Survey-weighted prevalence of frequent loneliness (%)")
fig1.text(.04,.93,"Frequent loneliness by swallowing problems",ha="left",va="top",fontsize=15,fontweight="semibold")
ax.text(1.05,1.18,"Prevalence (95% CI)",transform=ax.transAxes,fontsize=10.5,fontweight="semibold")
fig1.text(.04,.025,
          f"Adults aged 65 years or older answering for themselves; available exposure and outcome responses.\n"
          f"No swallowing problems: n={integer(raw[0]['n_valid'])}; swallowing problems: n={integer(raw[1]['n_valid'])}.\n"
          "Frequent loneliness means always or usually feeling lonely. Counts are unweighted.",
          fontsize=9.1,color=GRAY,linespacing=1.5)
export(fig1,"Figure1_Weighted_Prevalence")

main_rows = [pick(models,model=f"M{i}",term="swallow") for i in range(5)]
fig2=forest(main_rows,["M0  Unadjusted","M1  Sociodemographic and household",
                      "M2  Additional health factors","M3  Additional social connection",
                      "M4  Additional depressive feelings"],
            "Sequential adjustment for frequent loneliness",
            f"All models: n={common_n:,}; {common_events:,} frequent-loneliness events. M3 is the primary model.\n"
            "Survey-weighted Poisson regression; ten income imputations. Each model retains all earlier covariates.",
            primary=3)
export(fig2,"Figure2_Sequential_Models")

severity_rows=[pick(models,model="M3_severity",term=f"severity{x}") for x in ["little","middle","a_lot"]]
fig3=forest(severity_rows,["A little difficulty","Somewhere in between","A lot of difficulty"],
            "Swallowing difficulty and frequent loneliness",
            f"Reference: no swallowing problem. M3 adjustment; n={int(severity_rows[0]['n']):,}.\n"
            "Survey-weighted Poisson regression; ten income imputations. Self-reported severity categories.",
            size=(8.6,4.2))
export(fig3,"Figure3_Severity")

with PdfPages(FIG/"Main_Figures.pdf") as pdf:
    for fig in [fig1,fig2,fig3]:pdf.savefig(fig,bbox_inches="tight",pad_inches=.15)

# Supplementary figures are based on the current primary model.
ipw_path=EXT/"response_weighted_M3_PR.tsv"
ipw=read(ipw_path) if ipw_path.exists() else []
sensitivity_keys=[("M3","Primary M3"),("M4","M4: depressive feelings"),
                  ("M3_broad","Broader loneliness definition"),("M3_including_proxy","Including proxy interviews"),
                  ("M3_available","M3: available sample"),
                  ("M3_communication","Additional communication adjustment")]
sensrows=[pick(models,model=key,term="swallow") for key,label in sensitivity_keys]
senslabels=[label for key,label in sensitivity_keys]
for r in ipw:
    rr=dict(r)
    if "estimate" not in rr and "PR" in rr:rr["estimate"]=rr["PR"]
    sensrows.append(rr)
    senslabels.append("Response weighting" if "joint" in r.get("model","").lower() else "Response weighting, truncated")
figS1=forest(sensrows,senslabels,"Primary and sensitivity analyses",
             "PR denotes prevalence ratio. Each analysis uses its specified sample; all use ten income imputations.\n"
             "Broader loneliness includes sometimes. Communication comparisons use a matched complete sample.",
             primary=0,size=(8.9,6.0))
export(figS1,"FigureS1_Sensitivity")

figS2,ax=plt.subplots(figsize=(8.0,4.8))
figS2.subplots_adjust(left=.12,right=.96,top=.80,bottom=.34)
for i, (key,label,col) in enumerate([("M3","M3: primary",NAVY),("M4","M4: depressive feelings",TEAL)]):
    for a,m in enumerate(["prevalence_no_problem","prevalence_problem"]):
        r=pick(margins,model=key,measure=m); x=a+(-.08 if i==0 else .08)
        p,lo,hi=[num(r,k)*100 for k in ["estimate","lower","upper"]]
        ax.errorbar(x,p,yerr=[[p-lo],[hi-p]],fmt="o" if i==0 else "D",color=col,
                    capsize=4,elinewidth=1.8,markersize=7,label=label if a==0 else None)
        ax.annotate(f"{p:.1f}%",(x,p),xytext=(-3 if i==0 else 3,11 if i==0 else -20),
                    textcoords="offset points",ha="right" if i==0 else "left",fontsize=10,color=col)
ax.set_xlim(-.45,1.45);ax.set_ylim(bottom=0)
ax.set_xticks([0,1],["No swallowing problems","Swallowing problems"])
ax.set_ylabel("Standardized prevalence (%)",labelpad=10)
ax.yaxis.grid(True,color="#E3E8EC",linewidth=.7);ax.set_axisbelow(True)
for spine in ["top","right"]:ax.spines[spine].set_visible(False)
ax.legend(loc="upper left",frameon=False,fontsize=10)
figS2.text(.04,.94,"Model-standardized frequent loneliness",ha="left",va="top",fontsize=15,fontweight="semibold")
figS2.text(.04,.025,f"Survey-weighted logistic standardization to the same {common_n:,} respondents; ten income imputations.\n"
                   "Points and lines show estimated prevalences and 95% confidence intervals. These are adjusted associations.",
           fontsize=9.1,color=GRAY,linespacing=1.5)
export(figS2,"FigureS2_Standardized_Prevalence")

distribution=read(EXT/"loneliness_five_categories.tsv")
cats=["Never","Rarely","Sometimes","Usually","Always"]
palette=["#D6E3EC","#A8BFCE","#7AA3B4","#3D8297","#15566C"]
figS3,ax=plt.subplots(figsize=(8.4,4.0))
figS3.subplots_adjust(left=.29,right=.96,top=.75,bottom=.36)
for a,y in [(0,1),(1,0)]:
    left=0
    for ca,col in zip(cats,palette):
        r=pick(distribution,label=f"swallow_{a}",category=ca)
        p=num(r,"prevalence")*100
        ax.barh(y,p,left=left,color=col,height=.46,label=ca if a==0 else None)
        if p>=4:ax.text(left+p/2,y,f"{p:.1f}",ha="center",va="center",fontsize=10,color=NAVY if ca in cats[:2] else "white")
        left+=p
    if abs(left-100)>1e-6:raise AssertionError(f"Loneliness distribution does not sum to 100: {left}")
ax.set_yticks([1,0],["No swallowing problems","Swallowing problems"])
ax.set_xlim(0,100);ax.set_ylim(-.55,1.6);style_axis(ax,"Survey-weighted percentage")
figS3.legend(loc="lower center",bbox_to_anchor=(.60,.035),frameon=False,ncol=5,fontsize=9)
figS3.text(.04,.93,"Distribution of loneliness responses",ha="left",va="top",fontsize=15,fontweight="semibold")
export(figS3,"FigureS3_Loneliness_Distribution")

with PdfPages(FIG/"Supplementary_Figures.pdf") as pdf:
    for fig in [figS1,figS2,figS3]:pdf.savefig(fig,bbox_inches="tight",pad_inches=.15)

for fig in [fig1,fig2,fig3,figS1,figS2,figS3]:plt.close(fig)

# Supplementary PDF: full results and technical details.
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name="BodySmall",fontName="Helvetica",fontSize=9.4,leading=13.1,spaceAfter=7))
styles.add(ParagraphStyle(name="TableCell",fontName="Helvetica",fontSize=8.6,leading=11.2))
styles.add(ParagraphStyle(name="TableHeader",fontName="Helvetica-Bold",fontSize=8.6,leading=11.2,textColor=colors.white))
styles["Title"].fontName="Helvetica-Bold";styles["Title"].fontSize=18;styles["Title"].leading=22
styles["Heading2"].fontName="Helvetica-Bold";styles["Heading2"].fontSize=12;styles["Heading2"].spaceBefore=9;styles["Heading2"].spaceAfter=8
story=[]


def p(text,style="BodySmall"):
    story.append(Paragraph(escape(text),styles[style]))


def table(rows,widths):
    data=[[Paragraph(escape(str(value)),styles["TableHeader" if i==0 else "TableCell"]) for value in row] for i,row in enumerate(rows)]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor(NAVY)),
                           ("VALIGN",(0,0),(-1,-1),"TOP"),
                           ("LINEBELOW",(0,0),(-1,0),.7,colors.HexColor(NAVY)),
                           ("LINEBELOW",(0,1),(-1,-1),.35,colors.HexColor("#D9E2E7")),
                           ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F4F7F9")]),
                           ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story.append(t);story.append(Spacer(1,9))


def page_header(canvas,doc):
    canvas.saveState();canvas.setFont("Helvetica",8);canvas.setFillColor(colors.HexColor(GRAY))
    canvas.drawString(44,25,"Swallowing problems and loneliness | NHIS2025")
    canvas.drawRightString(A4[0]-44,25,f"S{doc.page}");canvas.restoreState()


p("Supplementary Material S1","Title")
p("Self-Reported Swallowing Problems Are Associated With Frequent Loneliness in Older US Adults")
p("Counts are unweighted. Estimates account for the 2025 NHIS survey design and all ten official income imputations unless otherwise stated.")
p("Table S1. Sequential models on a common sample","Heading2")
adjustments=["No covariates","Age, sex, education, income-to-poverty ratio, partnership, living alone",
             "M1 plus mobility, hearing and vision difficulties; stroke; dementia; memory/concentration difficulties; myocardial infarction; COPD/current asthma; arthritis; diabetes; cancer excluding nonmelanoma skin cancer",
             "M2 plus in-person contact, telephone/video contact, religious-service attendance and group participation (primary model)",
             "M3 plus daily or weekly depressive feelings"]
rows=[["Model","Adjustment","PR (95% CI)"]]
for i,r in enumerate(main_rows):rows.append([f"M{i}",adjustments[i],ci(r)])
table(rows,[42,337,128])
p(f"All five models contain {common_n:,} self-respondents and {common_events:,} frequent-loneliness events. The sample requires complete exposure, outcome and M4 non-income covariates. Comparison exposures and communication difficulties do not determine the common sample.")
imputation=read(TABLES/"income_imputation_counts.tsv")
ir=pick(imputation,population="common")
p("Text S1. Sample and income imputation","Heading2")
p(f"There were {flow_map['self_report_age_eligible']:,} age-eligible self-respondents after excluding {flow_map['proxy_age_eligible']:,} proxy interviews. Exposure and outcome were jointly available for {flow_map['self_report_valid_exposure_and_outcome']:,}. The regression sample contains {common_n:,} respondents. Income was imputed for {integer(ir['income_imputed_n'])} ({100*int(ir['income_imputed_n'])/common_n:.1f}%) of the common sample; this includes fully imputed income and income imputed within reported brackets. Income category counts can vary across the ten imputations.")
story.append(PageBreak())
p("Table S2. Sensitivity analyses","Heading2")
rows=[["Analysis","N","PR (95% CI)"]]
for key,label in [("M3","Primary M3"),("M4","M4: depressive feelings"),("M3_broad","Broader loneliness definition"),
                  ("M3_including_proxy","Including proxy interviews"),("M3_available","M3 without requiring complete depressive feelings"),
                  ("M3_communication_matched","M3 on communication-complete sample"),("M3_communication","M3 plus communication difficulty"),
                  ("M4_communication_matched","M4 on communication-complete sample"),("M4_communication","M4 plus communication difficulty")]:
    r=pick(models,model=key,term="swallow");rows.append([label,integer(r["n"]),ci(r)])
for r in ipw:
    label="Response weighting: joint variance estimation" if "joint" in r.get("model","").lower() else "Response weighting: truncated multipliers"
    rows.append([label,integer(r.get("n",common_n)),ci(r,"estimate" if "estimate" in r else "PR")])
table(rows,[296,65,146])
p("The broader outcome includes always, usually or sometimes feeling lonely, compared with rarely or never. Communication difficulty is modeled as none, some, or a lot/unable. Matched analyses ensure that changes after adding communication do not reflect a different sample. The available-M3 analysis relaxes only the requirement for a depressive-feelings response. Proxy interviews remain excluded except in the explicitly labeled sensitivity analysis.")
story.append(PageBreak())
p("Table S3. Comparison exposures","Heading2")
rows=[["Exposure","N","M3 PR (95% CI)","M4 PR (95% CI)"]]
for ex,label in [("comparison_matched","Swallowing problems"),("voice","Voice problems"),("speech","Speech problems"),("vision_exposure","Vision difficulties")]:
    t="swallow" if ex=="comparison_matched" else ex
    a=pick(models,model="M3_"+ex,term=t);b=pick(models,model="M4_"+ex,term=t)
    rows.append([label,integer(a["n"]),ci(a),ci(b)])
table(rows,[170,47,145,145])
p("These models use a common sample with valid swallowing, voice, speech and vision measures. Each exposure replaces swallowing problems while the remaining model covariates are retained. Vision difficulty is omitted as a covariate when it is the exposure. Voice and speech refer to problems during the previous 12 months; vision exposure is any reported difficulty. No formal contrast between exposure coefficients was performed. Different measurement properties and overlapping health conditions limit comparison; these analyses do not establish a swallowing-specific causal effect.")
p("Table S4. Swallowing-difficulty categories","Heading2")
counts=read(TABLES/"severity_outcome_common.tsv")
rows=[["Difficulty","N","Events","M3 PR (95% CI)","M4 PR (95% CI)"]]
for lev,term,label in [("none",None,"No swallowing problem"),("little","severitylittle","A little"),("middle","severitymiddle","Somewhere in between"),("a_lot","severitya_lot","A lot")]:
    cr=[r for r in counts if r["severity"]==lev]
    nn=sum(int(r["Freq"]) for r in cr);ev=sum(int(r["Freq"]) for r in cr if r["lonely"]=="1")
    if term is None:a=b="Reference"
    else:a=ci(pick(models,model="M3_severity",term=term));b=ci(pick(models,model="M4_severity",term=term))
    rows.append([label,f"{nn:,}",f"{ev:,}",a,b])
table(rows,[140,45,48,137,137])
p("Severity is an ordered questionnaire response rather than an equally spaced continuous score. The original codes 1, 3 and 2 correspond to a little difficulty, somewhere in between and a lot of difficulty. Structural skips for respondents without swallowing problems define the reference group. No formal linear-trend test is reported.")
story.append(PageBreak())
p("Table S5. Standardized absolute and relative estimates","Heading2")
rows=[["Model","N","No problems, % (95% CI)","Problems, % (95% CI)","Difference, percentage points (95% CI)","Marginal PR (95% CI)"]]
for key,label in [("M3","M3: primary"),("M4","M4: depressive feelings"),("M3_broad","M3: broader loneliness")]:
    rr=[r for r in margins if r["model"]==key]
    def m(measure):return pick(rr,measure=measure)
    rows.append([label,integer(rr[0]["n"]),ci(m("prevalence_no_problem"),scale=100,digits=1),ci(m("prevalence_problem"),scale=100,digits=1),ci(m("prevalence_difference"),scale=100,digits=1),ci(m("marginal_PR"))])
table(rows,[82,40,95,95,103,92])
p("Survey-weighted logistic predictions are standardized to each analysis sample. For each respondent, predicted loneliness probability is calculated once under each exposure setting while retaining the same covariates; weighted averages give the two prevalences. Design-based uncertainty is estimated by the survey package, and transformed estimates are combined across the ten income imputations. Contrasts are pooled separately, so displayed pooled prevalences need not reproduce the pooled difference or ratio exactly. Marginal logistic PRs differ from the log-link regression PRs in Tables S1-S4.")
p("Text S2. Additional statistical details","Heading2")
p("The full Sample Adult dataset defines the survey design using the final adult weight (WTFA_A), public-use stratum (PSTRAT) and primary sampling unit (PPSU), nested within stratum. Analytic populations are then treated as survey domains. Regression uses a Poisson log link with design-based variance estimation. Models are fitted separately in each of the ten official income datasets and combined with Rubin's rules; t-based intervals use finite complete-data design degrees of freedom. Income imputation does not impute missing exposure, outcome or other covariates.")
p("Age is grouped as 65-74, 75-84 or 85+ years. Educational attainment has four groups: below high school, high school/GED, some college/associate degree, and bachelor's degree or higher. Income-to-poverty ratio groups are below 1, 1 to below 2, 2 to below 4, and 4+. Partnership is married/cohabiting versus other; living alone requires one adult and no children. Mobility, hearing, vision, memory/concentration and supplementary communication difficulty each use none, some, or a lot/unable. In-person and telephone/video contacts use less than once, 1-2, 3-4 or 5+ times per week; religious services and group meetings use none, 1-3, 4-11 or 12+ occasions in the preceding year.")
p("Each chronic condition is entered as a separate binary indicator. Chronic lung disease means COPD or current asthma. Cancer includes reported malignancies other than nonmelanoma skin cancer; nonmelanoma skin cancer alone is coded absent. When skin cancer type is unknown and no other qualifying malignancy is established, cancer status remains missing. Sex-specific structural skips are handled according to the item universe. Other refused or unknown responses remain missing. Arthritis refers to the broad NHIS item and does not isolate inflammatory rheumatic disease.")
diag=pick(diagnostics,model="M4")
p(f"Model diagnostics assessed convergence, coefficient estimability, design-based covariance matrices, fitted values and sparse categories. M4 has {int(diag['nonintercept_parameters'])} non-intercept parameters and {common_events/int(diag['nonintercept_parameters']):.2f} outcome events per parameter. This descriptive ratio is not a guarantee of stability. Poisson fitted means can exceed 1; all absolute probability estimates therefore come from logistic standardization. Complete diagnostic tables are provided in Supplementary Material S2.")
if ipw:
    p("For selection sensitivity analyses, a survey-logistic model predicts inclusion in the common analysis sample among age-eligible self-respondents with known numeric age. Predictors are age group, region, adult household count and the presence of children. Stabilized inverse-probability multipliers modify the original survey weights. Joint estimating-equation linearization accounts for propensity estimation in the untruncated analysis. A secondary analysis truncates multipliers at the 1st and 99th percentiles and treats the resulting weights as fixed. These analyses cannot remove selection bias from unmeasured or non-ignorable missingness.")
ordinal_path=EXT/"proportional_odds_diagnostics.tsv"
if ordinal_path.exists():
    ordinal=read(ordinal_path); rejected=sum(r["reject"] in ["TRUE","True","1"] for r in ordinal)
    p(f"Four separate cumulative survey-logistic models describe loneliness thresholds: at least rarely, at least sometimes, at least usually, and always. Their joint design covariance is used to compare each non-intercept slope at the other three thresholds with its value at the primary threshold. Bonferroni adjustment is applied to this diagnostic family of {len(ordinal)} contrasts; {rejected} rejected equality. A common proportional-odds summary is not used when this diagnostic rejects equality. Rejection for another covariate does not itself establish a threshold difference for the swallowing coefficient.")
    thresholds=read(EXT/"threshold_specific_swallowing_OR.tsv")
    table([["Loneliness threshold","OR (95% CI)"]]+[[r["measure"].replace("_"," "),ci(r)] for r in thresholds],[310,197])
p("Descriptive prevalence intervals use a design-based logit method. Supplementary precision checks use effective sample sizes, design degrees of freedom and Korn-Graubard intervals according to NCHS presentation standards. Confidence intervals outside the stated ordinal diagnostic family are not globally adjusted for multiplicity. All analyses estimate cross-sectional associations; covariate adjustment and changes in model coefficients do not establish mediation or causality.")
p("Source: National Center for Health Statistics. 2025 NHIS public-use Sample Adult data and multiply imputed income files. Variable-level recoding, full coefficients, diagnostics and provenance are supplied in the accompanying workbook and reproducibility files.")
story.append(PageBreak())
p("Figure S1. Primary and sensitivity analyses","Heading2")
story.append(Image(str(FIG/"FigureS1_Sensitivity.png"),width=507,height=507*6/8.9))
p("Points and lines indicate PRs and 95% confidence intervals. M3 is highlighted. The broader outcome includes sometimes feeling lonely. Sample-specific denominators and matched comparisons are given in Table S2.")
story.append(PageBreak())
p("Figure S2. Standardized prevalence by model","Heading2")
story.append(Image(str(FIG/"FigureS2_Standardized_Prevalence.png"),width=507,height=507*4.8/8))
p("M3 and M4 use the same common sample; M4 adds daily or weekly depressive feelings. Predictions come from survey-weighted logistic standardization and are pooled across ten income imputations.")
story.append(PageBreak())
p("Figure S3. All loneliness response categories","Heading2")
story.append(Image(str(FIG/"FigureS3_Loneliness_Distribution.png"),width=507,height=507*4/8.4))
p("The full five-category loneliness distribution uses available responses among self-responding adults aged 65 years or older, grouped by reported swallowing problems. Percentages are survey-weighted and rounded.")
supp=OUT/"Supplement_S1.pdf"
SimpleDocTemplate(str(supp),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=40,bottomMargin=43,
                  title="NHIS2025 Swallowing and Loneliness - Supplement S1",author="Bendix Labeit et al.").build(story,onFirstPage=page_header,onLaterPages=page_header)

# Typed R outputs for the formatted spreadsheet report.
def typed(rows):
    if not rows:return []
    keys=list(rows[0]);numeric=set()
    for key in keys:
        values=[r.get(key,"") for r in rows if r.get(key,"") not in ["NA",""]]
        try:
            if values and all(math.isfinite(float(v)) for v in values):numeric.add(key)
        except (ValueError,TypeError):pass
    return [keys]+[[None if r.get(key,"") in ["NA",""] else float(r[key]) if key in numeric else r[key] for key in keys] for r in rows]


sheets=[]
preferred=[("Models",TABLES/"model_results.tsv"),("Absolute estimates",EXT/"standardized_prevalence_and_contrasts.tsv"),
           ("Participant flow",TABLES/"participant_flow.tsv"),("Characteristics",EXT/"table1_characteristics.tsv"),
           ("Income",EXT/"table1_income_ten_imputations.tsv"),("Model specification",TABLES/"model_specification.tsv")]
done=set()
for name,path in preferred:
    if path.exists():sheets.append({"name":name,"source":str(path),"values":typed(read(path))});done.add(path)
coeff=[]
for path in sorted(TABLES.glob("coefficients_*.tsv")):
    coeff.extend(read(path));done.add(path)
if coeff:sheets.append({"name":"All coefficients","source":"results/tables/coefficients_*.tsv","values":typed(coeff)})
for path in sorted(list(TABLES.glob("*.tsv"))+list(EXT.glob("*.tsv"))):
    if path in done or path.stem in {"joint_score_validation", "threshold_covariance_validation"}:continue
    name=path.stem.replace("_"," ")[:31]
    i=2
    while name in [x["name"] for x in sheets]:name=(path.stem.replace("_"," ")[:28]+f" {i}")[:31];i+=1
    rows=read(path)
    if rows:sheets.append({"name":name,"source":str(path),"values":typed(rows)})
definitions=[["Variable or analysis","Definition"],
             ["Population","Self-respondents aged 65 years or older. AGE65 fallback establishes descriptive eligibility but does not supply a regression age group."],
             ["Swallowing exposure","VSLSWYR_A=1 yes versus 2 no; previous 12 months. Unknown/refused responses are missing."],
             ["Frequent loneliness","LONELY_A=1-2 (always/usually) versus 3-5 (sometimes/rarely/never)."],
             ["Broader loneliness","LONELY_A=1-3 versus 4-5."],
             ["M0","Unadjusted swallowing exposure."],
             ["M1",adjustments[1]],["M2",adjustments[2]],["M3",adjustments[3]],["M4",adjustments[4]],
             ["Common sample","Complete exposure, outcome and M4 non-income predictors. Comparison exposures, severity and communication do not restrict the primary sample."],
             ["Income","Ten official imputations; fitted coefficients and design variances pooled with Rubin's rules and finite design degrees of freedom."],
             ["Difficulty variables","None; some; a lot/unable, corresponding to raw codes 1, 2, and 3-4."],
             ["Cognitive variables","Diagnosed dementia(DEMENEV_A) and remembering/concentrating difficulty(COGMEMDFF_A)."],
             ["Communication sensitivity","COMDIFF_A added only in matched-sample sensitivity analyses."],
             ["Chronic conditions","Myocardial infarction, COPD/current asthma, arthritis, diabetes and cancer are separate binary covariates."],
             ["Cancer","Cancer other than nonmelanoma skin cancer. Unknown skin type without another qualifying malignancy remains missing."],
             ["Missingness","Unknown/refused responses remain missing; structural skips follow each questionnaire item's universe."],
             ["Standardization","Survey-logistic weighted predictive margins; prevalences and contrasts pooled separately. These are associations, not intervention effects."],
             ["Comparison exposures","Voice/speech symptoms and any vision difficulty replace swallowing exposure on a matched sample. No formal between-exposure contrast or causal specificity claim."],
             ["Statistical software","R survey and mitools; exact versions are in results/R_session_info.txt."],
             ["Source","https://www.cdc.gov/nchs/nhis/documentation/2025-nhis.html"],
             ["Reproduction","Run analysis/RunAnalysis.R from the repository root. Publication figures and Supplement S1 are produced by analysis/BuildFigures.py; this workbook reports the R-generated numerical tables."],
             ["Values","All estimates are static computed R results, not Excel regression calculations. Retained precision exceeds manuscript rounding."]]
sheets.append({"name":"Definitions and sources","source":"2025 NHIS codebook and R scripts","values":definitions})
(WORK/"workbook_inputs.json").write_text(json.dumps(sheets,ensure_ascii=False,indent=2),encoding="utf-8")
manifest={"common_n":common_n,"common_events":common_events,"figures":[str(x) for x in FIG.glob("*.pdf")],
          "supplement_pdf":str(supp),"supplement_pages":len(PdfReader(supp).pages),"workbook_sheets":len(sheets)}
(WORK/"artwork_manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
