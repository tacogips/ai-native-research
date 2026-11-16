// XLSBは実際のBIFF12形式で作成する。拡張子変更による代用は禁止。
const path = require('node:path');
const XLSX = require(process.env.PII_XLSX_MODULE ? path.resolve(process.env.PII_XLSX_MODULE) : 'xlsx');
const [source, destination, format] = process.argv.slice(2);
if (!source || !destination || !['xlsb', 'xlsm', 'read'].includes(format)) throw Error('source destination xlsb|xlsm');
const book = XLSX.readFile(source);
if (format === 'read') {
  process.stdout.write(JSON.stringify(book.SheetNames.map(name => XLSX.utils.sheet_to_json(book.Sheets[name], {header:1, defval:''}))));
} else {
  XLSX.writeFile(book, destination, {bookType:format, compression:true});
}
