"""Create the English manuscript from reviewed content and a real Zotero export.

Run with the bundled Python from the project root after the authoring marker:
  python work/manuscript/build_manuscript.py

This builder deliberately refuses to substitute a fabricated Zotero item or a
hand-formatted citation if the required Zotero export is unavailable/inconsistent.
It does not run Word, refresh Zotero, or render the document. Root performs those
steps separately and must visually verify the rendered final artifact.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import html
import json
import re
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from lxml import etree

ROOT = Path.cwd()
CONTENT = ROOT / "outputs/manuscript_sources/content.json"
EXPORT = ROOT / "outputs/literature/zotero_citations.json"
OUTPUT = ROOT / "outputs/NHIS2025_Manuscript_EN.docx"
CHECKS = ROOT / "work/manuscript/docx_build_checks.json"
MARKERS = re.compile(r"\[\[([^\]]+)\]\]")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CUSTOM_NS = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def load_json(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"Required input is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_tsv(name: str, extended: bool = True):
    folder = "extended_tables" if extended else "tables"
    with (ROOT / "outputs" / folder / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def number(value, digits=2):
    return f"{float(value):.{digits}f}"


def interval(row, multiplier=1, digits=2):
    return f"{number(float(row['estimate'])*multiplier,digits)} ({number(float(row['lower'])*multiplier,digits)}-{number(float(row['upper'])*multiplier,digits)})"


def explicit_font_properties(rpr, size=None):
    """Remove theme precedence and make all writing systems explicitly Times."""
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attribute in list(fonts.attrib):
        if "theme" in etree.QName(attribute).localname.lower():
            del fonts.attrib[attribute]
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(f"w:{key}"), "Times New Roman")
    color = rpr.find(qn("w:color"))
    if color is None:
        color = OxmlElement("w:color")
        rpr.append(color)
    color.attrib.clear()
    color.set(qn("w:val"), "000000")
    if size is not None:
        for tag in ("sz", "szCs"):
            node = rpr.find(qn(f"w:{tag}"))
            if node is None:
                node = OxmlElement(f"w:{tag}")
                rpr.append(node)
            node.set(qn("w:val"), str(round(size * 2)))


def set_font(run, size=11, bold=None):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        run.bold = bold
    explicit_font_properties(run._r.get_or_add_rPr(), size)


def enforce_plain_styles(doc):
    """Clean template decorations, linked styles and automatic redefinition."""
    styles = doc.styles.element
    defaults = styles.find(qn("w:docDefaults"))
    if defaults is None:
        defaults = OxmlElement("w:docDefaults")
        styles.insert(0, defaults)
    rdefault = defaults.find(qn("w:rPrDefault"))
    if rdefault is None:
        rdefault = OxmlElement("w:rPrDefault")
        defaults.insert(0, rdefault)
    rpr = rdefault.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        rdefault.append(rpr)
    explicit_font_properties(rpr, 11)
    for style in styles.findall(qn("w:style")):
        for node in list(style.findall(qn("w:autoRedefine"))):
            style.remove(node)
        sid = style.get(qn("w:styleId"), "")
        base = sid.removesuffix("Char")
        if base not in ("Normal", "DefaultParagraphFont", "Title", "Subtitle", "Caption") and not base.startswith("Heading"):
            continue
        rpr = style.find(qn("w:rPr"))
        if rpr is None:
            rpr = OxmlElement("w:rPr")
            style.append(rpr)
        size = 16 if base == "Title" else 12 if base == "Heading1" else 11
        explicit_font_properties(rpr, size)
        # The bundled template has a blue title border, theme fonts, and linked
        # character styles. Remove those inherited visual decorations explicitly.
        for tag in ("bdr", "u", "shadow", "outline", "emboss", "imprint", "spacing", "kern"):
            for node in list(rpr.findall(qn(f"w:{tag}"))):
                rpr.remove(node)
        underline = OxmlElement("w:u")
        underline.set(qn("w:val"), "none")
        rpr.append(underline)
        if base == "Title" or base.startswith("Heading"):
            for tag in ("b", "bCs"):
                node = rpr.find(qn(f"w:{tag}"))
                if node is None:
                    node = OxmlElement(f"w:{tag}")
                    rpr.append(node)
                node.set(qn("w:val"), "1")
        ppr = style.find(qn("w:pPr"))
        if ppr is not None:
            for tag in ("pBdr", "numPr"):
                for node in list(ppr.findall(qn(f"w:{tag}"))):
                    ppr.remove(node)
    settings = doc.settings.element
    for tag in ("attachedTemplate", "updateStyles"):
        for node in list(settings.findall(qn(f"w:{tag}"))):
            settings.remove(node)
    update_styles = OxmlElement("w:updateStyles")
    update_styles.set(qn("w:val"), "false")
    settings.append(update_styles)
    # A template relationship can also be carried by an imported Settings part.
    settings_part = doc.part.part_related_by("http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings")
    for rid, relationship in list(settings_part.rels.items()):
        if relationship.reltype.endswith("/attachedTemplate"):
            del settings_part.rels[rid]


def explicit_heading_runs(doc):
    """Give generated heading/title runs the same explicit style typography."""
    for paragraph in doc.paragraphs:
        sid = paragraph.style.style_id
        if sid not in ("Title", "Subtitle") and not sid.startswith("Heading"):
            continue
        size = 16 if sid == "Title" else 12 if sid == "Heading1" else 11
        for run in paragraph.runs:
            set_font(run, size, bold=(sid != "Subtitle"))


def field_control(paragraph, kind: str):
    run = paragraph.add_run()
    set_font(run)
    node = OxmlElement("w:fldChar")
    node.set(qn("w:fldCharType"), kind)
    if kind == "begin":
        node.set(qn("w:dirty"), "false")
    run._r.append(node)


def field_start(paragraph, instruction: str):
    field_control(paragraph, "begin")
    # Splitting instruction text into runs is supported by Word; no JSON bytes
    # are removed or escaped beyond the XML serializer's normal handling.
    for start in range(0, len(instruction), 2000):
        run = paragraph.add_run()
        set_font(run)
        node = OxmlElement("w:instrText")
        node.set(qn("xml:space"), "preserve")
        node.text = instruction[start:start + 2000]
        run._r.append(node)
    field_control(paragraph, "separate")


def plain_citeproc(value: str):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Empty or non-text citation/bibliography output from Zotero")
    # The export requests the text output mode. Reject unexpected rich output
    # instead of silently changing the citation engine's formatting.
    if re.search(r"<\/?(?:div|span|i|b)\b", value) or value.startswith("{\\rtf"):
        raise ValueError("Expected Zotero citeproc text output, received rich text")
    return html.unescape(value).strip()


class CitationWriter:
    def __init__(self, export):
        self.export = export
        self.clusters = export["citations"]
        self.index = 0
        self.rendered = {}
        for triple in export["rendered"]:
            if not isinstance(triple, list) or len(triple) != 3:
                raise ValueError("Unexpected Zotero rendered citation schema")
            citation_id, _note_index, text = triple
            self.rendered[str(citation_id)] = plain_citeproc(text)
        if len(self.rendered) != len(self.clusters):
            raise ValueError("Zotero rendered citation count differs from clusters")
        self.audit = []

    def append(self, paragraph, text: str):
        cursor = 0
        for marker in MARKERS.finditer(text):
            before = text[cursor:marker.start()]
            if before:
                set_font(paragraph.add_run(before))
            keys = [k.strip() for k in marker.group(1).split(",")]
            if self.index >= len(self.clusters):
                raise ValueError("Manuscript contains more citation markers than the Zotero export")
            cluster = self.clusters[self.index]
            if cluster.get("keys") != keys:
                raise ValueError(f"Citation sequence mismatch at marker {self.index + 1}: {keys}")
            citation_id = str(cluster["citationID"])
            rendered = self.rendered[citation_id]
            items = copy.deepcopy(cluster["citationItems"])
            if len(items) != len(keys):
                raise ValueError("Citation item count mismatch")
            for key, item in zip(keys, items):
                actual = self.export["items"][key]
                if item.get("id") != actual["id"] or actual["uri"] not in item.get("uris", []):
                    raise ValueError(f"Citation does not link to the real exported Zotero item: {key}")
                if not item.get("itemData") or not actual.get("key"):
                    raise ValueError(f"Missing CSL data or Zotero key for {key}")
            properties = copy.deepcopy(cluster.get("properties", {}))
            properties.update({"formattedCitation": rendered, "plainCitation": rendered, "noteIndex": 0})
            payload = {"citationID": citation_id, "properties": properties,
                       "citationItems": items,
                       "schema": "https://github.com/citation-style-language/schema/raw/master/csl-citation.json"}
            instruction = " ADDIN ZOTERO_ITEM CSL_CITATION " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + " "
            field_start(paragraph, instruction)
            set_font(paragraph.add_run(rendered))
            field_control(paragraph, "end")
            self.audit.append({"citationID": citation_id, "keys": keys, "cached_text": rendered})
            self.index += 1
            cursor = marker.end()
        if cursor < len(text):
            set_font(paragraph.add_run(text[cursor:]))

    def finish(self):
        if self.index != len(self.clusters):
            raise ValueError("Unused Zotero citation clusters: content and export differ")


def document_styles(doc):
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = section.bottom_margin = Inches(1)
    section.left_margin = section.right_margin = Inches(1)
    section.header_distance = section.footer_distance = Inches(0.5)
    for name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Caption"):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(11)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.widow_control = True
    normal = doc.styles["Normal"].paragraph_format
    normal.line_spacing = 1.15
    normal.space_after = Pt(6)
    normal.space_before = Pt(0)
    for name, size in (("Title", 16), ("Heading 1", 12), ("Heading 2", 11)):
        style = doc.styles[name]
        style.font.size = Pt(size)
        style.font.bold = True
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(10 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(5 if name != "Title" else 8)
    doc.styles["Subtitle"].paragraph_format.space_after = Pt(10)
    enforce_plain_styles(doc)
    # Page number is a standard Word field; citation fields remain live and unlocked.
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field_start(footer, " PAGE ")
    set_font(footer.add_run("1"), 10)
    field_control(footer, "end")
    settings = doc.settings.element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "false")
    doc.core_properties.title = "Self reported swallowing problems and frequent loneliness among older adults in the United States"
    doc.core_properties.subject = "NHIS 2025 cross sectional secondary analysis"
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    doc.core_properties.comments = ""


def write_section(doc, section, writer, level=1):
    doc.add_heading(section["heading"], level=level)
    for text in section.get("paragraphs", []):
        paragraph = doc.add_paragraph()
        writer.append(paragraph, text)
    for sub in section.get("subsections", []):
        write_section(doc, sub, writer, min(level + 1, 3))


def add_bibliography(doc, export):
    params, entries = export["bibliography"]
    if not entries:
        raise ValueError("Zotero bibliography is empty")
    doc.add_heading("References", level=1)
    first = None
    last = None
    for i, entry in enumerate(entries):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_after = Pt(5)
        paragraph.paragraph_format.left_indent = Inches(0.28)
        paragraph.paragraph_format.first_line_indent = Inches(-0.28)
        paragraph.paragraph_format.keep_together = True
        if i == 0:
            first = paragraph
            field_start(paragraph, ' ADDIN ZOTERO_BIBL {"uncited":[],"omitted":[],"custom":[]} CSL_BIBLIOGRAPHY ')
        text = plain_citeproc(entry)
        set_font(paragraph.add_run(text))
        last = paragraph
    field_control(last, "end")
    return len(entries)


def shade(cell, fill):
    props = cell._tc.get_or_add_tcPr()
    item = props.find(qn("w:shd"))
    if item is None:
        item = OxmlElement("w:shd")
        props.append(item)
    item.set(qn("w:fill"), fill)


def table(doc, headers, rows, widths, fontsize=10):
    tab = doc.add_table(rows=1, cols=len(headers))
    tab.alignment = WD_TABLE_ALIGNMENT.CENTER
    tab.autofit = False
    for col, width in zip(tab.columns, widths):
        col.width = Inches(width)
    for cell, width in zip(tab.rows[0].cells, widths):
        cell.width = Inches(width)
    for j, label in enumerate(headers):
        tab.rows[0].cells[j].text = label
    for record in rows:
        cells = tab.add_row().cells
        for j, value in enumerate(record):
            cells[j].width = Inches(widths[j])
            cells[j].text = str(value)
    props = tab._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "4")
        node.set(qn("w:color"), "D9D9D9")
        borders.append(node)
    props.append(borders)
    margins = OxmlElement("w:tblCellMar")
    for edge, val in (("top", 70), ("bottom", 70), ("left", 85), ("right", 85)):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        margins.append(node)
    props.append(margins)
    for i, row in enumerate(tab.rows):
        # Keep each row intact, but let a long table continue with a repeated header.
        trpr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trpr.append(cant)
        if i == 0:
            repeat = OxmlElement("w:tblHeader")
            trpr.append(repeat)
        for j, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if i == 0:
                shade(cell, "E7E6E6")
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.keep_with_next = False
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    set_font(run, fontsize, bold=(i == 0))
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return tab


def table_note(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.0
    for r in p.runs:
        set_font(r, 10)


def add_table1(doc):
    rows = read_tsv("table1_characteristics.tsv")
    income = read_tsv("table1_income_ten_imputations.tsv")
    selected = [
        ("Age 65-74 years", "agegrp", ["65-74"]),
        ("Age 75-84 years", "agegrp", ["75-84"]),
        ("Age 85 years or older", "agegrp", ["85+"]),
        ("Female sex", "sex", ["2"]),
        ("Education less than high school", "education", ["lt_HS"]),
        ("High school or GED", "education", ["HS"]),
        ("Some college or associate degree", "education", ["some_college"]),
        ("Bachelor's degree or higher", "education", ["BA_plus"]),
        ("Married or cohabiting", "partner", ["1"]),
        ("Living alone", "alone", ["1"]),
        ("Any mobility difficulty", "mobility", ["2", "3"]),
        ("Any hearing difficulty", "hearing", ["2", "3"]),
        ("History of stroke", "stroke", ["1"]),
        ("In-person contact less than weekly", "contact1", ["0"]),
        ("Phone or video contact less than weekly", "contact2", ["0"]),
        ("Daily or weekly depressive feelings", "depression", ["1"]),
        ("Proxy interview", "proxy", ["1"]),
    ]
    records = []
    for label, variable, categories in selected:
        cells = []
        for exposure in ("0", "1"):
            matches = [r for r in rows if r["population"] == "common" and r["swallow"] == exposure and r["variable"] == variable and r["category"] in categories]
            if len(matches) != len(categories):
                raise ValueError(f"Missing Table 1 row: {variable}, {categories}, {exposure}")
            if len({r["denominator_n"] for r in matches}) != 1:
                raise ValueError("Cannot combine categories with different valid denominators")
            percent = 100 * sum(float(r["prevalence"]) for r in matches)
            count = sum(int(r["numerator_n"]) for r in matches)
            cells.append(f"{percent:.1f} ({count:,})")
        records.append([label, *cells])
    income_labels = [("Below 100%", "Income below 100% of poverty threshold"),
                     ("100 to <200%", "Income 100% to less than 200%"),
                     ("200 to <400%", "Income 200% to less than 400%"),
                     ("400% or more", "Income at least 400%")]
    income_records = []
    for category, label in income_labels:
        cells = []
        for exposure in ("0", "1"):
            match = [r for r in income if r["population"] == "common" and r["swallow"] == exposure and r["category"] == category]
            if len(match) != 1:
                raise ValueError("Income Table 1 row is missing or duplicated")
            r = match[0]
            cells.append(f"{float(r['weighted_percent']):.1f} ({int(r['n_min']):,}-{int(r['n_max']):,})")
        income_records.append([label, *cells])
    records[8:8] = income_records
    doc.add_heading("Table 1 Selected characteristics of the common analytic sample", level=1)
    table(doc, ["Characteristic", "No swallowing problems\nN = 7,420\n% (n)", "Swallowing problems\nN = 674\n% (n)"], records, [3.5, 1.5, 1.5], fontsize=10)
    table_note(doc, "Percentages are survey-weighted; counts are unweighted. Income percentages are averaged across ten official imputations; parentheses show the minimum-maximum unweighted category counts across those imputations. All displayed covariates except depressive feelings are complete in this sample. Depressive feelings are missing for 34 participants without and 5 with swallowing problems; corresponding percentages use valid-response denominators of 7,386 and 669. Any mobility/hearing difficulty combines some difficulty with a lot of difficulty/unable. Full category-level estimates and available-case characteristics are provided in the supplementary tables.")
    return len(records)


def add_table2(doc):
    rows = read_tsv("model_results.tsv", extended=False)
    labels = [("M0", "M0 Unadjusted"), ("M1", "M1 Age and sex"),
              ("M2", "M2 Social and health characteristics"),
              ("M3_primary", "M3 Contact frequency added"),
              ("M4_participation", "M4 Participation added")]
    records = []
    for key, label in labels:
        r = next(r for r in rows if r["model"] == key and r["term"] == "swallow")
        assert int(r["n"]) == 8094 and int(r["events"]) == 429
        records.append([label, interval(r)])
    doc.add_heading("Table 2 Sequential models for frequent loneliness", level=1)
    table(doc, ["Model", "Prevalence ratio (95% CI)"], records, [4.0, 2.5], fontsize=10)
    table_note(doc, "All models compare swallowing problems with no problems and use N = 8,094 with 429 frequent-loneliness events. Models are survey-weighted and sequentially add the covariates described in Methods. M3 is the primary model; M4 is an extended sensitivity analysis. Income-adjusted models combine all ten official imputations. PR denotes prevalence ratio; CI denotes confidence interval.")


def add_table3(doc):
    rows = read_tsv("standardized_prevalence_and_contrasts.tsv")
    labels = [("M3", "Primary M3"), ("M3_depression_matched", "Matched sample before additional adjustment"),
              ("M3_depression", "Adjusted for depressive feelings"), ("M3_broad", "Broader loneliness outcome")]
    records = []
    for key, label in labels:
        sub = {r["measure"]: r for r in rows if r["model"] == key}
        records.append([label, f"{int(sub['marginal_PR']['n']):,}",
                        interval(sub["prevalence_no_problem"], 100),
                        interval(sub["prevalence_problem"], 100),
                        interval(sub["prevalence_difference"], 100), interval(sub["marginal_PR"])])
    doc.add_heading("Table 3 Standardized absolute and relative estimates", level=1)
    table(doc, ["Analysis", "N", "No problem\n% (95% CI)", "Problem\n% (95% CI)", "Difference\npercentage points\n(95% CI)", "Marginal PR\n(95% CI)"], records, [1.35, .55, 1.15, 1.15, 1.25, 1.05], fontsize=9.5)
    table_note(doc, "Survey-logistic predictions were standardized to each analytic sample's weighted covariate distribution. Frequent loneliness means always or usually lonely; the broader outcome also includes sometimes. The two depressive-feelings comparisons use the same N = 8,055. All estimates combine ten income imputations. Separate transformed pooling means the displayed contrast need not exactly equal an arithmetic operation on the separately rounded prevalences. These are model-standardized associations, not intervention effects.")


def add_figures(doc):
    figures = [
        ("Figure 1", "Figure1_Weighted_Prevalence.png",
         "Survey-weighted prevalence of frequent loneliness by self-reported swallowing problems. Frequent loneliness means always or usually feeling lonely; swallowing problems refer to the preceding 12 months. Points show weighted prevalence and lines show design-based logit 95% confidence intervals. Valid-response denominators are 7,545 without and 686 with swallowing problems (N = 8,231). Counts are unweighted. No covariate adjustment was performed."),
        ("Figure 2", "Figure2_Sequential_Models.png",
         "Prevalence ratios across sequential adjustment models. All models use the same 8,094 adults with 429 events. M1 adds age and sex; M2 adds education, income-to-poverty ratio, partnership, living alone, mobility, hearing and stroke; primary M3 adds in-person and phone/video contact; M4 adds religious and group participation. Points and lines represent PRs and 95% confidence intervals from survey-weighted Poisson models. The logarithmic axis marks PR = 1. These are cross-sectional associations."),
        ("Figure 3", "Figure3_Severity.png",
         "Secondary analysis of reported swallowing difficulty. M3-adjusted prevalence ratios compare a little difficulty, somewhere in between and a lot of difficulty with no swallowing problems. N = 8,093; the three exposed categories contain 361, 199 and 113 adults, with 33, 27 and 22 events. The reference category has no artificial interval. The categories are not equally spaced and no formal trend test was performed. Small event counts and self-reported severity limit interpretation."),
    ]
    for title, filename, caption in figures:
        doc.add_page_break()
        doc.add_heading(title, level=1)
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.keep_with_next = True
        picture = paragraph.add_run().add_picture(str(ROOT / "outputs/figures_en" / filename), width=Inches(6.5))
        picture._inline.docPr.set("descr", caption)
        p = doc.add_paragraph(caption)
        p.paragraph_format.space_after = Pt(6)


def add_zotero_properties(path: Path, export):
    # Zotero's official integration.js currently serializes XML data version 3.
    # Long Word custom-property strings are stored in sequential 255-char chunks.
    session_id = hashlib.sha256(json.dumps(export["citations"], sort_keys=True).encode()).hexdigest()[:8]
    data = etree.Element("data", attrib={"data-version": "3", "zotero-version": str(export["zoteroVersion"])})
    etree.SubElement(data, "session", id=session_id)
    etree.SubElement(data, "style", id=export["styleID"], locale="en-US", hasBibliography="1", bibliographyStyleHasBeenSet="1")
    prefs = etree.SubElement(data, "prefs")
    etree.SubElement(prefs, "pref", name="fieldType", value="Field")
    etree.SubElement(prefs, "pref", name="automaticJournalAbbreviations", value="true")
    etree.SubElement(prefs, "pref", name="delayCitationUpdates", value="false")
    serialized = etree.tostring(data, encoding="unicode")
    props = etree.Element(f"{{{CUSTOM_NS}}}Properties", nsmap={None: CUSTOM_NS, "vt": VT_NS})
    for i, start in enumerate(range(0, len(serialized), 255), start=1):
        prop = etree.SubElement(props, f"{{{CUSTOM_NS}}}property", fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}", pid=str(i + 1), name=f"ZOTERO_PREF_{i}")
        etree.SubElement(prop, f"{{{VT_NS}}}lpwstr").text = serialized[start:start + 255]
    with zipfile.ZipFile(path) as source:
        files = {info.filename: source.read(info.filename) for info in source.infolist()}
    # python-docx edits styles.xml but leaves the optional Word styles-with-
    # effects part untouched. Keep the same plain styles in both representations.
    if "word/stylesWithEffects.xml" in files:
        files["word/stylesWithEffects.xml"] = files["word/styles.xml"]
    rels = etree.fromstring(files["_rels/.rels"])
    rel_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
    if not any(r.get("Type") == rel_type for r in rels):
        etree.SubElement(rels, f"{{{REL_NS}}}Relationship", Id="rIdZoteroCustomProperties", Type=rel_type, Target="docProps/custom.xml")
    files["_rels/.rels"] = etree.tostring(rels, encoding="UTF-8", xml_declaration=True, standalone=True)
    types = etree.fromstring(files["[Content_Types].xml"])
    if not any(t.get("PartName") == "/docProps/custom.xml" for t in types):
        etree.SubElement(types, f"{{{CT_NS}}}Override", PartName="/docProps/custom.xml", ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml")
    files["[Content_Types].xml"] = etree.tostring(types, encoding="UTF-8", xml_declaration=True, standalone=True)
    files["docProps/custom.xml"] = etree.tostring(props, encoding="UTF-8", xml_declaration=True, standalone=True)
    temporary = path.with_name(path.stem + ".tmp.docx")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, contents in files.items():
            target.writestr(name, contents)
    temporary.replace(path)


def verify_docx(path: Path, expected_citations: int, expected_bib: int):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        xml = etree.fromstring(archive.read("word/document.xml"))
        instructions = "".join(xml.xpath("//w:instrText/text()", namespaces={"w": W_NS}))
        text = "".join(xml.xpath("//w:t/text()", namespaces={"w": W_NS}))
        assert instructions.count("ADDIN ZOTERO_ITEM CSL_CITATION") == expected_citations
        assert instructions.count("ADDIN ZOTERO_BIBL") == 1
        assert "[[PMID" not in text and "[[CDC" not in text
        props = etree.fromstring(archive.read("docProps/custom.xml"))
        chunks = sorted(props, key=lambda p: int(p.get("name").rsplit("_", 1)[1]))
        prefs = "".join(p[0].text or "" for p in chunks)
        parsed = etree.fromstring(prefs.encode())
        assert parsed.find("style").get("id")
        controls = xml.xpath("//w:fldChar/@w:fldCharType", namespaces={"w": W_NS})
        assert controls.count("begin") == controls.count("end") == expected_citations + 1
        assert controls.count("separate") == expected_citations + 1
        styles = etree.fromstring(archive.read("word/styles.xml"))
        assert not styles.findall(".//" + qn("w:autoRedefine"))
        for style in styles.findall(qn("w:style")):
            sid = style.get(qn("w:styleId"), "").removesuffix("Char")
            if sid not in ("Normal", "DefaultParagraphFont", "Title", "Subtitle", "Caption") and not sid.startswith("Heading"):
                continue
            fonts = style.find(qn("w:rPr") + "/" + qn("w:rFonts"))
            assert fonts is not None
            assert all(fonts.get(qn(f"w:{key}")) == "Times New Roman" for key in ("ascii", "hAnsi", "eastAsia", "cs"))
            assert not any("theme" in etree.QName(key).localname.lower() for key in fonts.attrib)
            color = style.find(qn("w:rPr") + "/" + qn("w:color"))
            assert dict(color.attrib) == {qn("w:val"): "000000"}
            assert style.find(qn("w:pPr") + "/" + qn("w:pBdr")) is None
        if "word/stylesWithEffects.xml" in archive.namelist():
            assert archive.read("word/stylesWithEffects.xml") == archive.read("word/styles.xml")
        settings = etree.fromstring(archive.read("word/settings.xml"))
        assert settings.find(qn("w:attachedTemplate")) is None
        assert settings.find(qn("w:updateStyles")).get(qn("w:val")) == "false"
    return {"citation_fields": expected_citations, "bibliography_fields": 1,
            "bibliography_entries": expected_bib, "zotero_preferences_chunks": len(chunks),
            "body_text_characters": len(text), "structural_checks": "passed",
            "style_checks": "explicit Times New Roman/black; no heading borders or theme fonts; style parts synchronized; automatic style updates disabled",
            "visual_verification": "pending root rendering and inspection"}


def main():
    content = load_json(CONTENT)
    export = load_json(EXPORT)  # Hard gate: no real Zotero export, no document.
    for key in ("zoteroVersion", "styleID", "items", "citations", "rendered", "bibliography"):
        if key not in export:
            raise ValueError(f"Zotero export is missing {key}")
    doc = Document()
    document_styles(doc)
    doc.add_paragraph(content["title"], style="Title")
    doc.add_paragraph(content["subtitle"], style="Subtitle")
    writer = CitationWriter(export)
    for section in content["sections"]:
        write_section(doc, section, writer)
    writer.finish()
    n_bib = add_bibliography(doc, export)
    doc.add_page_break()
    n_table1 = add_table1(doc)
    doc.add_page_break()
    add_table2(doc)
    add_table3(doc)
    add_figures(doc)
    explicit_heading_runs(doc)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    add_zotero_properties(OUTPUT, export)
    audit = verify_docx(OUTPUT, writer.index, n_bib)
    audit.update({"output": str(OUTPUT), "styleID": export["styleID"],
                  "table1_selected_rows": n_table1, "citations": writer.audit,
                  "content_sha256": hashlib.sha256(CONTENT.read_bytes()).hexdigest(),
                  "zotero_export_sha256": hashlib.sha256(EXPORT.read_bytes()).hexdigest()})
    CHECKS.parent.mkdir(parents=True, exist_ok=True)
    CHECKS.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in audit.items() if k != "citations"}, indent=2))


if __name__ == "__main__":
    main()
