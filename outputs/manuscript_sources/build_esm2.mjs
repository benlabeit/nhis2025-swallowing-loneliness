// Export existing NHIS aggregate results without recalculating statistics.
// Usage: bundled-node build_esm2.mjs [project-root]
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(process.argv[2] || path.join(here, '../..'));
const bundle = process.env.CODEX_BUNDLED_MODULES || path.join(process.env.USERPROFILE,
  '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const requireBundle = createRequire(path.join(bundle, '_esm2_loader.cjs'));
const { Workbook, SpreadsheetFile } = await import(pathToFileURL(requireBundle.resolve('@oai/artifact-tool')).href);
const out = path.join(root, 'outputs/dysphagia');
const qa = path.join(root, 'work/esm2');
await fs.mkdir(out, {recursive:true});
await fs.mkdir(qa, {recursive:true});

const specs = [
  ['extended_tables/table1_characteristics.tsv','Characteristics','Participant characteristics','Prevalence and intervals: proportion. Counts: unweighted.'],
  ['extended_tables/table1_income_ten_imputations.tsv','Income imputations','Income across ten imputations','Percent columns: 0–100. Counts: unweighted range.'],
  ['extended_tables/standardized_prevalence_and_contrasts.tsv','Standardized estimates','Standardized prevalence and contrasts','Prevalence and differences: proportion. Ratios: unitless.'],
  ['extended_tables/loneliness_five_categories.tsv','Loneliness categories','Five loneliness response categories','Prevalence and intervals: proportion. Counts: unweighted.'],
  ['extended_tables/NCHS_precision_primary_prevalences.tsv','Prevalence precision','Precision of primary prevalence estimates','Prevalence and interval width: proportion. Counts: unweighted.'],
  ['extended_tables/included_excluded_characteristics.tsv','Included vs excluded','Included and excluded respondents','Prevalence: proportion. Missing weighted percent: 0–100.'],
  ['extended_tables/response_weighted_M3_PR.tsv','Response weighted PR','Response-weighted primary model','Estimates and confidence limits: prevalence ratio.'],
  ['extended_tables/response_model_coefficients.tsv','Response coefficients','Response model coefficients','Logit coefficients and their standard errors.'],
  ['extended_tables/response_weight_diagnostics.tsv','Response diagnostics','Response-weight diagnostics','Counts, proportions and weight multipliers as labeled.'],
  ['extended_tables/threshold_specific_swallowing_OR.tsv','Threshold odds ratios','Threshold-specific swallowing odds ratios','Estimates and confidence limits: odds ratio.'],
  ['extended_tables/proportional_odds_diagnostics.tsv','Proportional odds checks','Proportional-odds diagnostics','Log odds-ratio differences and p values.'],
  ['extended_tables/diagnostics_M3.tsv','Primary diagnostics','Primary logistic-model diagnostics','Fitted probabilities: proportion. Counts: unweighted.'],
  ['extended_tables/diagnostics_M3_broad.tsv','Broad outcome diagnostics','Broader-outcome logistic diagnostics','Fitted probabilities: proportion. Counts: unweighted.'],
  ['extended_tables/diagnostics_M3_depression.tsv','Depression diagnostics','Depression-adjusted logistic diagnostics','Fitted probabilities: proportion. Counts: unweighted.'],
  ['extended_tables/diagnostics_M3_depression_matched.tsv','Matched diagnostics','Matched-sample logistic diagnostics','Fitted probabilities: proportion. Counts: unweighted.'],
  ['extended_tables/joint_score_validation.tsv','Joint covariance check','Joint-score covariance validation','Maximum absolute covariance difference.'],
  ['extended_tables/threshold_covariance_validation.tsv','Threshold covariance check','Threshold covariance validation','Maximum absolute covariance difference.'],
  ['extended_tables/ordinal_model_decision.txt','Ordinal decision','Ordinal-model decision','Recorded analysis decision.'],
  ['extended_tables/session_info.txt','Analysis software','Analysis software environment','Original R session information.'],
  ['tables/coefficients_M3_severity.tsv','Severity coefficients','Severity-model coefficients','PR: prevalence ratio. Log estimates: natural logarithm.'],
  ['tables/severity_outcome_complete.tsv','Severity common sample','Severity by loneliness in the common sample','Counts: unweighted. Lonely: 1 frequent, 0 otherwise.'],
  ['tables/severity_outcome_65plus.tsv','Severity available sample','Severity by loneliness in available responses','Counts: unweighted. Lonely: 1 frequent, 0 otherwise.'],
  ['tables/missing_65plus.tsv','Missing responses','Missing responses among eligible adults','Missing counts and percentages (0–100).'],
  ['tables/participant_flow.tsv','Participant flow','Participant flow','Counts: unweighted respondents.'],
];
const forbidden = /Cinja|Bendix|Labeit|benlabeit|github\.com|C:\\Users|C:\/Users/i;
function parseTsv(text) {
  const rows=[]; let row=[], cell='', quoted=false;
  text=text.replace(/^\uFEFF/,'');
  for(let i=0;i<text.length;i++) {
    const char=text[i];
    if(char==='"') {
      if(quoted && text[i+1]==='"') {cell+='"';i++;}
      else quoted=!quoted;
    } else if(!quoted && (char==='\t'||char==='\n'||char==='\r')) {
      row.push(cell);cell='';
      if(char!=='\t') {rows.push(row);row=[];if(char==='\r'&&text[i+1]==='\n')i++;}
    } else cell+=char;
  }
  if(cell.length||row.length) {row.push(cell);rows.push(row);}
  if(quoted) throw new Error('Unclosed quoted TSV field');
  return rows;
}
function letter(n) {let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
function sha(buffer) {return crypto.createHash('sha256').update(buffer).digest('hex');}
const labelColumns = new Set(['model','measure','label','variable','category','status','complement_status','population','note','contrast','reject','term','statistic','severity','stage','Text']);
const numericPattern=/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;
const glossary={
 label:'Group or population label', variable:'Analysis variable', category:'Original category label or code',
 prevalence:'Weighted prevalence (proportion, 0–1)', se:'Standard error in the estimate scale',
 lower_KG:'Lower 95% Korn–Graubard confidence bound (proportion)', upper_KG:'Upper 95% Korn–Graubard confidence bound (proportion)',
 denominator_n:'Unweighted valid-response denominator', numerator_n:'Unweighted category count',
 effective_n:'Effective sample size', effective_n_df_adjusted:'Effective sample size adjusted for design degrees of freedom',
 design_df:'Survey design degrees of freedom', CI_width:'Confidence-interval width (proportion)', relative_CI_width:'Confidence-interval width divided by prevalence',
 status:'NCHS presentation status for this estimate', complement_status:'NCHS presentation status for the complementary proportion',
 missing_n:'Unweighted number missing', group_n:'Unweighted group size', missing_weighted_percent:'Survey-weighted missing percentage (0–100)',
 population:'Available-response or common regression sample', swallow:'Swallowing-problem code: 1 yes; 0 no',
 weighted_percent:'Survey-weighted percentage (0–100)', se_percent:'Standard error in percentage points', n_min:'Minimum unweighted count across income imputations', n_max:'Maximum unweighted count across income imputations', note:'Original analysis note',
 model:'Original analysis model identifier', measure:'Reported estimand or outcome threshold', estimate:'Estimate; units depend on measure', lower:'Lower 95% confidence limit in the estimate scale', upper:'Upper 95% confidence limit in the estimate scale',
 df:'Degrees of freedom used for inference', n:'Unweighted sample size', events:'Unweighted number meeting the loneliness outcome', imputation:'Official income-imputation number (1–10)',
 min_prediction:'Minimum fitted probability', max_prediction:'Maximum fitted probability',
 term:'Model coefficient term', coefficient:'Response-model logit coefficient', statistic:'Diagnostic statistic identifier', value:'Diagnostic value in the labeled units',
 contrast:'Slope comparison across loneliness thresholds', log_OR_difference:'Difference between log odds-ratio coefficients', p_unadjusted:'Unadjusted p value', p_Bonferroni:'Bonferroni-adjusted p value', reject:'Original proportional-odds diagnostic decision',
 max_covariance_difference:'Largest absolute covariance difference in the validation',
 log_estimate:'Natural logarithm of the ratio estimate', se_log:'Standard error of the log estimate',
 severity:'Original self-reported swallowing-difficulty category', lonely:'Frequent-loneliness code: 1 yes; 0 no', Freq:'Unweighted cell count',
 n_65plus:'Unweighted eligible population aged 65 or older', missing:'Unweighted missing-response count', percent_missing:'Unweighted missing percentage (0–100)', stage:'Participant inclusion stage', Line:'Original text line number', Text:'Original analysis record text'
};
const files=[];
for(const [relative,sheet,title,units] of specs) {
  const bytes=await fs.readFile(path.join(root,'outputs',relative));
  const text=bytes.toString('utf8');
  if(forbidden.test(text)) throw new Error(`Identifying content in reviewer source ${relative}`);
  let raw;
  if(relative.endsWith('.tsv')) raw=parseTsv(text);
  else {let lines=text.replace(/\r\n/g,'\n').split('\n');if(lines.at(-1)==='')lines.pop();raw=[['Line','Text'],...lines.map((x,i)=>[String(i+1),x])];}
  const headers=raw[0];
  if(raw.some(row=>row.length!==headers.length))throw new Error('Nonrectangular source '+relative);
  const values=raw.slice(1).map(row=>row.map((value,i)=>!labelColumns.has(headers[i])&&numericPattern.test(value)?Number(value):value));
  files.push({relative,sheet,title,units,headers,values,rawRows:raw.slice(1),sha256:sha(bytes)});
}
const actual=(await fs.readdir(path.join(root,'outputs/extended_tables'))).filter(x=>x.endsWith('.tsv')).sort();
const covered=files.filter(x=>x.relative.startsWith('extended_tables/')&&x.relative.endsWith('.tsv')).map(x=>path.basename(x.relative)).sort();
if(JSON.stringify(actual)!==JSON.stringify(covered))throw new Error('Extended TSV coverage mismatch');

const workbook=Workbook.create();
const index=workbook.worksheets.add('Contents');
index.showGridLines=false;
index.getRange('A1:F110').format.font={name:'Arial',size:10,color:'#171717'};
index.getRange('A2').values=[['Online Resource 2. Supplementary tables']];
index.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#111111'};
index.getRange('A4').values=[['NHIS 2025: swallowing problems and frequent loneliness among adults aged 65 years or older']];
index.getRange('A5').values=[['Original aggregate results. No statistics have been recalculated.']];
index.getRange('A6').values=[['All source labels and numeric values are retained. NA denotes a source missing value; blank text lines are retained.']];
const indexHeaders=['Worksheet','Source file','Rows','Columns','Content and units'];
const indexRows=files.map(x=>[x.sheet,x.relative,x.values.length,x.headers.length,x.units]);
index.getRange(`A8:E${8+indexRows.length}`).values=[indexHeaders,...indexRows];
index.getRange('A8:E8').format={fill:'#E6E9EC',font:{name:'Arial',size:10,bold:true,color:'#111111'},wrapText:true,verticalAlignment:'center'};
index.getRange('A8:E8').format.rowHeight=32;
index.getRange(`A9:E${8+indexRows.length}`).format.rowHeight=32;
index.getRange(`A9:E${8+indexRows.length}`).format.wrapText=true;
index.getRange('A:A').format.columnWidth=31;
index.getRange('B:B').format.columnWidth=65;
index.getRange('C:D').format.columnWidth=10;
index.getRange('E:E').format.columnWidth=64;
index.getRange('F:F').format.columnWidth=3;
index.getRange(`C9:D${8+indexRows.length}`).setNumberFormat('0');
const keys=[...new Set(files.flatMap(f=>f.headers))];
const start=files.length+12;
index.getRange(`A${start}`).values=[['Column definitions']];
index.getRange(`A${start}`).format.font={name:'Arial',size:12,bold:true};
index.getRange(`A${start+2}:B${start+2+keys.length}`).values=[['Source column','Meaning and units'],...keys.map(k=>[k,glossary[k]||'Source column; unchanged'])];
index.getRange(`A${start+2}:B${start+2}`).format={fill:'#E6E9EC',font:{bold:true},wrapText:true};
index.getRange(`A${start+3}:B${start+2+keys.length}`).format.wrapText=true;
index.getRange(`A${start+3}:B${start+2+keys.length}`).format.rowHeight=30;
index.freezePanes.freezeRows(8);

const previews=[];
const sheets=[];
for(const file of files) {
  const s=workbook.worksheets.add(file.sheet);s.showGridLines=false;
  const n=file.headers.length, last=letter(n-1), end=file.values.length+6;
  s.getRange(`A1:${last}${Math.max(end,7)}`).format.font={name:'Arial',size:10,color:'#171717'};
  s.getRange('A2').values=[[file.title]];s.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#111111'};
  s.getRange('A3').values=[['Source: '+file.relative]];
  s.getRange('A4').values=[[file.units]];
  s.getRange('A3:A4').format.font={name:'Arial',size:9,color:'#404040'};
  s.getRange(`A6:${last}${end}`).values=[file.headers,...file.values];
  s.getRange(`A6:${last}6`).format={fill:'#E6E9EC',font:{name:'Arial',size:10,bold:true,color:'#111111'},wrapText:true,verticalAlignment:'center',horizontalAlignment:'center'};
  s.getRange(`A6:${last}6`).format.rowHeight=44;
  if(end>=7)s.getRange(`A7:${last}${end}`).format.rowHeight=22;
  for(let i=0;i<n;i++) {
    const key=file.headers[i], col=letter(i);
    const values=file.values.map(r=>r[i]);
    const maxLength=Math.max(key.length,...values.map(v=>typeof v==='string'?v.length:0));
    const width=key==='Text'?105:labelColumns.has(key)?Math.max(22,Math.min(58,maxLength+2)):Math.max(16,Math.min(27,key.length+2));
    s.getRange(`${col}:${col}`).format.columnWidth=width;
    const range=s.getRange(`${col}7:${col}${Math.max(end,7)}`);
    range.format.horizontalAlignment=labelColumns.has(key)?'left':'right';
    range.setNumberFormat('General');
    if(values.some(x=>typeof x==='string'&&x.length>width-3)) {range.format.wrapText=true;}
    if(['prevalence','se','lower_KG','upper_KG','CI_width','relative_CI_width'].includes(key)&&file.headers.includes('prevalence')) range.setNumberFormat('0.0000');
    else if(/^(n|events|Freq|missing|denominator_n|numerator_n|group_n|missing_n|n_min|n_max|n_65plus|imputation|Line)$/.test(key))range.setNumberFormat('#,##0');
    else if(/^(df|design_df|effective_n|effective_n_df_adjusted)$/.test(key))range.setNumberFormat('0.00');
    else if(/percent/.test(key))range.setNumberFormat('0.0000');
    else if(/^(p_|max_covariance_difference)/.test(key))range.setNumberFormat('0.00000E+00');
    else if(['estimate','lower','upper','coefficient','se','log_estimate','se_log','log_OR_difference','min_prediction','max_prediction'].includes(key))range.setNumberFormat('0.000000');
  }
  // Fit wrapped labels, while retaining legible normal-sized text.
  for(let i=0;i<file.values.length;i++) {
    const lineCount=Math.max(...file.values[i].map((v,j)=>typeof v==='string'?Math.ceil(Math.max(1,v.length)/(file.headers[j]==='Text'?100:Math.max(18,Math.min(55,Math.max(file.headers[j].length,...file.values.map(r=>typeof r[j]==='string'?r[j].length:0))+1)))):1));
    if(lineCount>1)s.getRange(`A${i+7}:${last}${i+7}`).format.rowHeight=22*lineCount;
  }
  if(n===2){s.getRange('A:A').format.columnWidth=file.headers[0]==='Line'?12:54;if(file.headers[0]!=='Line')s.getRange('B:B').format.columnWidth=36;}
  s.freezePanes.freezeRows(6);
  if(n>7)s.freezePanes.freezeColumns(Math.min(3,n));
  const table=s.tables.add(`A6:${last}${end}`,true,'Results'+(sheets.length+1));
  table.showFilterButton=true;
  const got=s.getRange(`A7:${last}${end}`).values;
  if(JSON.stringify(got)!==JSON.stringify(file.values))throw new Error('Cell mismatch before export '+file.relative);
  sheets.push({s,file,last,end});
}
workbook.recalculate();
console.log((await workbook.inspect({kind:'table',range:"'Standardized estimates'!A6:H11",include:'values,formulas',tableMaxRows:6,tableMaxCols:8,maxChars:1800})).ndjson);
console.log((await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'Error scan',maxChars:1200})).ndjson);
const previewSpecs=[{s:index,name:'Contents',range:'A1:E16'},...sheets.map(({s,file,last,end})=>({s,name:file.sheet,range:`A1:${last}${Math.min(end,12)}`}))];
for(let i=0;i<previewSpecs.length;i++) {
  const spec=previewSpecs[i];
  const png=await workbook.render({sheetName:spec.name,range:spec.range,scale:1,format:'png'});
  const target=path.join(qa,`preview_${String(i).padStart(2,'0')}.png`);
  await fs.writeFile(target,new Uint8Array(await png.arrayBuffer()));
  previews.push({sheet:spec.name,path:path.basename(target),range:spec.range});
}
const target=path.join(out,'ESM2.xlsx');
const exported=await SpreadsheetFile.exportXlsx(workbook);await exported.save(target);
for(const file of files){const bytes=await fs.readFile(path.join(root,'outputs',file.relative));if(sha(bytes)!==file.sha256)throw new Error('Source changed '+file.relative);}
await fs.writeFile(path.join(qa,'manifest.json'),JSON.stringify({sourceCount:files.length,extendedTsvCount:actual.length,worksheets:['Contents',...files.map(x=>x.sheet)],sources:files.map(({rawRows,...f})=>f),previews},null,2));
const python=process.env.CODEX_BUNDLED_PYTHON || path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe');
const checked=spawnSync(python,['-X','utf8',path.join(here,'finalize_esm2.py'),root],{encoding:'utf8'});
if(checked.status!==0)throw new Error(checked.stdout+'\n'+checked.stderr);
console.log(checked.stdout);
await fs.mkdir(path.join(root,'outputs/manuscript_sources'),{recursive:true});
const dest=path.join(root,'outputs/manuscript_sources/build_esm2.mjs');if(path.resolve(dest)!==path.resolve(fileURLToPath(import.meta.url)))await fs.copyFile(fileURLToPath(import.meta.url),dest);
const finalizeDest=path.join(root,'outputs/manuscript_sources/finalize_esm2.py');if(path.resolve(finalizeDest)!==path.resolve(path.join(here,'finalize_esm2.py')))await fs.copyFile(path.join(here,'finalize_esm2.py'),finalizeDest);
const inspectFile=target+'.inspect.ndjson';try{await fs.rename(inspectFile,path.join(qa,'export_inspect.ndjson'));}catch(error){if(error.code!=='ENOENT')throw error;}
console.log(JSON.stringify({output:target,sheets:files.length+1,extendedTsv:actual.length,sourceFiles:files.length,previewCount:previews.length,sourceCellsPreserved:true}));
