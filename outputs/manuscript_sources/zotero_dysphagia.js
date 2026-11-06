// Run in Zotero's Tools > Developer > Run JavaScript, as an async function.
// Preserves the original NLM export. Uses the official named Dysphagia CSL.
// Creates only this project's collection/items; no unrelated library records are edited.
var root = String.raw`C:\Users\benlabeit\Documents\Codex\2026-11-06\nhis-p2-analyse`;
var refs = JSON.parse(await Zotero.File.getContentsAsync(root + String.raw`\outputs\literature\verified_references.json`));
var manuscript = JSON.parse(await Zotero.File.getContentsAsync(root + String.raw`\outputs\manuscript_sources\content.json`));
var collectionName = 'NHIS 2025 P2 Swallowing and Loneliness';
var tag = 'NHIS2025_Loneliness_Project2';
var collection = Zotero.Collections.getByLibrary(Zotero.Libraries.userLibraryID).find(c => c.name === collectionName);
if (!collection) { collection = new Zotero.Collection(); collection.name = collectionName; collection.libraryID = Zotero.Libraries.userLibraryID; await collection.saveTx(); }
var search = new Zotero.Search(); search.libraryID = Zotero.Libraries.userLibraryID; search.addCondition('tag','is',tag);
var prior = await Zotero.Items.getAsync(await search.search());
var map = {};
for (var ref of refs) {
  var item = prior.find(i => i.isRegularItem() && i.getField('extra').includes('Reference key: ' + ref.id));
  if (!item) {
    var type = ref.type === 'article-journal' ? 'journalArticle' : ref.type === 'report' ? 'report' : 'webpage';
    item = new Zotero.Item(type); item.libraryID = Zotero.Libraries.userLibraryID;
    item.setField('title',ref.title); item.setField('date',String(ref.issued['date-parts'][0][0]));
    item.setField('url',ref.URL || ''); item.setField('accessDate','2026-11-06');
    item.setField('abstractNote',ref.abstract || ''); item.setField('language','en');
    item.setField('extra','Reference key: ' + ref.id + (ref.PMID ? '\nPMID: '+ref.PMID : ''));
    if (type === 'journalArticle') {
      for (var [field,value] of Object.entries({publicationTitle:ref['container-title'],journalAbbreviation:ref['container-title-short'],volume:ref.volume,issue:ref.issue,pages:ref.page,DOI:ref.DOI})) if(value) item.setField(field,String(value));
    } else if (type === 'report') { item.setField('institution',ref.publisher || ''); }
    else { item.setField('websiteTitle',ref.publisher || ''); }
    item.setCreators(ref.author.map(a => a.literal ? {name:a.literal,creatorType:'author'} : {firstName:a.given || '',lastName:a.family,creatorType:'author'}));
    item.addTag(tag); item.setCollections([collection.id]); await item.saveTx();
  }
  map[ref.id] = {id:item.id,key:item.key,uri:Zotero.URI.getItemURI(item),csl:Zotero.Utilities.Item.itemToCSLJSON(item)};
}
await Zotero.Styles.init();
// Install the official independent parent first, then the named journal alias.
for (var styleName of ['springer-vancouver-brackets', 'dysphagia']) {
  var targetID = 'http://www.zotero.org/styles/' + styleName;
  if (!Zotero.Styles.get(targetID)) {
    var styleXML = await Zotero.File.getContentsAsync(root + String.raw`\outputs\literature` + String.fromCharCode(92) + styleName + '.csl');
    await Zotero.Styles.validate(styleXML);
    await Zotero.Styles.install({string:styleXML}, 'https://www.zotero.org/styles/' + styleName, true);
  }
}
var styleID = 'http://www.zotero.org/styles/dysphagia';
var style = Zotero.Styles.get(styleID);
if (!style) throw new Error('Official Dysphagia citation style is unavailable');
var paragraphs = [];
function collect(section) { for(var p of section.paragraphs || []) paragraphs.push(p); for(var s of section.subsections || []) collect(s); }
manuscript.sections.forEach(collect);
var clusters = [];
for (var p of paragraphs) for(var match of p.matchAll(/\[\[([^\]]+)\]\]/g)) {
  var keys = match[1].split(',');
  clusters.push({citationID:'NHISP2_DYSPHAGIA_' + String(clusters.length+1).padStart(4,'0'),properties:{noteIndex:0},citationItems:keys.map(k=>({id:map[k].id,uris:[map[k].uri],itemData:map[k].csl})),keys});
}
var engine = style.getCiteProc('en-US','text');
var rendered = engine.rebuildProcessorState(clusters,'text',[]);
var bibliography = engine.makeBibliography();
var result = {zoteroVersion:Zotero.version,collection:{id:collection.id,key:collection.key,name:collection.name},styleID,styleTitle:style.title,items:map,citations:clusters,rendered,bibliography};
await Zotero.File.putContentsAsync(root + String.raw`\outputs\literature\zotero_citations_dysphagia.json`,JSON.stringify(result,null,2));
await Zotero.File.putContentsAsync(root + String.raw`\outputs\literature\Dysphagia_bibliography.txt`,Zotero.Cite.makeFormattedBibliography(engine,'text'));
return JSON.stringify({collection:collection.name,items:Object.keys(map).length,citations:clusters.length,bibliographyEntries:bibliography[1].length,style:style.title});
