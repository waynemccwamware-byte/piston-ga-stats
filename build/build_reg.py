import csv,collections,os,sys,json,re
sys.path.insert(0,os.path.expanduser('~/scripts'))
from families import family
R=os.path.expanduser('~/data/reg/')
def rd(f):
    with open(R+f,encoding='utf-8-sig',errors='replace') as fh:
        rdr=csv.reader(fh); h=[x.strip() for x in next(rdr)]
        for row in rdr: yield {h[i]:row[i].strip() for i in range(min(len(h),len(row)))}
ref={}
for r in rd('ACFTREF.txt'):
    if r['TYPE-ACFT'] in ('4','5') and r['TYPE-ENG'] in ('1','7','8','11') and r['BUILD-CERT-IND']=='0':
        b,f=family(r['MFR'],r['MODEL'])
        if b: ref[r['CODE']]=(b,f,r['MFR'],r['MODEL'],r['TYPE-ACFT'])
def sn(s): return re.sub(r'[^0-9A-Z]','',s.upper()).lstrip('0')
def d8(s): return s if re.fullmatch(r'\d{8}',s or '') else ''
air={}  # (code-family, serial) -> dict
byN=collections.defaultdict(list)
unf=collections.Counter()
for f,k in (('MASTER.txt','m'),('DEREG.txt','d')):
    for r in rd(f):
        code=r['MFR MDL CODE'] if k=='m' else r['MFR-MDL-CODE']
        a=ref.get(code)
        if not a: continue
        b,fam,mfr,model,ta=a
        if not fam: unf[(b,model)]+=1; continue
        ser=sn(r['SERIAL NUMBER'] if k=='m' else r['SERIAL-NUMBER'])
        aw=d8(r['AIR WORTH DATE'] if k=='m' else r['AIR-WORTH-DATE'])
        ci=d8(r['CERT ISSUE DATE'] if k=='m' else r['CERT-ISSUE-DATE'])
        yr=r['YEAR MFR'] if k=='m' else r['YEAR-MFR']
        cancel='' if k=='m' else d8(r['CANCEL-DATE'])
        key=(fam,ser)
        x=air.setdefault(key,{'fam':fam,'brand':b,'model':model,'aw':'','yr':'','first':'','last':'','active':False})
        for dt in (aw,ci):
            if dt and (not x['first'] or dt<x['first']): x['first']=dt
        if aw and (not x['aw'] or aw<x['aw']): x['aw']=aw
        if yr.isdigit(): x['yr']=yr
        if k=='m': x['active']=True
        elif cancel and cancel>x['last']: x['last']=cancel
        byN[r['N-NUMBER'].upper()].append((ser,fam,b,model,ci,cancel,k,yr if yr.isdigit() else ''))  # yr added for v0.2 columns
print('airframes',len(air))
print('unmapped models (top):',unf.most_common(40))
c=collections.Counter(x['fam'] for x in air.values()); print(c.most_common())
json.dump({f'{k[0]}|{k[1]}':v for k,v in air.items()},open(os.path.expanduser('~/data/airframes.json'),'w'))
json.dump(byN,open(os.path.expanduser('~/data/byN.json'),'w'))
