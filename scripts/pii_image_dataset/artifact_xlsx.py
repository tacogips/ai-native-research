"""利用可能なCodex Artifact Toolを通常XLSXの作成に使う。"""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import ImageFont


def author(rows,root,font_path):
    node_modules=Path(os.environ.get('PII_ARTIFACT_NODE_MODULES',str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')))
    if not (node_modules/'@oai/artifact-tool/package.json').is_file():return False
    with tempfile.TemporaryDirectory(prefix='pii-artifact-xlsx-') as folder:
        temp=Path(folder);(temp/'node_modules').symlink_to(node_modules,target_is_directory=True)
        shutil.copyfile(Path(__file__).with_name('baseline_xlsx.mjs'),temp/'baseline_xlsx.mjs')
        target=root/'office';target.mkdir(parents=True,exist_ok=True)
        generated=temp/'workbooks';generated.mkdir()
        config={'fontFamily':ImageFont.truetype(str(font_path),12).getname()[0],
                'rows':[{'text':r['text'],'output':str((generated/(r['source_id']+'.xlsx')).resolve())} for r in rows]}
        (temp/'config.json').write_text(json.dumps(config,ensure_ascii=False),encoding='utf-8')
        subprocess.run(['node',str(temp/'baseline_xlsx.mjs'),str(temp/'config.json')],check=True,timeout=300,capture_output=True,text=True)
        for row in rows:shutil.copyfile(generated/(row['source_id']+'.xlsx'),target/(row['source_id']+'.xlsx'))
    metadata=json.loads((node_modules/'@oai/artifact-tool/package.json').read_text())
    return {'engine':'Artifact Tool','version':metadata.get('version','unknown')}
