"""文脈の比較用資料。正解は検知項目と関係の注釈を分ける。"""
from generate import dump


def create(root, source, register, dest):
    positives=[r for r in source if r['positive'] and any(e['type']=='氏名' for e in r['entities'])][:2]
    cases=[]
    def write(r, name, text, entities, label):
        row=dict(r,text=text,entities=entities,positive=bool(entities))
        p=dest('comparisons',name+'.txt');p.write_text(text,encoding='utf-8')
        rr=register(p,row,'TXT',label)
        return rr['path']
    for i,r in enumerate(positives):
        name=next(e for e in r['entities'] if e['type']=='氏名')
        def entity(kind,value,person=None):return {'type':kind,'value':value,'person_id':person or name['person_id']}
        filled=write(r,f'{i}-form-filled','氏名：'+name['value'],[name],'V01')
        empty=write(r,f'{i}-form-empty','氏名：＿＿＿＿',[],'V01')
        cases.append({'id':'V01','files':[filled,empty],'relation':'記入と空欄'})
        purchase=entity('購買','書籍を2冊購入')
        personal=write(r,f'{i}-receipt','氏名：'+name['value']+'\n購入記録：'+purchase['value'],[name,purchase],'V02')
        catalog=write(r,f'{i}-catalog','商品一覧\n書籍　在庫あり',[],'V02')
        cases.append({'id':'V02','files':[personal,catalog],'relation':'個人の購入と非個人の商品情報'})
        member=entity('会員ID',f'TEST-MEMBER-{i:04d}')
        table=write(r,f'{i}-member-table','会員ID：'+member['value']+'\n氏名：'+name['value'],[member,name],'V03')
        event=write(r,f'{i}-member-event','会員ID：'+member['value']+'\n宿泊施設を1泊予約',[member],'V03')
        cases.append({'id':'V03','files':[table,event],'allowed_join':[True,False],
                      'relation':'ID単独も検知対象。予約の本人への帰属は表への照合可否で別採点',
                      'join_key':member['value'],'person_id':name['person_id'],'event_fact':'宿泊施設を1泊予約'})
        medical=[]
        for key,body,subject in [('diagnosis','糖尿病の診断を受けた',name['person_id']),('denial','糖尿病とは診断されていない',name['person_id']),('relative','父親が糖尿病の診断を受けた',name['person_id']+'-father')]:
            fact=entity('要配慮:病歴',body,subject)
            medical.append(write(r,f'{i}-{key}','氏名：'+name['value']+'\n相談内容：'+body,[name,fact],'V04'))
        medical.append(write(r,f'{i}-medical-general','糖尿病は疾患の名称である。',[],'V04'))
        cases.append({'id':'V04','files':medical,'relation':'本人・否定・家族・一般解説を分ける。否定を一律陰性にしない'})
        numbers=[]
        for key,value in [('valid','4242 4242 4242 4242'),('invalid','4242 4242 4242 4243')]:
            e=entity('カード番号',value)
            numbers.append(write(r,f'{i}-card-{key}','カード番号：'+value,[e],'V05'))
        numbers.append(write(r,f'{i}-part-code','部品コード：PART-4242-4242',[],'V05'))
        cases.append({'id':'V05','files':numbers,'checksum_valid':[True,False,None],
                      'relation':'番号形式の分類と検査数字の検証を別採点'})
        plain=write(r,f'{i}-unmasked',r['text'],r['entities'],'V06')
        masked=r['text']
        for e in sorted(r['entities'],key=lambda e:-len(e['value'])):masked=masked.replace(e['value'],'＿＿＿＿')
        full=write(r,f'{i}-masked',masked,[],'V06')
        partially=r['text'].replace(name['value'],'＿＿＿＿')
        part=write(r,f'{i}-partial-mask',partially,[e for e in r['entities'] if e['type']!='氏名'],'V06')
        cases.append({'id':'V06','files':[plain,part,full],'relation':'氏名だけ削除した資料は他項目が残る'})
        paths=[]
        for label in ['資料','機微情報']:
            p=dest('comparisons/'+label,f'{i}.txt');p.write_text(r['text'],encoding='utf-8')
            paths.append(register(p,r,'TXT','V07')['path'])
        cases.append({'id':'V07','files':paths,'relation':'PIIでないパス表現で本文の正解を変えない'})
        individual=write(r,f'{i}-individual','氏名：'+name['value']+'\n購入個数：2',[name,entity('購買','2')],'V08')
        aggregate=write(r,f'{i}-aggregate','商品分類ごとの出荷集計\n工具：5000個',[],'V08')
        cases.append({'id':'V08','files':[individual,aggregate],'relation':'個人の原文と、個人への対応を持たない非個人の集計'})
    dump(root.parent/'ground_truth/comparisons.json',cases)
