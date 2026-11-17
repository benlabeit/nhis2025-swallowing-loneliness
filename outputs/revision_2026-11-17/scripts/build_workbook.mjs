import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const base='outputs/revision_2026-11-17';
const qa='work/revision_2026-11-17';
const sheets=JSON.parse(await fs.readFile(`${qa}/workbook_inputs.json`,'utf8'));
const wb=Workbook.create();
await fs.mkdir(`${qa}/workbook_previews`,{recursive:true});
for (const entry of sheets) {
 const sh=wb.worksheets.add(entry.name);
 const rows=entry.values.length,cols=entry.values[0].length;
 sh.showGridLines=false;
 const all=sh.getRangeByIndexes(0,0,rows,cols);
 all.values=entry.values;
 all.format.font={name:'Arial',size:10,color:'#222222'};
 all.format.verticalAlignment='center';
 all.format.rowHeight=22;
 const head=sh.getRangeByIndexes(0,0,1,cols);
 head.format.fill='#33485C';head.format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};
 head.format.wrapText=true;head.format.rowHeight=42;
 head.format.horizontalAlignment='center';
 for(let c=0;c<cols;c++) {
  const col=sh.getRangeByIndexes(0,c,rows,1);
  const label=entry.values[0][c];
  const isNum=entry.values.slice(1).every(r=>r[c]===null||typeof r[c]==='number');
  col.format.columnWidth=isNum?17:(c===0?44:28);
  if(rows>1) {
   const body=sh.getRangeByIndexes(1,c,rows-1,1);
   body.format.horizontalAlignment=isNum?'right':'left';
   if(isNum) body.setNumberFormat(/^(n|count|events|Freq|.*_n|n_.*|parameters|group_n|missing_n)$/.test(label)?'#,##0':'0.0000');
  }
 }
 if(entry.name==='Definitions and sources') {
  sh.getRange(`B1:B${rows}`).format.columnWidth=115;
  sh.getRange(`B2:B${rows}`).format.wrapText=true;
  sh.getRange(`A2:B${rows}`).format.rowHeight=48;
 } else {
  sh.getRangeByIndexes(1,0,rows-1,Math.min(cols,3)).format.wrapText=true;
  sh.getRangeByIndexes(1,0,rows-1,cols).format.rowHeight=34;
 }
 sh.freezePanes.freezeRows(1);
}
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Models!A1:H6',include:'values,formulas',tableMaxRows:6,tableMaxCols:8,maxChars:2000})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1000})).ndjson);
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(`${base}/NHIS2025_Supplement_S2.xlsx`);
for(let i=0;i<sheets.length;i++) {
 const ent=sheets[i];const cols=Math.min(ent.values[0].length,8),rows=Math.min(ent.values.length,12);
 const endCol=String.fromCharCode(64+cols);
 const image=await wb.render({sheetName:ent.name,range:`A1:${endCol}${rows}`,scale:1.5,format:'png'});
 await fs.writeFile(`${qa}/workbook_previews/${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await image.arrayBuffer()));
}
console.log(`Exported ${sheets.length} sheets and rendered each sheet's opening range.`);
