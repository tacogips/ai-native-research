// 通常のXLSXはArtifact Toolで作成する。特殊な保存条件は専用の生成器で作る。
import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const config=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
for(const row of config.rows){
  const workbook=Workbook.create();
  const sheet=workbook.worksheets.add('内容');
  sheet.showGridLines=false;
  const values=row.text.split('\n').filter(line=>line.length).map(line=>[line]);
  const range=sheet.getRange('A1:A'+Math.max(1,values.length));
  if(values.length)range.values=values;
  range.format.font={name:config.fontFamily,size:12};
  range.format.columnWidth=100;
  range.format.rowHeight=24;
  workbook.recalculate();
  const inspection=await workbook.inspect({kind:'table',range:'内容!A1:A'+Math.max(1,values.length),include:'values',maxChars:3000});
  if(values.length && !inspection.ndjson.includes(values[0][0]))throw new Error('XLSX authoring inspection mismatch');
  const output=await SpreadsheetFile.exportXlsx(workbook);
  await output.save(row.output);
}
