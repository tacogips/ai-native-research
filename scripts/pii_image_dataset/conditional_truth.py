"""別表照合の可否で変わる対象と、観測できる事実を明示する。"""
import hashlib
from generate import dump


def attach(root,records):
    import json
    by_path={r['path']:r for r in records}
    comparisons=json.loads((root.parent/'ground_truth/comparisons.json').read_text())
    directories=json.loads((root.parent/'ground_truth/directories.json').read_text())
    profiles=[]
    def link(event_path,table_path,person_id,key,fact):
        event=by_path[event_path]
        start=event['text'].find(fact)
        if start<0:raise ValueError('照合する事実が本文にありません')
        value_key=person_id+'|予約|'+fact
        conditional={'type':'予約','value':fact,'person_id':person_id,
                     'value_id':hashlib.sha256(value_key.encode()).hexdigest()[:20],
                     'occurrence_id':'conditional-occurrence-0000',
                     'location':{'scope':'本文','canonical_text_start':start,'canonical_text_end':start+len(fact)}}
        event['observable_facts']=[{'type':'予約','value':fact,'subject_member_id':key,'attribution':'未照合のとき人物は未確定'}]
        event['conditional_entities']=[{'requires_files':[table_path,event_path],'requires_authorized_join':True,'entities':[conditional]}]
        profiles.extend([
            {'profile':'照合許可','event_path':event_path,'input_files':[table_path,event_path],
             'join_authorized':True,'expected_entities':event['entities']+[conditional]},
            {'profile':'照合なし','event_path':event_path,'input_files':[event_path],
             'join_authorized':False,'expected_entities':event['entities'],
             'note':'観測可能な予約の事実と、PIIとしての帰属は別。事実の抽出を自動的に誤警告としない'},
        ])
    for case in comparisons:
        if case['id']=='V03':link(case['files'][1],case['files'][0],case['person_id'],case['join_key'],case['event_fact'])
    for case in directories:
        if case.get('id')=='D08':
            rule=case['join_rule'];link(case['files'][1],case['files'][0],rule['person_id'],rule['key'],rule['fact'])
    dump(root.parent/'ground_truth/conditional_expectations.json',profiles)
