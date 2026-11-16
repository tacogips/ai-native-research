"""Apps Script用の架空資料を入力対象外に書き出す。実環境のIDは含めない。"""
import base64
import json
from pathlib import Path
from generate import dump


def write(dataset):
    from google_drive import build_plan
    rows=json.loads((dataset/'ground_truth/files.json').read_text())
    by_path={r['path']:r for r in rows}
    fixtures=[]
    for item in build_plan(dataset)['native_sheets']:
        r=by_path[item['source']]
        png=next(p for p in rows if p['source_id']==r['source_id'] and p['format']=='PNG' and p['path'].startswith('files/'))
        fixtures.append({'source_id':r['source_id'],'positive':r['positive'],'entities':r['entities'],'text':r['text'],
                         'xlsx_base64':base64.b64encode((dataset/'drive_upload'/r['path']).read_bytes()).decode(),
                         'png_base64':base64.b64encode((dataset/'drive_upload'/png['path']).read_bytes()).decode()})
    out=dataset/'automation';out.mkdir(exist_ok=True)
    dump(out/'google_sheets_config.json',{'outputParentId':'REPLACE_WITH_TEST_PARENT_ID','reportFolderId':'REPLACE_WITH_SEPARATE_REPORT_FOLDER_ID','fixtures':fixtures})
    (out/'google_sheets.gs').write_bytes(Path(__file__).with_name('google_sheets.gs').read_bytes())
    (out/'appsscript.json').write_bytes(Path(__file__).with_name('appsscript.json').read_bytes())
