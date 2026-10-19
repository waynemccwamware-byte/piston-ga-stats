import csv,collections,os
P=os.path.expanduser('~/data/ntsb/csv/')
es=list(csv.DictReader(open(P+'Events_Sequence.csv',encoding='latin-1')))
def cp(strs):
    s=min(strs);l=max(strs)
    i=0
    while i<len(s) and s[i]==l[i]: i+=1
    return s[:i]
def cs(strs):
    r=[x[::-1] for x in strs]; return cp(r)[::-1]
byp=collections.defaultdict(set); bye=collections.defaultdict(set)
for x in es:
    byp[x['phase_no']].add(x['Occurrence_Description']); bye[x['eventsoe_no']].add(x['Occurrence_Description'])
ph={k:cp(v).strip(' -') if len(v)>1 else None for k,v in byp.items()}
ev={k:cs(v).strip(' -') if len(v)>1 else None for k,v in bye.items()}
# fallback: single-desc codes, subtract known phase
for x in es:
    if ev.get(x['eventsoe_no']) is None and ph.get(x['phase_no']):
        ev[x['eventsoe_no']]=x['Occurrence_Description'][len(ph[x['phase_no']]):].strip(' -')
d=[x for x in es if x['Defining_ev']=='1']
import json
json.dump({'phase':ph,'event':ev},open(os.path.expanduser('~/data/codes.json'),'w'),indent=1)
c=collections.Counter(x['eventsoe_no'] for x in d)
for k,v in c.most_common(80): print(v,k,ev.get(k))
print('---')
for k,v in collections.Counter(x['phase_no'] for x in d).most_common(): print(v,k,ph.get(k))
