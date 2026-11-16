// Apps Scriptの制御・格納先・欠落検査を、外部接続なしで確認する。
const fs=require('node:fs'), vm=require('node:vm'), path=require('node:path'), assert=require('node:assert/strict'),crypto=require('node:crypto');
const XLSX=require(process.env.PII_XLSX_MODULE ? path.resolve(process.env.PII_XLSX_MODULE) : 'xlsx');
const config=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let serial=0;const folders=new Map(),books=new Map(),comments=new Map(),files=new Map(),createdBooks=[],createdFiles=[];
const blob=bytes=>({bytes, setName(name){this.name=name;return this;}});
class Folder {
  constructor(){this.id='fake-folder-'+serial++;folders.set(this.id,this);this.files=[];this.children=[];}
  getId(){return this.id;}
  createFolder(){const folder=new Folder();this.children.push(folder);return folder;}
  createFile(...args){const f={id:'fake-file-'+serial++,content:args[1],getId(){return this.id;},setContent(v){this.content=v;},getBlob(){return {getDataAsString:()=>this.content};}};this.files.push(args);files.set(f.id,f);createdFiles.push({id:f.id,parent:this.id,name:typeof args[0]==='string'?args[0]:args[0].name});return f;}
}
class Sheet {
  constructor(data=[]){this.data=data;this.formulas=[];this.notes=[];this.images=[];this.hidden=false;this.protected=false;}
  clear(){this.data=[];this.formulas=[];this.notes=[];return this;}
  getRange(a,b){
    const i=typeof a==='number'?a-1:Number(a.slice(1))-1;
    const j=typeof a==='number'?b-1:a.charCodeAt(0)-65;
    const set=(target,value)=>{target[i]??=[];target[i][j]=value;};
    return {setValue:v=>set(this.data,v),setNote:v=>set(this.notes,v),setFormula:v=>{set(this.formulas,v);set(this.data,v.slice(2,-1).replace(/""/g,'"'));}};
  }
  getDataRange(){return {getDisplayValues:()=>this.data,getFormulas:()=>this.formulas,getNotes:()=>this.notes};}
  hideSheet(){this.hidden=true;}
  isSheetHidden(){return this.hidden;}
  insertImage(b){this.images.push(b);}
  getImages(){return this.images;}
  protect(){this.protected=true;return {setDescription(){return this;},setWarningOnly(){return this;},addEditor(){},getEditors(){return [];},canDomainEdit(){return false;}};}
  getProtections(){return this.protected?[{}]:[];}
}
const parent=new Folder(),report=new Folder();
config.outputParentId=parent.id;config.reportFolderId=report.id;
const context={
  DriveApp:{getFolderById:id=>folders.get(id),getFileById:id=>files.get(id)},
  LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock(){}})},
  Utilities:{base64Decode:s=>Buffer.from(s,'base64'),newBlob:bytes=>blob(bytes),DigestAlgorithm:{SHA_256:'sha256'},computeDigest:(a,s)=>Array.from(crypto.createHash(a).update(s).digest())},
  MimeType:{PLAIN_TEXT:'text/plain'},
  Drive:{Files:{list:({q})=>({files:createdBooks.concat(createdFiles).filter(r=>q.includes("'"+r.parent+"'") && q.includes("name = '"+r.name+"'")).map(r=>({id:r.id}))}),create:(meta,b)=>{const id='fake-book-'+serial++;createdBooks.push({id,name:meta.name,parent:meta.parents[0]});const input=XLSX.read(b.bytes);const rows=XLSX.utils.sheet_to_json(input.Sheets[input.SheetNames[0]],{header:1});books.set(id,{sheets:[new Sheet(rows)],getSheets(){return this.sheets;},insertSheet(){const sheet=new Sheet();this.sheets.push(sheet);return sheet;}});return {id};}},
         Comments:{create:(value,id)=>{comments.set(id,value.content);return {id:'fake-comment'};},list:id=>({comments:comments.has(id)?[{content:comments.get(id)}]:[]})}},
  SpreadsheetApp:{openById:id=>books.get(id),flush(){},ProtectionType:{SHEET:'sheet'}},
  Session:{getEffectiveUser:()=>({getEmail:()=> 'owner@example.test'})},
  UrlFetchApp:{fetch:()=>({getResponseCode:()=>200,getBlob:()=>blob(Buffer.from('mock export - not a validated real file'))})},
  ScriptApp:{getOAuthToken:()=> 'fake-test-token'},
};
const properties=new Map();
context.PropertiesService={getScriptProperties:()=>({setProperty:(k,v)=>properties.set(k,v),getProperty:k=>properties.get(k)})};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'google_sheets.gs'),'utf8'),context);
let result=context.buildPiiSheets(config);
assert.equal(result.cases.length,1,'既定では少数ずつ作成する');
assert.equal(result.status,'続きあり');
config.resumeReportId=result.reportFileId;
for(let n=0;n<30 && result.status==='続きあり';n++) result=context.buildPiiSheets(config);
assert.equal(result.cases.length,28);
assert.equal(books.size,28,'再開による作成済み資料の重複がない');
const completedIds=result.cases.map(c=>c.fileId);
assert.deepEqual(context.buildPiiSheets(config).cases.map(c=>c.fileId),completedIds);
assert.equal(books.size,28);
const changed=JSON.parse(JSON.stringify(config));changed.fixtures[0].text+='変更';
assert.throws(()=>context.buildPiiSheets(changed),/一致しません/);
for(const c of result.cases){
  assert.equal(c.status,'作成済み');assert.equal(c.exports.length,6);
  if(c.mode==='hidden')assert.equal(c.hidden,true);
  if(c.mode==='image')assert.equal(c.imageCount,1);
  if(c.mode==='note')assert.ok(JSON.stringify(c.notes).includes(c.positive ? c.entities[0].value : '架空資料'));
  if(c.mode==='protected')assert.equal(c.protected,true);
}
assert.ok(report.files.length>0);
assert.equal(parent.children.length,1);
assert.equal(parent.children[0].children.length,0,'未確認の出力物を入力フォルダーへ入れない');
assert.equal(report.children.length,28);
assert.equal(report.children.reduce((n,f)=>n+f.files.length,0),168);
// 出力途中の通信失敗後も、作成済み資料・完了済み出力を重複させず再開する。
const retryConfig=JSON.parse(JSON.stringify(config));delete retryConfig.resumeReportId;
const originalFetch=context.UrlFetchApp.fetch;let requests=0;
context.UrlFetchApp.fetch=()=>{if(++requests===2)throw Error('simulated network failure');return originalFetch();};
assert.throws(()=>context.buildPiiSheets(retryConfig),/simulated network/);
const pendingFile=Array.from(files.values()).find(f=>{
  try{const r=JSON.parse(f.content);return r.schema===2 && r.reportFileId!==result.reportFileId && r.cases.length===1;}catch{return false;}
});
assert.ok(pendingFile);const pending=JSON.parse(pendingFile.content);
assert.equal(pending.cases[0].exports.length,1);
assert.equal(pending.cases[0].prepared,true);
retryConfig.resumeReportId=pending.reportFileId;context.UrlFetchApp.fetch=originalFetch;
let retry=context.buildPiiSheets(retryConfig);
for(let n=0;n<30 && retry.status==='続きあり';n++) retry=context.buildPiiSheets(retryConfig);
assert.equal(retry.cases.length,28);assert.equal(books.size,56);
assert.equal(retry.cases.reduce((n,c)=>n+c.exports.length,0),168);
function finish(c,r){
  c.resumeReportId=r.reportFileId;
  r=context.buildPiiSheets(c);
  for(let n=0;n<35 && (r.status==='続きあり'||r.status==='出力失敗あり・再実行で再試行');n++) r=context.buildPiiSheets(c);
  assert.equal(r.cases.length,28);
  assert.equal(r.cases.reduce((n,x)=>n+x.exports.length,0),168);
  assert.equal(r.cases.flatMap(x=>x.exports).filter(e=>e.status==='出力失敗').length,0);
  assert.equal(r.cases.reduce((n,x)=>n+folders.get(x.exportsFolderId).files.length,0),168);
  return r;
}
// HTTPエラーは次回に再試行する。
const transient=JSON.parse(JSON.stringify(config));delete transient.resumeReportId;let first=true;
context.UrlFetchApp.fetch=()=>first?(first=false,{getResponseCode:()=>503}):originalFetch();
finish(transient,context.buildPiiSheets(transient));context.UrlFetchApp.fetch=originalFetch;
// 保存済み出力の応答喪失では既存ファイルを回収する。
const lost=JSON.parse(JSON.stringify(config));delete lost.resumeReportId;
const createFile=Folder.prototype.createFile;let loseResponse=true;
Folder.prototype.createFile=function(...args){const f=createFile.apply(this,args);if(loseResponse && args[0]?.name?.startsWith('document.')){loseResponse=false;throw Error('lost export response');}return f;};
assert.throws(()=>context.buildPiiSheets(lost),/lost export/);
Folder.prototype.createFile=createFile;
let latest=Array.from(files.values()).reverse().find(f=>{try{return JSON.parse(f.content).schema===2;}catch{return false;}});
finish(lost,Object.assign(JSON.parse(latest.content),{reportFileId:latest.id}));
// 初回の報告更新失敗でも有効な初期JSONへ自動入口から復帰する。
const initial=JSON.parse(JSON.stringify(config));delete initial.resumeReportId;
initial.stateKey='pii-sheets-report:REPLACE_WITH_PRIVATE_CONFIG_FILE_ID';let failCheckpoint=true;
files.set('REPLACE_WITH_PRIVATE_CONFIG_FILE_ID',{getBlob:()=>({getDataAsString:()=>JSON.stringify(initial)})});
Folder.prototype.createFile=function(...args){const f=createFile.apply(this,args);if(typeof args[0]==='string' && args[0].startsWith('sheets-progress-')){const set=f.setContent;f.setContent=function(v){if(failCheckpoint){failCheckpoint=false;throw Error('initial checkpoint failed');}return set.call(this,v);};}return f;};
assert.throws(()=>context.runPiiSheets(),/initial checkpoint/);
Folder.prototype.createFile=createFile;
assert.equal(properties.has(initial.stateKey),true);
latest=Array.from(files.values()).reverse().find(f=>{try{return JSON.parse(f.content).schema===2;}catch{return false;}});
assert.ok(JSON.parse(latest.content).fixtureSignature);
const parentCount=parent.children.length;
let recovered=context.runPiiSheets();
assert.equal(parent.children.length,parentCount,'初回更新失敗後の自動再実行で入力フォルダーを増やさない');
const recoveredFinal=finish(initial,recovered);
assert.equal(recoveredFinal.summary.export_created_unverified,168);
assert.equal(recoveredFinal.summary.export_failed,0);
assert.equal(recoveredFinal.summary.export_not_attempted,0);
console.log(JSON.stringify({mock_cases_verified:result.cases.length,resume_after_failure_cases:retry.cases.length,extra_fault_scenarios:3,scope:'Apps Scriptの制御・格納先・再開・値の読み戻し。Google上の実測・出力ファイルの正しさは別確認'}));
