/**
 * Google Sheetsの格納箇所別の資料を作成する。
 * Advanced Drive service v3を有効にし、生成されたconfig.jsonを読み込んで呼び出す。
 * 実データ・認証情報をコードへ埋め込まない。PIIはローカル生成した架空例だけ。
 */
function buildPiiSheets(config) {
  const lock=LockService.getScriptLock();
  if (!lock.tryLock(1000)) throw new Error('同じスクリプトで別の作成処理が実行中です');
  try {return buildPiiSheetsBatch(config);} finally {lock.releaseLock();}
}

function buildPiiSheetsBatch(config) {
  if (!config || !config.outputParentId || !config.reportFolderId || !config.fixtures) {
    throw new Error('outputParentId・reportFolderId・fixturesが必要です');
  }
  if (config.outputParentId === config.reportFolderId) throw new Error('正解の保存先は入力と分離してください');
  const started=Date.now(),requestedBudget=config.maxRuntimeMs===undefined ? 240000 : config.maxRuntimeMs;
  const maxCases=config.maxCasesPerRun===undefined ? 1 : config.maxCasesPerRun;
  if (!Number.isInteger(maxCases) || maxCases<1 || maxCases>28 || !Number.isFinite(requestedBudget) || requestedBudget<1) throw new Error('実行件数または時間の指定が不正です');
  const budget=Math.min(requestedBudget,240000);
  const retryFailures=config.retryFailedExports!==false;
  const parent = DriveApp.getFolderById(config.outputParentId);
  const reportFolder = DriveApp.getFolderById(config.reportFolderId);
  const modes = ['body', 'hidden', 'note', 'comment', 'formula', 'image', 'protected'];
  const signature=Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,
    JSON.stringify(config.fixtures)).map(n=>('0'+(n&255).toString(16)).slice(-2)).join('');
  let report,output,reportFile;
  if (config.resumeReportId) {
    reportFile=DriveApp.getFileById(config.resumeReportId);
    report=JSON.parse(reportFile.getBlob().getDataAsString());
    report.reportFileId=config.resumeReportId;
    if (report.fixtureSignature!==signature || report.outputParentId!==config.outputParentId || report.reportFolderId!==config.reportFolderId)
      throw new Error('再開対象の設定・元資料が一致しません');
    output=DriveApp.getFolderById(report.inputFolderId);
  } else {
    output=parent.createFolder('PII-DLP検知試験-LIGHT-Sheets');
    report={schema:2,inputFolderId:output.getId(),outputParentId:config.outputParentId,
      reportFolderId:config.reportFolderId,fixtureSignature:signature,cases:[],status:'作成中'};
    reportFile=reportFolder.createFile('sheets-progress-'+output.getId()+'.json',JSON.stringify(report),MimeType.PLAIN_TEXT);
    report.reportFileId=reportFile.getId();
  }
  const checkpoint=()=>{
    const exports=report.cases.flatMap(r=>r.exports);
    report.summary={planned_native:config.fixtures.length*modes.length,
      native_prepared:report.cases.filter(r=>r.prepared).length,
      export_created_unverified:exports.filter(e=>e.status==='出力済み・正解の再確認待ち').length,
      export_failed:exports.filter(e=>e.status==='出力失敗').length,
      export_not_attempted:config.fixtures.length*modes.length*6-exports.length};
    reportFile.setContent(JSON.stringify(report,null,2));
  };
  let processed=0;
  const pause=()=>{report.status='続きあり';checkpoint();return report;};
  // 初期報告はcreateFile時点で有効な内容を持つため、更新前でも参照を保存できる。
  if (config.stateKey) PropertiesService.getScriptProperties().setProperty(config.stateKey,report.reportFileId);
  checkpoint();
  for (const fixture of config.fixtures) {
    for (let index=0; index<modes.length; index++) {
      const mode = modes[index];
      let record=report.cases.find(r=>r.source_id===fixture.source_id && r.mode===mode);
      if (record && record.status==='作成済み' && !(retryFailures && record.exports.some(e=>e.status==='出力失敗'))) continue;
      if (processed>=maxCases || Date.now()-started>=budget) return pause();
      // 新規作成は検証済みXLSXのネイティブ変換を使う。
      const blob = Utilities.newBlob(Utilities.base64Decode(fixture.xlsx_base64),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'source.xlsx');
      const name=fixture.source_id+'-variant-'+index;
      const found=Drive.Files.list({q:"'"+output.getId()+"' in parents and name = '"+name+"' and trashed = false",fields:'files(id)',pageSize:100}).files || [];
      if (found.length>1) throw new Error('同名資料が重複しています。未完了として確認してください');
      if (record && (!found.length || found[0].id!==record.fileId)) throw new Error('再開対象の資料が入力フォルダーの記録と一致しません');
      const created=record ? {id:record.fileId} : found[0] || Drive.Files.create({name:name,
        mimeType:'application/vnd.google-apps.spreadsheet', parents:[output.getId()]}, blob, {fields:'id'});
      const book = SpreadsheetApp.openById(created.id);
      const sheet = book.getSheets()[0];
      if (!record) {
        record = {source_id:fixture.source_id, fileId:created.id, mode:mode,
        positive:fixture.positive, entities:fixture.entities, expectedSurfaces:[], exports:[]};
        report.cases.push(record);
      }
      checkpoint();
      if (!record.prepared) {
      if (mode === 'hidden') {
        if (book.getSheets().length===1) book.insertSheet('案内').getRange('A1').setValue('補足資料を確認してください。');
        sheet.hideSheet(); record.expectedSurfaces=['非表示シート'];
      } else if (mode === 'note') {
        sheet.clear(); sheet.getRange('A1').setValue('補足資料を確認してください。');
        sheet.getRange('B2').setNote(fixture.text); record.expectedSurfaces=['セルのメモ'];
      } else if (mode === 'comment') {
        sheet.clear(); sheet.getRange('A1').setValue('補足資料を確認してください。');
        const existing=Drive.Comments.list(created.id,{fields:'comments(content)'}).comments || [];
        if (!existing.some(c=>c.content===fixture.text)) Drive.Comments.create({content:fixture.text}, created.id, {fields:'id'});
        record.expectedSurfaces=['Driveファイルのコメント'];
      } else if (mode === 'formula') {
        sheet.clear();
        fixture.text.split('\n').forEach((line,n) => sheet.getRange(n+1,1).setFormula('="'+line.replace(/"/g,'""')+'"'));
        record.expectedSurfaces=['数式','計算結果'];
      } else if (mode === 'image') {
        sheet.clear();
        const image = Utilities.newBlob(Utilities.base64Decode(fixture.png_base64),'image/png','document.png');
        if (!sheet.getImages().length) sheet.insertImage(image,1,1); record.expectedSurfaces=['シート内の画像'];
      } else if (mode === 'protected') {
        const protection = sheet.getProtections(SpreadsheetApp.ProtectionType.SHEET)[0] || sheet.protect();
        protection.setDescription('試験用の編集保護');
        protection.setWarningOnly(false);
        const owner = Session.getEffectiveUser();
        protection.addEditor(owner);
        const others = protection.getEditors().filter(user => user.getEmail() !== owner.getEmail());
        if (others.length) protection.removeEditors(others);
        if (protection.canDomainEdit()) protection.setDomainEdit(false);
        record.expectedSurfaces=['編集保護されたセル'];
      } else record.expectedSurfaces=['セルの値'];
      SpreadsheetApp.flush();
      record.sheetCount = book.getSheets().length;
      record.cellValues = sheet.getDataRange().getDisplayValues();
      record.formulas = sheet.getDataRange().getFormulas();
      record.notes = sheet.getDataRange().getNotes();
      record.imageCount = sheet.getImages().length;
      record.hidden = sheet.isSheetHidden();
      record.protected = sheet.getProtections(SpreadsheetApp.ProtectionType.SHEET).length > 0;
      // 内容は実際に読み戻す。画像内の文字とコメントは別の確認経路を使う。
      let readback = JSON.stringify([record.cellValues,record.formulas,record.notes]);
      if (mode === 'comment') {
        record.comments = Drive.Comments.list(created.id,{fields:'comments(content)'}).comments || [];
        readback += JSON.stringify(record.comments);
      }
      if (mode === 'image') {
        if (record.imageCount !== 1) throw new Error('画像を挿入できませんでした');
        record.contentVerification='画像を1件挿入。画像中の文字の検証はローカルの元PNGと別途照合';
      } else {
        const flatten=rows=>rows.map(row=>row.join('\n')).join('\n').replace(/\s/g,'');
        const actual=mode==='note' ? flatten(record.notes) : mode==='comment' ? record.comments.map(c=>c.content).join('\n').replace(/\s/g,'') : flatten(record.cellValues);
        if (actual!==fixture.text.replace(/\s/g,'')) throw new Error('元原稿と実際の格納面の全文が一致しません');
        for (const entity of fixture.entities) {
          if (!readback.replace(/\s/g,'').includes(entity.value.replace(/\s/g,''))) throw new Error('値の欠落: '+fixture.source_id+' '+mode);
        }
        record.contentVerification='対象値を読み戻して一致';
      }
      record.prepared=true;checkpoint();
      }
      const formats = [
        ['xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        ['ods','application/vnd.oasis.opendocument.spreadsheet'], ['pdf','application/pdf'],
        ['csv','text/csv'], ['tsv','text/tab-separated-values'], ['zip','application/zip']
      ];
      const exportsFolder=record.exportsFolderId ? DriveApp.getFolderById(record.exportsFolderId) : reportFolder.createFolder(fixture.source_id+'-exports-'+index);
      record.exportsFolderId=exportsFolder.getId();checkpoint();
      for (const format of formats) {
        const prior=record.exports.find(r=>r.format===format[0]);
        if (prior && !(retryFailures && prior.status==='出力失敗')) continue;
        if (Date.now()-started>=budget) return pause();
        if (prior) record.exports=record.exports.filter(r=>r!==prior);
        const saved=Drive.Files.list({q:"'"+exportsFolder.getId()+"' in parents and name = 'document."+format[0]+"' and trashed = false",fields:'files(id)',pageSize:100}).files || [];
        if (saved.length>1) throw new Error('同名出力が重複しています。保留領域を確認してください');
        let exportedId=saved.length ? saved[0].id : null;
        if (!exportedId) {
        const url='https://www.googleapis.com/drive/v3/files/'+encodeURIComponent(created.id)+'/export?mimeType='+encodeURIComponent(format[1]);
        const response=UrlFetchApp.fetch(url,{headers:{Authorization:'Bearer '+ScriptApp.getOAuthToken()},muteHttpExceptions:true});
        if (response.getResponseCode()!==200) {
          record.exports.push({format:format[0],status:'出力失敗',httpStatus:response.getResponseCode()});
          checkpoint();
          continue;
        }
        const exported=exportsFolder.createFile(response.getBlob().setName('document.'+format[0]));
        exportedId=exported.getId();
        }
        record.exports.push({format:format[0],fileId:exportedId,status:'出力済み・正解の再確認待ち',
          note:'元資料の正解を自動転用しない。非表示・メモ・コメント・画像の保持は形式ごとに確認'});
        checkpoint();
      }
      record.exportLocation='検査範囲外の保留領域。正解確認後だけ入力へ移す';
      record.status='作成済み'; checkpoint();
      processed++;
    }
  }
  report.status=report.cases.some(c=>c.exports.some(e=>e.status==='出力失敗')) ? '出力失敗あり・再実行で再試行' : 'ネイティブ資料作成済み。出力物の正解は別途検証'; checkpoint();
  return report;
}

// Apps Scriptエディターから引数なしで実行するための入口。
// 設定ファイルは検査対象外へアップロードし、そのIDだけをここへ設定する。
function runPiiSheets() {
  const configFileId='REPLACE_WITH_PRIVATE_CONFIG_FILE_ID';
  const config=JSON.parse(DriveApp.getFileById(configFileId).getBlob().getDataAsString());
  config.stateKey='pii-sheets-report:'+configFileId;
  config.resumeReportId=PropertiesService.getScriptProperties().getProperty(config.stateKey) || config.resumeReportId;
  const result=buildPiiSheets(config);
  console.log(JSON.stringify({status:result.status,reportFileId:result.reportFileId,cases:result.cases.length}));
  return result;
}
