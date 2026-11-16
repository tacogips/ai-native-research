"""LIGHTの比較・格納位置・境界・ディレクトリ構成を補う。"""
import json
import shutil
from pathlib import Path

import fitz
from pdf_fonts import write as pdf_text
import xlsxwriter
from PIL import Image
from generate import dump


def create(root, source, records, register, dest):
    pos=[r for r in source if r['positive'] and any(e['type']=='氏名' for e in r['entities'])][:2]
    neg=[r for r in source if not r['positive']][:2]
    scenarios=[]
    # 本文に対象がなく、名前のみに対象があるもの。
    for i,r in enumerate(pos):
        e=next(e for e in r['entities'] if e['type']=='氏名')
        single=dict(r,entities=[e],text=e['value'])
        p=dest('names',f"記録-{e['value']}-{i}.txt");p.write_text('資料を確認してください。',encoding='utf-8')
        register(p,single,'TXT','ファイル名')
        p=dest('names/'+e['value'],f'item-{i}.txt');p.write_text('資料を確認してください。',encoding='utf-8')
        register(p,single,'TXT','ディレクトリ名')
    for i,r in enumerate(neg):
        for where in ['ファイル名','ディレクトリ名']:
            p=dest('names-control'+('/一般資料' if where=='ディレクトリ名' else ''),f'一般資料-{i}.txt')
            p.write_text('資料を確認してください。',encoding='utf-8')
            register(p,dict(r,text='',entities=[]),'TXT',where)
    # 複数ページと画像・文字の混在。全ページに正解があるものと、末尾だけあるもの。
    for r in pos+neg:
        sid=r['source_id']
        for kind in ['multipage','mixed','last-page']:
            pdf=fitz.open()
            for page_no in range(3):
                page=pdf.new_page(width=700,height=500)
                if kind=='last-page' and page_no<2:
                    pdf_text(page,(30,40),'資料の案内',fontname='japan',fontsize=14)
                elif kind=='mixed' and page_no==1:
                    page.insert_image(page.rect,filename=str(root/r['path']))
                else:
                    for k,line in enumerate(r['text'].splitlines()):pdf_text(page,(30,40+k*45),line,fontname='japan',fontsize=12)
            pdf.subset_fonts();p=dest('features',sid+'.'+kind+'.pdf');pdf.save(p,deflate=True,garbage=4,no_new_id=True);pdf.close()
            if kind=='mixed':
                occurrences=[]
                for page_number in range(3):
                    for e in r['entities']:
                        location={'scope':'画像' if page_number==1 else '文字','page':page_number}
                        if page_number==1:location.update({'bbox':[v/2 for v in e['bbox']],'unit':'PDF point'})
                        occurrences.append(dict(e,target_location=location))
                register(p,dict(r,entities=occurrences),'PDF',kind)
            else:register(p,r,'PDF',kind)
        with Image.open(root/r['path']) as im:
            p=dest('features',sid+'.multipage.tiff');im.save(p,save_all=True,append_images=[im.copy()],compression='raw')
        repeated=[dict(e,target_location={'scope':'画像','frame':frame,'bbox':e['bbox'],'unit':'pixel'}) for frame in range(2) for e in r['entities']]
        register(p,dict(r,entities=repeated),'TIFF','複数ページ')
        # Excelの名前定義だけに対象を格納。
        p=dest('features',sid+'.defined-name.xlsx');w=xlsxwriter.Workbook(p);ws=w.add_worksheet('案内');ws.write('A1','資料を確認してください。')
        for k,line in enumerate(r['text'].splitlines()):w.define_name('record_'+str(k),'="'+line.replace('"','""')+'"')
        w.close();register(p,r,'XLSX','名前定義')
        # 同じ本文を異なるしきい値前後の長さで構成。実製品の制限とは別の試験設定。
        for size in [4095,4096,4097]:
            body=r['text'].encode('utf-8')
            p=dest('boundaries',f'{sid}.bytes-{size}.txt');p.write_bytes(body+b' '*(size-len(body)))
            rr=register(p,r,'TXT','容量境界')
            rr['fixture_limit']={'bytes':4096,'actual_bytes':size}
        # 無害な一般文の先頭・中央・末尾へ配置。元の値と対応を維持。
        for position in ['start','middle','end']:
            filler=('資料の取扱手順を確認します。\n'*40)
            text=r['text']+filler if position=='start' else filler+r['text']+filler if position=='middle' else filler+r['text']
            p=dest('features',sid+'.'+position+'.txt');p.write_text(text,encoding='utf-8');register(p,dict(r,text=text),'TXT',position)
    # 伏字・削除・空欄の比較。全対象を除去し、残存がない資料を陰性にする。
    for r in pos:
        masked=r['text']
        for e in sorted(r['entities'],key=lambda e:-len(e['value'])):masked=masked.replace(e['value'],'＿＿＿＿')
        p=dest('comparisons',r['source_id']+'.blank.txt');p.write_text(masked,encoding='utf-8')
        clean=dict(r,entities=[],positive=False,text=masked)
        other=register(p,clean,'TXT','全対象を空欄化')
        scenarios.append({'id':'V01-V06','original':r['path'],'variant':other['path'],'relation':'全対象を除去'})
    # ディレクトリ構成。既存4構成とは独立した明示的な14条件。
    directory_truth=[]
    def clone(folder,row,index,suffix='.txt',source_path=None):
        p=dest(folder,f'item-{index:04d}'+suffix)
        if source_path:shutil.copyfile(source_path,p)
        else:p.write_text(row['text'],encoding='utf-8')
        return register(p,row,'TXT' if not source_path else 'copy','ディレクトリ配置')
    def add_directory(key,folder,members,note=''):
        (root/folder).mkdir(parents=True,exist_ok=True)
        directory_truth.append({'id':key,'path':folder,'files':[r['path'] for r in members],
                                'positive':any(r['positive'] for r in members),'note':note})
    folder='scenarios/group-01';add_directory('D01',folder,[clone(folder,r,k) for k,r in enumerate(neg)])
    add_directory('D02','scenarios/group-02',[])
    folder='scenarios/group-03/a/b/c/d';members=[clone(folder,r,k) for k,r in enumerate(neg)];add_directory('D03','scenarios/group-03',members)
    folder='scenarios/group-04';add_directory('D04',folder,[clone(folder,r,k) for k,r in enumerate(pos)])
    folder='scenarios/group-05';add_directory('D05',folder,[clone(folder,r,k) for k,r in enumerate(pos+neg)])
    folder='scenarios/group-06';members=[clone(folder,neg[0],k) for k in range(999)];members.append(clone(folder+'/a/b',pos[0],999));add_directory('D06',folder,members,'陰性999件は同じ元文書の複製')
    folder='scenarios/group-07';members=[clone(folder+'/branch-1',pos[0],0),clone(folder+'/branch-2',neg[0],0)];add_directory('D07',folder,members)
    folder='scenarios/group-08'
    name=next(e for e in pos[0]['entities'] if e['type']=='氏名')
    member={'type':'会員ID','value':'TEST-JOIN-0001','person_id':name['person_id']}
    table_row=dict(pos[0],text='会員ID：'+member['value']+'\n氏名：'+name['value'],entities=[member,name])
    event_row=dict(pos[0],text='会員ID：'+member['value']+'\n宿泊施設を1泊予約',entities=[member])
    members=[clone(folder+'/table',table_row,0),clone(folder+'/records',event_row,0)]
    add_directory('D08',folder,members,'会員IDで人物と予約を照合。表を利用できる場合とできない場合を別試験にする')
    directory_truth[-1]['join_rule']={'key':member['value'],'person_id':name['person_id'],'fact':'宿泊施設を1泊予約','availability':[True,False]}
    folder='scenarios/group-09';members=[clone(folder,neg[0],0)];src=root/'protected'/f"{pos[0]['source_id']}.encrypted.xlsx";p=dest(folder,'item-0001.xlsx');shutil.copyfile(src,p);rr=register(p,pos[0],'XLSX-encrypted','復号鍵なし');members.append(rr);add_directory('D09',folder,members,'鍵供給なしでは部分読取')
    folder='scenarios/group-10';add_directory('D10',folder,[clone(folder+'/.hidden',pos[0],0)])
    folder='scenarios/group-11';add_directory('D11',folder,[clone(folder+'/branch-'+str(k),pos[0],k) for k in range(3)])
    folder='scenarios/group-13';members=[clone(folder+'/version-1',neg[0],0),clone(folder+'/version-2',pos[0],0),clone(folder+'/version-3',neg[0],0)];add_directory('D13',folder,members,'状態別の保存資料。実際の更新・移動は外部の試験実行器で行う')
    folder='scenarios/group-14';e=pos[0]['entities'][0];p=dest(folder,f"記録-{e['value']}.txt");p.write_text('資料の確認',encoding='utf-8');rr=register(p,dict(pos[0],entities=[e],text=e['value'],expected_body='資料の確認'),'TXT','ファイル名');add_directory('D14',folder,[rr])
    folder='scenarios/group-16';members=[clone(folder,neg[0],0)];p=dest(folder,'item-0001.zip');shutil.copyfile(root/'archives'/f"{pos[0]['source_id']}.nested.zip",p);members.append(register(p,pos[0],'ZIP','入れ子',members=['inner.zip']));add_directory('D16',folder,members)
    old=json.loads((root.parent/'ground_truth/directories.json').read_text())
    dump(root.parent/'ground_truth/directories.json',old+directory_truth)
    dump(root.parent/'ground_truth/comparisons.json',scenarios)
