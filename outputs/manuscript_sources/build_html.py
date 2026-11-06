"""Build a standalone manuscript HTML using existing Zotero-rendered citations.

Reads JSON, the completed DOCX tables/captions, and three PNG figures; performs
no citation reformatting, Word automation, network requests, or source edits.
Usage: python build_html.py [--root PATH]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import io
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path

from docx import Document
from PIL import Image


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    root = parser.parse_args().root.resolve()
    out = root / 'outputs'
    paths = {
        'content': out / 'manuscript_sources/content.json',
        'zotero': out / 'literature/zotero_citations.json',
        'docx': out / 'NHIS2025_Manuscript_EN.docx',
    }
    before = {key: checksum(path) for key, path in paths.items()}
    content = json.loads(paths['content'].read_text(encoding='utf-8'))
    zotero = json.loads(paths['zotero'].read_text(encoding='utf-8'))
    require(isinstance(content.get('title'), str), 'Missing manuscript title')
    require(isinstance(content.get('sections'), list), 'Missing manuscript sections')
    require(len(zotero['items']) == 26, 'Expected 26 actual Zotero items')
    citations = zotero['citations']
    rendered = zotero['rendered']
    require(len(citations) == len(rendered), 'Citation/rendered count mismatch')
    rendered_by_id = {}
    for triple in rendered:
        require(isinstance(triple, list) and len(triple) == 3, 'Expected rendered citation triples')
        citation_id, _note, actual_text = triple
        require(isinstance(actual_text, str) and actual_text, 'Empty Zotero citation text')
        require(citation_id not in rendered_by_id, 'Duplicate rendered citation ID')
        rendered_by_id[citation_id] = actual_text

    token = re.compile(r'\[\[([A-Za-z0-9_,]+)\]\]')
    citation_position = 0
    used_keys = set()
    expected_citation_texts = []

    def paragraph(text):
        nonlocal citation_position
        require(isinstance(text, str), 'Non-string paragraph')
        pieces = []
        end = 0
        for match in token.finditer(text):
            pieces.append(html.escape(text[end:match.start()]))
            keys = match.group(1).split(',')
            require(all(key in zotero['items'] for key in keys), 'Unknown citation reference key')
            require(citation_position < len(citations), 'More source markers than Zotero citations')
            citation = citations[citation_position]
            expected_ids = {str(zotero['items'][key]['id']) for key in keys}
            actual_ids = {str(item['id']) for item in citation['citationItems']}
            require(expected_ids == actual_ids,
                    f'Citation items mismatch at marker {citation_position + 1}: {keys}')
            actual_text = rendered_by_id[citation['citationID']]
            pieces.append('<span class="citation" data-reference-keys="' +
                          html.escape(','.join(keys), quote=True) + '">' +
                          html.escape(actual_text) + '</span>')
            expected_citation_texts.append(actual_text)
            used_keys.update(keys)
            citation_position += 1
            end = match.end()
        pieces.append(html.escape(text[end:]))
        result = ''.join(pieces)
        require('[[' not in result and ']]' not in result, 'Unresolved citation marker')
        return '<p>' + result + '</p>'

    def section(block, level=2):
        require(isinstance(block.get('heading'), str), 'Missing section heading')
        heading = block['heading']
        anchor = re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')
        parts = [f'<section aria-labelledby="{anchor}">',
                 f'<h{level} id="{anchor}">{html.escape(heading)}</h{level}>']
        parts.extend(paragraph(text) for text in block.get('paragraphs', []))
        parts.extend(section(child, level + 1) for child in block.get('subsections', []))
        parts.append('</section>')
        return '\n'.join(parts)

    body = '\n'.join(section(block) for block in content['sections'])
    require(citation_position == len(citations), 'Not every Zotero citation was used')
    require(used_keys == set(zotero['items']), 'Referenced items do not match the 26 Zotero sources')
    bib_meta, bib_entries = zotero['bibliography']
    require(not bib_meta.get('bibliography_errors'), 'Zotero reports bibliography errors')
    require(len(bib_entries) == len(bib_meta['entry_ids']) == 26, 'Expected 26 bibliography entries')
    item_ids = {str(value['id']) for value in zotero['items'].values()}
    bibliography_ids = {str(x) for ids in bib_meta['entry_ids'] for x in ids}
    require(item_ids == bibliography_ids, 'Bibliography IDs do not match Zotero items')
    bibliography = ['<section aria-labelledby="references"><h2 id="references">References</h2>',
                    '<div class="bibliography">']
    for index, entry in enumerate(bib_entries, 1):
        require(isinstance(entry, str) and entry.strip(), 'Empty bibliography entry')
        bibliography.append(f'<p class="reference" id="reference-{index}">' +
                            html.escape(entry.strip()) + '</p>')
    bibliography.append('</div></section>')

    # Read only the finalized table contents and associated caption paragraphs.
    doc = Document(paths['docx'])
    require(len(doc.tables) == 3, 'Expected three finalized DOCX tables')
    blocks = {}
    current = None
    for para in doc.paragraphs:
        text = para.text.strip()
        match = re.match(r'^(Table|Figure) ([123])(?:\s|$)', text)
        if match:
            current = (match.group(1), int(match.group(2)))
            require(current not in blocks, 'Duplicate DOCX table/figure caption block')
            blocks[current] = {'heading': text, 'notes': []}
        elif current and text:
            blocks[current]['notes'].append(text)

    tables_html = ['<section aria-labelledby="tables"><h2 id="tables">Tables</h2>']
    source_table_values = []
    for number, table in enumerate(doc.tables, 1):
        block = blocks[('Table', number)]
        values = [[cell.text for cell in row.cells] for row in table.rows]
        source_table_values.append(values)
        require(len(values) > 1 and all(len(row) == len(values[0]) for row in values),
                'Inconsistent DOCX table dimensions')
        tables_html.append(f'<div class="table-container" tabindex="0" role="region" '
                           f'aria-labelledby="table-{number}-caption">')
        tables_html.append(f'<table id="table-{number}" class="table-{number}"><caption '
                           f'id="table-{number}-caption">{html.escape(block["heading"])}</caption>')
        for row_index, row in enumerate(values):
            if row_index == 0:
                tables_html.append('<thead><tr>')
            else:
                if row_index == 1:
                    tables_html.append('<tbody>')
                tables_html.append('<tr>')
            for column_index, cell in enumerate(row):
                tag = 'th' if row_index == 0 or column_index == 0 else 'td'
                scope = ' scope="col"' if row_index == 0 else (' scope="row"' if column_index == 0 else '')
                cell_html = '<br>'.join(html.escape(line) for line in cell.split('\n'))
                tables_html.append(f'<{tag}{scope}>{cell_html}</{tag}>')
            tables_html.append('</tr>' + ('</thead>' if row_index == 0 else ''))
        tables_html.append('</tbody></table></div>')
        tables_html.extend('<p class="table-note">' + html.escape(note) + '</p>'
                           for note in block['notes'])
    tables_html.append('</section>')

    figures_html = ['<section aria-labelledby="figures"><h2 id="figures">Figures</h2>']
    figure_files = ['Figure1_Weighted_Prevalence.png', 'Figure2_Sequential_Models.png',
                    'Figure3_Severity.png']
    figure_details = []
    for number, filename in enumerate(figure_files, 1):
        data = (out / 'figures_en' / filename).read_bytes()
        with Image.open(io.BytesIO(data)) as picture:
            require(picture.format == 'PNG', 'Figure is not PNG')
            width, height = picture.size
        block = blocks[('Figure', number)]
        require(len(block['notes']) == 1, f'Expected one caption for Figure {number}')
        caption = block['notes'][0]
        figures_html.extend([
            f'<figure id="figure-{number}">',
            f'<img width="{width}" height="{height}" alt="{html.escape(caption, quote=True)}" '
            f'src="data:image/png;base64,{base64.b64encode(data).decode("ascii")}">',
            f'<figcaption><strong>Figure {number}.</strong> {html.escape(caption)}</figcaption>',
            '</figure>',
        ])
        figure_details.append({'file': filename, 'width': width, 'height': height,
                               'sha256': hashlib.sha256(data).hexdigest()})
    figures_html.append('</section>')

    style = '''
* { box-sizing: border-box; }
html { scroll-behavior: smooth; background: #fff; color: #111; }
body { margin: 0; font-family: Georgia, "Times New Roman", serif; font-size: 17px; line-height: 1.65; }
main { max-width: 900px; margin: 0 auto; padding: 56px 30px 72px; }
header { margin-bottom: 38px; border-bottom: 1px solid #777; padding-bottom: 28px; }
h1, h2, h3 { color: #000; line-height: 1.23; font-weight: 700; }
h1 { font-size: 2rem; margin: 0 0 15px; }
h2 { font-size: 1.5rem; margin: 38px 0 15px; }
h3 { font-size: 1.14rem; margin: 25px 0 10px; }
p { margin: 0 0 17px; }
.subtitle { font-size: 1.15rem; margin: 0; }
.citation { white-space: nowrap; }
.bibliography { font-size: .89rem; line-height: 1.5; }
.reference { padding-left: 2.15em; text-indent: -2.15em; overflow-wrap: anywhere; }
.table-container { width: 100%; overflow-x: auto; margin-top: 28px; }
table { width: 100%; border-collapse: collapse; font-size: .84rem; line-height: 1.45; }
caption { text-align: left; font-weight: 700; font-size: 1.02rem; line-height: 1.4; padding: 0 0 13px; }
thead { border-top: 1.5px solid #111; border-bottom: 1px solid #333; }
th, td { text-align: right; padding: 9px 9px; vertical-align: top; }
th:first-child, td:first-child { text-align: left; }
tbody th { font-weight: 400; }
tbody tr { border-bottom: 1px solid #ddd; }
tbody tr:last-child { border-bottom: 1.5px solid #111; }
.table-1 th:first-child { width: 46%; }
.table-1, .table-2 { min-width: 500px; }
.table-3 { min-width: 780px; font-size: .77rem; }
.table-3 th:first-child { width: 23%; }
.table-3 th, .table-3 td { padding: 8px 6px; }
.table-note { font-size: .8rem; line-height: 1.5; margin: 10px 0 27px; }
figure { margin: 30px 0 42px; }
img { display: block; width: 100%; height: auto; }
figcaption { font-size: .86rem; line-height: 1.55; margin-top: 12px; }
@media (max-width: 600px) {
  body { font-size: 16px; }
  main { padding: 30px 18px 45px; }
  h1 { font-size: 1.65rem; }
  h2 { font-size: 1.35rem; }
}
@media print {
  body { font-size: 10.5pt; line-height: 1.45; }
  main { max-width: none; padding: 0; }
  h1 { font-size: 19pt; }
  h2 { font-size: 15pt; break-after: avoid; }
  h3, caption { break-after: avoid; }
  p { orphans: 3; widows: 3; }
  .table-container { overflow: visible; }
  table, .table-3 { min-width: 0; }
  thead { display: table-header-group; }
  tr { break-inside: avoid; }
  figure { break-inside: avoid; }
  .reference { break-inside: avoid; }
}
'''
    title = html.escape(content['title'])
    result = '\n'.join([
        '<!doctype html>', '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<title>{title}</title>', '<style>' + style + '</style></head><body><main>',
        f'<header><h1>{title}</h1><p class="subtitle">{html.escape(content.get("subtitle", ""))}</p></header>',
        body, '\n'.join(bibliography), '\n'.join(tables_html), '\n'.join(figures_html),
        '</main></body></html>',
    ])
    require('[[' not in result and ']]' not in result, 'Unresolved markers in HTML')

    class ValidateHTML(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.images = []
            self.tables = []
            self.row = None
            self.cell = None
            self.in_citation = False
            self.citation_texts = []
            self.references = 0
            self.dependency_errors = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'img':
                self.images.append(attrs['src'])
            if tag in ['script', 'iframe', 'link', 'video', 'audio', 'object', 'embed']:
                self.dependency_errors.append(tag)
            if tag == 'span' and attrs.get('class') == 'citation':
                self.in_citation = True
                self.citation_texts.append('')
            if tag == 'p' and attrs.get('class') == 'reference':
                self.references += 1
            if tag == 'table': self.tables.append([])
            if tag == 'tr': self.row = []
            if tag in ['td', 'th']: self.cell = ''
            if tag == 'br' and self.cell is not None: self.cell += '\n'
        def handle_data(self, data):
            if self.in_citation: self.citation_texts[-1] += data
            if self.cell is not None: self.cell += data
        def handle_endtag(self, tag):
            if tag == 'span': self.in_citation = False
            if tag in ['td', 'th']:
                self.row.append(self.cell)
                self.cell = None
            if tag == 'tr':
                self.tables[-1].append(self.row)
                self.row = None

    check = ValidateHTML()
    check.feed(result)
    require(check.citation_texts == expected_citation_texts, 'Rendered citation texts altered')
    require(check.references == 26, 'Incorrect reference count in HTML')
    require(check.tables == source_table_values, 'HTML table cells differ from DOCX')
    require(len(check.images) == 3 and all(x.startswith('data:image/png;base64,') for x in check.images),
            'Expected three embedded PNG images')
    require(not check.dependency_errors and 'url(' not in style, 'Unexpected external dependency')
    for index, image_src in enumerate(check.images):
        decoded = base64.b64decode(image_src.split(',', 1)[1], validate=True)
        require(hashlib.sha256(decoded).hexdigest() == figure_details[index]['sha256'], 'Image corruption')
    require(before == {key: checksum(path) for key, path in paths.items()}, 'Source input changed')
    target = out / 'NHIS2025_Manuscript_EN.html'
    target.write_text(result, encoding='utf-8')
    copied_script = out / 'manuscript_sources/build_html.py'
    copied_script.parent.mkdir(parents=True, exist_ok=True)
    if copied_script.resolve() != Path(__file__).resolve():
        shutil.copy2(__file__, copied_script)
    report = {
        'output': str(target), 'bytes': target.stat().st_size,
        'reference_count': check.references, 'citation_cluster_count': citation_position,
        'citation_texts_exactly_match_zotero': True,
        'table_count': len(check.tables), 'table_cells_exactly_match_docx': True,
        'table_dimensions': [[len(x), len(x[0])] for x in check.tables],
        'embedded_figures': figure_details, 'external_dependencies': 0,
        'source_checksums_unchanged': before,
        'validation_scope': 'Source/schema/content/embedding checks; no browser or Word visual QA performed.',
    }
    validation_path = root / 'work/manuscript/html_validation.json'
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
