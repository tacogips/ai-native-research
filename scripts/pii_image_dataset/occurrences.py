"""対象の値と、ページ・フレーム上の各出現を区別する。"""
import hashlib
import fitz


def text_locations(page,value):
    chars=[]
    for block in page.get_text('rawdict')['blocks']:
        for line in block.get('lines',[]):
            for span in line.get('spans',[]):
                for char in span.get('chars',[]):
                    if not char['c'].isspace():chars.append(char)
    text=''.join(c['c'] for c in chars);query=''.join(value.split())
    result=[];start=0
    while query:
        index=text.find(query,start)
        if index<0:break
        matches=chars[index:index+len(query)]
        box=[min(c['bbox'][0] for c in matches),min(c['bbox'][1] for c in matches),max(c['bbox'][2] for c in matches),max(c['bbox'][3] for c in matches)]
        result.append(box);start=index+len(query)
    return result


def annotate(path,row,fmt,condition):
    entities=[]
    pdf=fitz.open(path) if fmt in ['PDF','PDF-text','PDF-image','PDF-protected'] else None
    if pdf and pdf.needs_pass:pdf.authenticate('DlpTest-2026')
    for source in row['entities']:
        base={k:v for k,v in source.items() if k not in ['bbox','location','target_location','occurrence_id','value_id']}
        value_key=source.get('person_id','')+'|'+source['type']+'|'+source.get('canonical_value',source['value'])
        base['value_id']=hashlib.sha256(value_key.encode()).hexdigest()[:20]
        if 'target_location' in source:
            hint=dict(source['target_location'])
            if pdf and hint.get('scope')=='文字':
                locations=[dict(hint,bbox=box,unit='PDF point') for box in text_locations(pdf[hint['page']],source['value'])]
                if not locations:raise ValueError('指定ページに対象がありません')
            else:locations=[hint]
        elif fmt=='PDF-image':locations=[{'scope':'画像','page':0,'bbox':[v/2 for v in source['bbox']],'unit':'PDF point'}]
        elif pdf and condition not in ['annotation','attachment','form']:
            locations=[{'scope':'文字','page':number,'bbox':box,'unit':'PDF point'} for number,page in enumerate(pdf) for box in text_locations(page,source['value'])]
            if not locations:raise ValueError('PDF上で対象が見つかりません: '+source['value'])
        elif pdf and condition=='form':locations=[{'scope':'フォーム','page':0,'field_name':'Email'}]
        elif pdf and condition=='annotation':locations=[{'scope':'注釈','page':0,'annotation_index':0}]
        elif pdf and condition=='attachment':locations=[{'scope':'添付','member':'document.txt'}]
        else:
            locations=[{'scope':condition}]
            if fmt in ['TXT','Markdown'] and condition not in ['ファイル名','ディレクトリ名']:
                start=row['text'].find(source['value'])
                locations[0].update({'canonical_text_start':start,'canonical_text_end':start+len(source['value']),'unit':'Unicode code point'})
        for location in locations:
            entities.append(dict(base,location=location,occurrence_id=f'occurrence-{len(entities):04d}'))
    if pdf:pdf.close()
    return entities


def validate(path,row):
    fmt=row['format'];entities=row['entities']
    if fmt not in ['PDF','PDF-text','PDF-image','PDF-protected','TIFF']:return
    if fmt=='TIFF':
        from PIL import Image
        from collections import Counter
        with Image.open(path) as image:
            if row.get('condition')=='複数ページ' and image.n_frames!=2:raise ValueError('TIFFフレーム数が違います')
            for e in entities:
                if 'frame' in e['location'] and e['location']['frame']>=getattr(image,'n_frames',1):raise ValueError('TIFFの出現先フレームがありません')
            if row.get('condition')=='複数ページ':
                counts=[Counter((e['type'],e['value']) for e in entities if e['location'].get('frame')==frame) for frame in range(image.n_frames)]
                if any(count!=counts[0] for count in counts):raise ValueError('TIFFのフレーム別対象集合が違います')
        return
    pdf=fitz.open(path)
    if pdf.needs_pass:pdf.authenticate('DlpTest-2026')
    if row.get('condition') in ['multipage','mixed','last-page'] and pdf.page_count!=3:raise ValueError('PDFページ数が違います')
    from collections import Counter
    expected=Counter()
    for e in entities:
        location=e['location']
        if 'page' in location and location['page']>=pdf.page_count:raise ValueError('出現先ページがありません')
        if location.get('scope')=='文字':expected[(location['page'],e['value'])]+=1
        elif location.get('scope')=='画像' and not pdf[location['page']].get_images():raise ValueError('対象ページに画像がありません')
    actual=Counter()
    for value in {value for _,value in expected}:
        for number,page in enumerate(pdf):
            count=len(text_locations(page,value))
            if count:actual[(number,value)]=count
    if actual!=expected:raise ValueError('PDFの対象出現数が違います: '+row['path'])
    pdf.close()
