"""Remove identifying package metadata and validate every exported source cell.

Only package metadata is edited here. Spreadsheet authoring is performed by
build_esm2.mjs with the bundled Artifact Tool; no worksheet content is changed.
"""
import csv, hashlib, io, json, math, pathlib, re, sys, zipfile
import xml.etree.ElementTree as ET

root=pathlib.Path(sys.argv[1]).resolve()
target=root/'outputs/dysphagia/ESM2.xlsx'
manifest=json.loads((root/'work/esm2/manifest.json').read_text(encoding='utf-8'))
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
with zipfile.ZipFile(target) as z:
    package={n:z.read(n) for n in z.namelist()}
changes=[]
for name in ['docProps/core.xml','docProps/app.xml']:
    if name in package:
        tree=ET.fromstring(package[name])
        for child in list(tree):
            local=child.tag.rsplit('}',1)[-1]
            if local in ['creator','lastModifiedBy','Company','Manager']:
                tree.remove(child);changes.append(name+':'+local)
        package[name]=ET.tostring(tree,encoding='utf-8',xml_declaration=True)
if 'docProps/custom.xml' in package:
    del package['docProps/custom.xml'];changes.append('docProps/custom.xml')
    for name in ['[Content_Types].xml','_rels/.rels']:
        if name not in package:continue
        tree=ET.fromstring(package[name])
        for child in list(tree):
            if child.attrib.get('PartName')=='/docProps/custom.xml' or child.attrib.get('Target','').lstrip('/')=='docProps/custom.xml':tree.remove(child)
        package[name]=ET.tostring(tree,encoding='utf-8',xml_declaration=True)

strings=[]
if 'xl/sharedStrings.xml' in package:
    strings=[''.join(x.itertext()) for x in ET.fromstring(package['xl/sharedStrings.xml']).findall('s:si',ns)]
workbook=ET.fromstring(package['xl/workbook.xml'])
rels=ET.fromstring(package['xl/_rels/workbook.xml.rels'])
relmap={x.attrib['Id']:x.attrib['Target'] for x in rels}
sheets={x.attrib['name']:x.attrib['{'+ns['r']+'}id'] for x in workbook.findall('s:sheets/s:sheet',ns)}
assert list(sheets)==manifest['worksheets']

def col(index):
    s='';index+=1
    while index:index,r=divmod(index-1,26);s=chr(65+r)+s
    return s

checked=0;numeric=0;formula_count=0;row_counts={}
for source in manifest['sources']:
    rel=relmap[sheets[source['sheet']]]
    name=rel.lstrip('/') if rel.startswith('/') else 'xl/'+rel
    tree=ET.fromstring(package[name])
    formula_count+=len(tree.findall('.//s:f',ns))
    cells={}
    for c in tree.findall('.//s:sheetData/s:row/s:c',ns):
        t=c.attrib.get('t');v=c.find('s:v',ns)
        if t=='s':value=strings[int(v.text)] if v is not None else ''
        elif t=='inlineStr':value=''.join(c.find('s:is',ns).itertext())
        elif v is None:value=''
        elif t=='b':value=v.text=='1'
        elif t in ['str','e']:value=v.text or ''
        else:value=float(v.text)
        cells[c.attrib['r']]=value
    expected=[source['headers'],*source['values']]
    for r,row in enumerate(expected,6):
        for j,value in enumerate(row):
            got=cells.get(f'{col(j)}{r}','')
            if isinstance(value,(int,float)) and not isinstance(value,bool):
                assert isinstance(got,(int,float)) and not isinstance(got,bool),(source['sheet'],r,j,'numeric type',got)
                assert got==float(value),(source['sheet'],r,j,got,value)
                numeric+=1
            else:assert got==value,(source['sheet'],r,j,got,value)
            checked+=1
    assert not any(int(re.search(r'\d+',cell).group())>len(source['values'])+6 and value!='' for cell,value in cells.items())
    row_counts[source['sheet']]=len(source['values'])
    src=root/'outputs'/source['relative']
    assert hashlib.sha256(src.read_bytes()).hexdigest()==source['sha256']
assert formula_count==0
identifiers=re.compile(r'Cinja|Bendix|Labeit|benlabeit|github\.com|C:\\Users|C:/Users',re.I)
for name,data in package.items():
    if name.endswith(('.xml','.rels')):
        text=data.decode('utf-8')
        assert not identifiers.search(text),('Identifying content',name)
        assert 'externalLink' not in name,('External link',name)
assert 'docProps/custom.xml' not in package

buffer=io.BytesIO()
with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in package.items():z.writestr(name,data)
target.write_bytes(buffer.getvalue())
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert set(z.namelist())==set(package)
    for name in z.namelist():assert z.read(name)==package[name]
report={'status':'PASS','worksheet_count':len(sheets),'source_file_count':len(manifest['sources']),
        'extended_tsv_count':manifest['extendedTsvCount'],'verified_source_cells':checked,
        'numeric_cells_compared_exactly':numeric,'formula_count':formula_count,'source_row_counts':row_counts,
        'metadata_removed':changes,'identifying_strings_found':0,'source_files_unchanged':True,
        'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
(root/'work/esm2/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
