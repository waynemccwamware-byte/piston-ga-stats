import csv,json,os,collections,re
csv.field_size_limit(10**9)
H=os.path.expanduser('~/data/'); O=os.path.expanduser('~/app/piston-ga-stats/data/')
rows=[r for r in json.load(open(H+'all_rows.json')) if r['t']=='ACC' and r['y']>=1982]
air=json.load(open(H+'airframes.json'))
# dictionaries
def idx(lst):
    d={};return d,lambda v:d.setdefault(v,len(d))
FAMS=sorted({(r['b'],r['f']) for r in rows}|{(v['brand'],v['fam']) for v in air.values()})
fam_i={(b,f):i for i,(b,f) in enumerate(FAMS)}
CATS={}; PH={}; PHD={}; FIND={}
def g(d,v): return d.setdefault(v,len(d))
HI={'NONE':0,'MINR':1,'SERS':2,'FATL':3}
DM={'NONE':0,'MINR':1,'SUBS':2,'DEST':3}
def pur(p):
    p=p.strip()
    if p=='PERS': return 0
    if p=='INST': return 1
    if p in ('BUS','EXEC','POSI','FERY','FLTS','AOBV','OWRK','BANT','SKYD','PUBU','ASHO','GLDT','EXLD','PUBS','PUBL','PUBF'): return 2
    return 3
# findings 2008+
fnd=collections.defaultdict(list)
for x in csv.DictReader(open(H+'ntsb/csv/Findings.csv',encoding='utf-8',errors='replace')):
    d=re.sub(r'\s*-\s*[CF]$','',x['finding_description'].strip())
    fnd[(x['ev_id'],x['Aircraft_Key'])].append((g(FIND,d), 1 if x['Cause_Factor']=='C' else 0))
rows.sort(key=lambda r:(r['d'][4:8] if len(r['d'])>=8 else '', r['id']))
def dkey(d): # mm/dd/yy -> yyyymmdd
    m=re.match(r'(\d\d)/(\d\d)/(\d\d)',d); 
    return None if not m else (m.group(3),m.group(1),m.group(2))
out=[]
for r in rows:
    m=dkey(r['d']); mo=int(m[1]) if m else 0; dy=int(m[2]) if m else 0
    f=fnd.get((r['id'],r['k']),[])
    out.append([r['y'],mo,dy,fam_i[(r['b'],r['f'])],g(CATS,r['c']),1 if r['cs']=='derived' else 0,g(PH,r['ph']),g(PHD,r['phd'] or ''),HI.get(r['hi'],-1),DM.get(r['dm'],-1),pur(r['pu']),r['fat'],r['ser'],r['n'],r['reg'],r['st'].strip(),[a*2+c for a,c in f],r.get('mdl',''),r.get('yb',''),r.get('wx',''),r.get('lt',''),r.get('city','')])
out.sort(key=lambda x:(x[0],x[1],x[2]))
# fleet per family per year
# Data dates come from the source files (set by the monthly GitHub job); defaults = last manual build.
import datetime as _dt
NTSB_AS_OF=os.environ.get('NTSB_AS_OF','2026-10-01'); REG_AS_OF=os.environ.get('REG_AS_OF','2026-10-16')
# last data year = the year of the day before the NTSB file date (a 01-Jan file covers the year before)
Y0,Y1=1982,(_dt.date.fromisoformat(NTSB_AS_OF)-_dt.timedelta(days=1)).year
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from regstats import fleet_and_new   # v0.7: fleet + new registrations per family per year
flist,nwlist=fleet_and_new(air,fam_i,Y0,Y1)
meta=dict(fams=[[b,f] for b,f in FAMS],cats=list(CATS),phases=list(PH),phd=list(PHD),findings=list(FIND),fleetY0=Y0,
  fleet=flist,newreg=nwlist,ntsbAsOf=NTSB_AS_OF,regAsOf=REG_AS_OF,
  cols=['y','m','d','fam','cat','catDerived','phase','phaseDetail','inj','dmg','purpose','fatal','serious','ntsb','reg','state','findings','model','yearBuilt','wx','light','city'])
json.dump(dict(meta=meta,rows=out),open(O+'accidents.json','w'),separators=(',',':'))
# causes by brand (probable cause text)
key2={(r['id'],r['k']):(r['b'],r['n']) for r in rows}
cz=collections.defaultdict(dict)
for db in ('ntsb','pre'):
    if not os.path.exists(H+db+'/csv/narratives.csv'): continue
    for x in csv.DictReader(open(H+db+'/csv/narratives.csv',encoding='utf-8',errors='replace')):
        k=(x['ev_id'],x['Aircraft_Key'])
        if k in key2 and (x.get('narr_cause') or '').strip():
            b,n=key2[k]; cz[b][n]=re.sub(r'\s+',' ',x['narr_cause']).strip()
for b,d in cz.items(): json.dump(d,open(O+f'causes-{b.lower()}.json','w'),separators=(',',':'))
print('rows',len(out),'fams',len(FAMS),'cats',CATS,'phases',PH,'findings',len(FIND))
