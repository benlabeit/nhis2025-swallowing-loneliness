"""Build the Dysphagia master, anonymous manuscript and SNAPP information sheet.

Run from the project root only after the root agent's authoring marker:
    python outputs/manuscript_sources/build_dysphagia.py

After a native Zotero refresh of the master, regenerate only the anonymous copy:
    python outputs/manuscript_sources/build_dysphagia.py --anonymous-from-master

The original NLM manuscript and builder are never modified. The reviewer copy
contains no fields in its body and no Zotero data or author metadata. Its only
field is the standard PAGE field in the footer, retained for automatic numbering.
Rendering and visual inspection remain a separate, mandatory root-agent step.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from lxml import etree
from PIL import Image

ROOT = Path.cwd()
SOURCE = ROOT / "outputs/manuscript_sources/content.json"
ABSTRACT = Path(__file__).with_name("dysphagia_abstract.txt")
if not ABSTRACT.is_file():
    ABSTRACT = ROOT / "work/dysphagia_abstract.txt"
AUTHORS = Path(__file__).with_name("dysphagia_authors.json")
if not AUTHORS.is_file():
    AUTHORS = ROOT / "work/dysphagia_authors.json"
EXPORT = ROOT / "outputs/literature/zotero_citations_dysphagia.json"
FOLDER = ROOT / "outputs/dysphagia"
MASTER = FOLDER / "NHIS2025_Dysphagia_Master.docx"
ANONYMOUS = FOLDER / "NHIS2025_Dysphagia_Anonymous.docx"
AUTHOR_SHEET = FOLDER / "NHIS2025_Dysphagia_Author_Information.docx"
AUDIT = ROOT / "work/manuscript/dysphagia_build_checks.json"
TITLE = "Self reported swallowing problems and frequent loneliness in older US adults"
KEYWORDS = ["Swallowing problems", "Loneliness", "Older adults", "Social contact", "National Health Interview Survey"]
ACCEPTED_STYLES = {
    "http://www.zotero.org/styles/dysphagia",
    "http://www.zotero.org/styles/springer-vancouver-brackets",
}
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"

# Reuse the already reviewed numerical tables and low-level Word/Zotero helpers.
# Importing the original script does not call its main() or write any artifacts.
_spec = importlib.util.spec_from_file_location("nhis_original_builder", Path(__file__).with_name("build_manuscript.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def iter_paragraph_texts(content):
    def visit(section):
        yield from section.get("paragraphs", [])
        for child in section.get("subsections", []):
            yield from visit(child)
    for section in content["sections"]:
        yield from visit(section)


def prepare_content(source, abstract):
    content = copy.deepcopy(source)
    content["title"] = TITLE
    content.pop("subtitle", None)
    modifications = []
    resource_map = {
        "Supplementary Figure S1": "Online Resource 1, Fig. S1",
        "Supplementary Figure S2": "Online Resource 1, Fig. S2",
        "Supplementary Figure S3": "Online Resource 1, Fig. S3",
        "the supplementary tables": "Online Resource 2",
    }

    def visit(section):
        if section["heading"] == "Abstract":
            section["paragraphs"] = [abstract]
            return
        if section["heading"] == "Data availability and ethical considerations":
            section["heading"] = "Data availability"
            section["paragraphs"] = [
                "The analysis used deidentified public-use NHIS files available from the National Center for Health Statistics. "
                "Additional tabular results are provided in Online Resource 2. [[CDC2025,CDC_SURVEY]]"
            ]
            modifications.append("Ethics/consent moved to the SNAPP information sheet; data availability retains public CDC data and accompanying result tables without author-identifying repository links")
            return
        revised = []
        for text in section.get("paragraphs", []):
            new = text
            for old, replacement in resource_map.items():
                new = new.replace(old, replacement)
            if new != text:
                modifications.append({"original": text, "journal_version": new})
            revised.append(new)
        section["paragraphs"] = revised
        for child in section.get("subsections", []):
            visit(child)
    for section in content["sections"]:
        visit(section)
    old_markers = [m.group(1) for p in iter_paragraph_texts(source) for m in base.MARKERS.finditer(p)]
    new_markers = [m.group(1) for p in iter_paragraph_texts(content) for m in base.MARKERS.finditer(p)]
    if old_markers != new_markers:
        raise ValueError("Journal adaptation unexpectedly changed the literature citation sequence")
    return content, modifications


def validate_inputs(content, export, authors):
    if export.get("styleID") not in ACCEPTED_STYLES:
        raise ValueError("The real Zotero export must use Dysphagia or its Springer Vancouver brackets parent")
    for key in ("zoteroVersion", "items", "citations", "rendered", "bibliography"):
        if key not in export:
            raise ValueError(f"Missing real Zotero export component: {key}")
    markers = [m.group(1) for p in iter_paragraph_texts(content) for m in base.MARKERS.finditer(p)]
    if len(markers) != len(export["citations"]):
        raise ValueError("Citation count differs between manuscript and real Zotero export")
    rendered = {str(row[0]): base.plain_citeproc(row[2]) for row in export["rendered"]}
    for marker, cluster in zip(markers, export["citations"]):
        keys = [x.strip() for x in marker.split(",")]
        if cluster.get("keys") != keys:
            raise ValueError("Real Zotero cluster order does not match the manuscript")
        cached = rendered[str(cluster["citationID"])]
        if not re.fullmatch(r"\[[0-9,\s\-\u2013\u2014]+\]", cached):
            raise ValueError(f"Expected bracketed numeric journal citation, got {cached!r}")
        for key, item in zip(keys, cluster["citationItems"]):
            actual = export["items"][key]
            if item.get("id") != actual["id"] or actual["uri"] not in item.get("uris", []):
                raise ValueError(f"Citation is not linked to the exported real Zotero item: {key}")
    entries = export["bibliography"][1]
    for entry in entries:
        if re.search(r"\bdoi:\s*10\.", entry, flags=re.I):
            raise ValueError("Journal bibliography must render DOI identifiers as full DOI URLs")
    if len(authors["authors"]) != 11 or len(authors["affiliations"]) != 7:
        raise ValueError("The confirmed P1 author composition was unexpectedly changed")
    if len(KEYWORDS) not in range(4, 7):
        raise ValueError("Journal version requires four to six keywords")
    for number in range(1, 4):
        if not (FOLDER / "figures" / f"Fig{number}.png").is_file():
            raise FileNotFoundError(f"Journal artwork is not ready: Fig{number}.png")


def journal_styles(doc, identified=False, authors=None, administrative=False):
    base.document_styles(doc)
    doc.styles["Normal"].paragraph_format.line_spacing = 1.15 if administrative else 1.5
    doc.styles["Normal"].paragraph_format.space_after = Pt(6)
    doc.core_properties.title = TITLE
    doc.core_properties.subject = "Dysphagia research manuscript" if not administrative else "Author information and SNAPP declarations"
    doc.core_properties.author = "; ".join(a["name"] for a in authors["authors"]) if identified and authors else ""
    doc.core_properties.last_modified_by = ""
    doc.core_properties.comments = ""
    doc.core_properties.keywords = "; ".join(KEYWORDS)


def add_author_block(doc, authors):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_after = Pt(9)
    for index, author in enumerate(authors["authors"]):
        if index:
            base.set_font(paragraph.add_run(", "))
        base.set_font(paragraph.add_run(author["name"]))
        run = paragraph.add_run(",".join(str(n) for n in author["affiliation_numbers"]))
        base.set_font(run, 9)
        run.font.superscript = True
    for affiliation in authors["affiliations"]:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(str(affiliation["number"]))
        base.set_font(run, 9)
        run.font.superscript = True
        base.set_font(p.add_run(" " + affiliation["text"]))
    p = doc.add_paragraph(authors["corresponding_author"]["source_text"])
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(8)
    for run in p.runs:
        base.set_font(run)


def add_keywords(doc):
    p = doc.add_paragraph()
    base.set_font(p.add_run("Keywords: "), bold=True)
    base.set_font(p.add_run("; ".join(KEYWORDS)))


def add_body(doc, content, writer):
    for section in content["sections"]:
        base.write_section(doc, section, writer)
        if section["heading"] == "Abstract":
            add_keywords(doc)
    writer.finish()


def add_journal_tables(doc):
    doc.add_page_break()
    base.add_table1(doc)
    doc.add_page_break()
    base.add_table2(doc)
    base.add_table3(doc)
    # This table note has no fields and is safe to replace as a single run.
    for p in doc.paragraphs:
        if "Full category-level estimates and available-case characteristics are provided in the supplementary tables." in p.text:
            p.text = p.text.replace("in the supplementary tables.", "in Online Resource 2.")
            for run in p.runs:
                base.set_font(run, 10)


FIGURE_CAPTIONS = [
    "Survey-weighted prevalence of frequent loneliness by self-reported swallowing problems. Frequent loneliness means always or usually feeling lonely; swallowing problems refer to the preceding 12 months. Points show weighted prevalence and lines show design-based logit 95% confidence intervals. Valid-response denominators are 7,545 without and 686 with swallowing problems (N = 8,231). Counts are unweighted. No covariate adjustment was performed. Created in R 4.6.0 using grid graphics and Cairo devices",
    "Prevalence ratios across sequential adjustment models. All models use the same 8,094 adults with 429 events. M1 adds age and sex; M2 adds education, income-to-poverty ratio, partnership, living alone, mobility, hearing and stroke; primary M3 adds in-person and phone/video contact; M4 adds religious and group participation. M3 is highlighted by a diamond and color. Points and lines represent prevalence ratios and 95% confidence intervals from survey-weighted Poisson models. The logarithmic axis marks a prevalence ratio of 1. Income-adjusted estimates combine all ten official income imputations. These are cross-sectional associations. Created in R 4.6.0 using grid graphics and Cairo devices",
    "Secondary analysis of reported swallowing difficulty. M3-adjusted prevalence ratios compare a little difficulty, somewhere in between and a lot of difficulty with no swallowing problems. N = 8,093; the three exposed categories contain 361, 199 and 113 adults, with 33, 27 and 22 events. The reference category has no artificial interval. The categories are not equally spaced and no formal trend test was performed. Small event counts and self-reported severity limit interpretation. Created in R 4.6.0 using grid graphics and Cairo devices",
]


def add_journal_figures(doc):
    for number, caption in enumerate(FIGURE_CAPTIONS, 1):
        doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_after = Pt(8)
        image_path = FOLDER / "figures" / f"Fig{number}.png"
        with Image.open(image_path) as picture:
            width_px, height_px = picture.size
        width_inches = min(6.5, 6.4 * width_px / height_px)
        image = p.add_run().add_picture(str(image_path), width=Inches(width_inches))
        image._inline.docPr.set("descr", caption)
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        base.set_font(p.add_run(f"Fig. {number}"), bold=True)
        base.set_font(p.add_run(" " + caption.rstrip(". ")))


def save_package(path, files):
    temporary = path.with_name(path.stem + ".tmp.docx")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    temporary.replace(path)


def journal_zotero_properties(path, export):
    """Use genuine style metadata and the verified item journal abbreviations."""
    base.add_zotero_properties(path, export)
    with zipfile.ZipFile(path) as archive:
        files = {n: archive.read(n) for n in archive.namelist()}
    props = etree.fromstring(files["docProps/custom.xml"])
    chunks = sorted((p for p in props if p.get("name", "").startswith("ZOTERO_PREF_")), key=lambda p: int(p.get("name").rsplit("_", 1)[1]))
    data = etree.fromstring("".join(p[0].text or "" for p in chunks).encode())
    preferences = data.find("prefs")
    journal_pref = preferences.find("pref[@name='automaticJournalAbbreviations']")
    if journal_pref is None:
        journal_pref = etree.SubElement(preferences, "pref", name="automaticJournalAbbreviations")
    journal_pref.set("value", "false")
    for p in chunks:
        props.remove(p)
    text = etree.tostring(data, encoding="unicode")
    starting_pid = max([int(p.get("pid")) for p in props] + [1])
    for index, start in enumerate(range(0, len(text), 255), 1):
        p = etree.SubElement(props, f"{{{base.CUSTOM_NS}}}property", fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}", pid=str(starting_pid + index), name=f"ZOTERO_PREF_{index}")
        etree.SubElement(p, f"{{{base.VT_NS}}}lpwstr").text = text[start:start + 255]
    files["docProps/custom.xml"] = etree.tostring(props, encoding="UTF-8", xml_declaration=True, standalone=True)
    save_package(path, files)


def finish_plain_package(path, anonymous=False):
    """Preserve cached citation text, remove body fields and hidden review data."""
    with zipfile.ZipFile(path) as archive:
        files = {n: archive.read(n) for n in archive.namelist()}
    if "word/stylesWithEffects.xml" in files:
        files["word/stylesWithEffects.xml"] = files["word/styles.xml"]
    body = etree.fromstring(files["word/document.xml"])
    for node in list(body.xpath("//w:instrText | //w:fldChar", namespaces=NS)):
        node.getparent().remove(node)
    for node in list(body.xpath("//w:fldSimple", namespaces=NS)):
        parent = node.getparent()
        position = parent.index(node)
        for child in list(node):
            parent.insert(position, child)
            position += 1
        parent.remove(node)
    files["word/document.xml"] = etree.tostring(body, encoding="UTF-8", xml_declaration=True, standalone=True)
    removed = {n for n in files if n.startswith(("customXml/", "docProps/thumbnail")) or n == "docProps/custom.xml"}
    for name in removed:
        del files[name]
    for name in list(files):
        if not name.endswith(".rels"):
            continue
        root = etree.fromstring(files[name])
        for relationship in list(root):
            if relationship.get("Type", "").endswith(("/customXml", "/custom-properties", "/attachedTemplate", "/metadata/thumbnail")):
                root.remove(relationship)
        files[name] = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
    types = etree.fromstring(files["[Content_Types].xml"])
    for node in list(types):
        if node.get("PartName", "").lstrip("/") in removed:
            types.remove(node)
    files["[Content_Types].xml"] = etree.tostring(types, encoding="UTF-8", xml_declaration=True, standalone=True)
    if anonymous:
        core = etree.fromstring(files["docProps/core.xml"])
        for tag in (f"{{{DC_NS}}}creator", f"{{{CP_NS}}}lastModifiedBy", f"{{{DC_NS}}}description"):
            for node in core.findall(tag):
                node.text = ""
        files["docProps/core.xml"] = etree.tostring(core, encoding="UTF-8", xml_declaration=True, standalone=True)
        if "docProps/app.xml" in files:
            app = etree.fromstring(files["docProps/app.xml"])
            for node in app:
                if etree.QName(node.tag).localname in ("Company", "Manager"):
                    node.text = ""
            files["docProps/app.xml"] = etree.tostring(app, encoding="UTF-8", xml_declaration=True, standalone=True)
    save_package(path, files)


def build_manuscript(path, content, export, authors, anonymous):
    doc = Document()
    journal_styles(doc, identified=not anonymous, authors=authors)
    doc.add_paragraph(TITLE, style="Title")
    if not anonymous:
        add_author_block(doc, authors)
        doc.add_page_break()
    writer = base.CitationWriter(export)
    add_body(doc, content, writer)
    n_bib = base.add_bibliography(doc, export)
    add_journal_tables(doc)
    add_journal_figures(doc)
    base.explicit_heading_runs(doc)
    doc.save(path)
    if anonymous:
        finish_plain_package(path, anonymous=True)
    else:
        journal_zotero_properties(path, export)
    return {"path": str(path), "citation_clusters": writer.index, "bibliography_entries": n_bib, "cached_citations": writer.audit}


def add_admin_paragraph(doc, text, pending=False):
    p = doc.add_paragraph()
    if pending:
        base.set_font(p.add_run("To be completed before submission: "), bold=True)
    base.set_font(p.add_run(text))
    return p


def build_author_sheet(authors):
    doc = Document()
    journal_styles(doc, identified=True, authors=authors, administrative=True)
    doc.add_paragraph("Author information and declarations", style="Title")
    add_admin_paragraph(doc, TITLE)
    add_author_block(doc, authors)
    doc.add_heading("Funding", level=1)
    add_admin_paragraph(doc, authors["funding"]["source_text"])
    doc.add_heading("Competing interests", level=1)
    for author in authors["authors"]:
        if author.get("competing_interests"):
            add_admin_paragraph(doc, author["competing_interests"])
        else:
            add_admin_paragraph(doc, f"{author['name']}'s competing-interest declaration has not been supplied. No declaration of absence of competing interests is inferred.", pending=True)
    doc.add_heading("Author contributions", level=1)
    add_admin_paragraph(doc, "The authors must provide the contribution statement for this NHIS study. Contribution roles and any equal-contribution designation have not been supplied.", pending=True)
    doc.add_heading("Ethics approval and consent", level=1)
    add_admin_paragraph(doc, "The analysis used deidentified public-use NHIS files. No attempt was made to identify respondents or link them to identifiable records. NHIS obtains participant consent under its survey procedures.")
    add_admin_paragraph(doc, "The applicable local ethics determination and consent requirements for this secondary analysis have not been supplied. The authors must confirm these statements; no institutional approval, exemption, waiver or new participant-consent statement is inferred.", pending=True)
    doc.add_heading("Data and code availability", level=1)
    add_admin_paragraph(doc, "The original public-use data and documentation are available from the National Center for Health Statistics at https://www.cdc.gov/nchs/nhis/documentation/2025-nhis.html. Supplementary figures and tabular results accompany the submission as Online Resources 1 and 2. The analysis code and original downloaded files are retained in the project research package.")
    doc.add_heading("Additional submission information", level=1)
    add_admin_paragraph(doc, "ORCID identifiers, corresponding-author telephone/fax details and acknowledgements have not been supplied. This sheet is for the SNAPP author and declaration fields and must remain separate from the anonymous reviewer manuscript.")
    base.explicit_heading_runs(doc)
    doc.save(AUTHOR_SHEET)
    finish_plain_package(AUTHOR_SHEET)


def cached_export_from_master(export):
    """Read refreshed Word field caches without changing the authoring master."""
    updated = copy.deepcopy(export)
    with zipfile.ZipFile(MASTER) as archive:
        xml = etree.fromstring(archive.read("word/document.xml"))
    stack, fields = [], []
    for node in xml.iter():
        if node.tag == qn("w:p") and stack and stack[-1]["result"]:
            stack[-1]["text"] += "\n"
        elif node.tag == qn("w:fldChar"):
            kind = node.get(qn("w:fldCharType"))
            if kind == "begin":
                stack.append({"instruction": "", "text": "", "result": False})
            elif kind == "separate" and stack:
                stack[-1]["result"] = True
            elif kind == "end" and stack:
                fields.append(stack.pop())
        elif stack and node.tag == qn("w:instrText"):
            stack[-1]["instruction"] += node.text or ""
        elif stack and stack[-1]["result"] and node.tag == qn("w:t"):
            stack[-1]["text"] += node.text or ""
        elif stack and stack[-1]["result"] and node.tag == qn("w:tab"):
            stack[-1]["text"] += "\t"
    if stack:
        raise ValueError("Unclosed field in refreshed master")
    citations, bibliographies = {}, []
    for field in fields:
        if "ZOTERO_ITEM CSL_CITATION" in field["instruction"]:
            payload = json.loads(field["instruction"].split("CSL_CITATION", 1)[1].strip())
            citations[payload["citationID"]] = field["text"].strip()
        elif "ZOTERO_BIBL" in field["instruction"]:
            bibliographies.append([p.strip() for p in field["text"].split("\n") if p.strip()])
    if len(citations) != len(export["citations"]) or len(bibliographies) != 1:
        raise ValueError("Refreshed master does not have the expected citation/bibliography fields")
    if len(bibliographies[0]) != len(export["bibliography"][1]):
        raise ValueError("Refreshed bibliography paragraph count differs from the real export")
    updated["rendered"] = [[c["citationID"], 0, citations[c["citationID"]]] for c in export["citations"]]
    updated["bibliography"][1] = bibliographies[0]
    return updated


def audit_plain_document(path, authors, anonymous=False):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("DOCX ZIP integrity check failed")
        xml = etree.fromstring(archive.read("word/document.xml"))
        if xml.xpath("//w:instrText | //w:fldChar | //w:fldSimple", namespaces=NS):
            raise ValueError("A body field survived in the reviewer/admin document")
        whole_xml = "\n".join(archive.read(n).decode("utf-8") for n in archive.namelist() if n.endswith((".xml", ".rels")))
        if "ZOTERO_" in whole_xml or "zotero.org/users/" in whole_xml or "zotero.org/groups/" in whole_xml:
            raise ValueError("Zotero metadata survived plain-copy sanitization")
        instructions = []
        for name in archive.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                part = etree.fromstring(archive.read(name))
                instructions += [s.strip() for s in part.xpath("//w:instrText/text()", namespaces=NS)]
        if instructions != ["PAGE"]:
            raise ValueError(f"Only the automatic footer PAGE field may remain: {instructions}")
        if anonymous:
            for needle in [a["name"] for a in authors["authors"]] + [authors["corresponding_author"]["email"], "benlabeit", "github.com", "C:\\Users\\"]:
                if needle.casefold() in whole_xml.casefold():
                    raise ValueError(f"Identifying content remains in the anonymous document: {needle}")
            if xml.xpath("//w:commentRangeStart | //w:commentRangeEnd | //w:ins | //w:del", namespaces=NS):
                raise ValueError("Annotations or tracked revisions remain in reviewer document")
    return {"body_fields": 0, "zotero_metadata": "absent", "retained_footer_fields": ["PAGE"], "automatic_pagination_exception": "Only Word PAGE is retained, as explicitly approved", "anonymity_check": "passed" if anonymous else "not applicable"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anonymous-from-master", action="store_true")
    args = parser.parse_args()
    source = base.load_json(SOURCE)
    authors = base.load_json(AUTHORS)
    abstract = ABSTRACT.read_text(encoding="utf-8-sig").strip()
    content, modifications = prepare_content(source, abstract)
    export = base.load_json(EXPORT)
    validate_inputs(content, export, authors)
    FOLDER.mkdir(parents=True, exist_ok=True)
    audit = {"title": TITLE, "abstract_words": len(abstract.split()), "keywords": KEYWORDS,
             "styleID": export["styleID"], "automaticJournalAbbreviations": False, "source_content_sha256": sha256(SOURCE),
             "author_source_sha256": sha256(AUTHORS), "zotero_export_sha256": sha256(EXPORT),
             "authorized_adaptations": modifications,
             "online_resources": {"1": "ESM1.pdf; Figs. S1-S3", "2": "ESM2.xlsx; supplementary tabular results"},
             "visual_verification": "pending rendering and inspection of every page",
             "open_author_items": ["Anel Karisik competing interests", "study-specific author contributions", "applicable local ethics/consent determination"]}
    if args.anonymous_from_master:
        export = cached_export_from_master(export)
        validate_inputs(content, export, authors)
        audit["refreshed_master_sha256"] = sha256(MASTER)
        audit["anonymous"] = build_manuscript(ANONYMOUS, content, export, authors, anonymous=True)
        audit["anonymous"].update(audit_plain_document(ANONYMOUS, authors, anonymous=True))
        audit["operation"] = "anonymous copy regenerated from native Zotero field caches; master and author sheet unchanged"
    else:
        audit["master"] = build_manuscript(MASTER, content, export, authors, anonymous=False)
        audit["master"].update(base.verify_docx(MASTER, len(export["citations"]), len(export["bibliography"][1])))
        audit["anonymous"] = build_manuscript(ANONYMOUS, content, export, authors, anonymous=True)
        audit["anonymous"].update(audit_plain_document(ANONYMOUS, authors, anonymous=True))
        build_author_sheet(authors)
        audit["author_information"] = {"path": str(AUTHOR_SHEET), **audit_plain_document(AUTHOR_SHEET, authors)}
        audit["operation"] = "three journal DOCX files generated; original NLM files unchanged"
    for key in ("master", "anonymous", "author_information"):
        if key in audit:
            audit[key]["sha256"] = sha256(audit[key]["path"])
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in audit.items() if k not in ("authorized_adaptations", "master", "anonymous")}, indent=2))
    print("Created:", ANONYMOUS if args.anonymous_from_master else f"{MASTER}\n{ANONYMOUS}\n{AUTHOR_SHEET}")


if __name__ == "__main__":
    main()
