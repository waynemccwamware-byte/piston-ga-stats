# One-off probe (03-Nov-2026): what the FAA registry and NTSB files say about the turboprop types
# before they are added (PC-12, TBM, Epic E1000, PA-46 turboprops and JetPROP conversions). Writes text reports to explore-out/.
import csv,collections,os,re,sys
csv.field_size_limit(10**9)
H=os.path.expanduser('~/data/'); O=sys.argv[1]; os.makedirs(O,exist_ok=True)
def rd(f,enc='utf-8-sig'):
    with open(f,encoding=enc,errors='replace') as fh:
        r=csv.reader(fh); h=[x.strip() for x in next(r)]
        for row in r: yield {h[i]:row[i].strip() for i in range(min(len(h),len(row)))}
def hdr(f):
    with open(f,encoding='utf-8-sig',errors='replace') as fh: return next(csv.reader(fh))
WANT=re.compile(r'PILATUS|SOCATA|DAHER|EADS|PIPER|TBM|JETPROP|ROCKET|EPIC',re.I)
out=open(O+'/registry.txt','w')
for f in ('MASTER.txt','DEREG.txt','ACFTREF.txt'): print(f,'HEADER',hdr(H+'reg/'+f),file=out)
ref={}
print('\n== ACFTREF rows of interest (CODE|MFR|MODEL|TYPE-ACFT|TYPE-ENG|AC-CAT|BUILD-CERT|NO-ENG)',file=out)
for r in rd(H+'reg/ACFTREF.txt'):
    if WANT.search(r['MFR']) and (not r['MFR'].upper().startswith('PIPER') or re.search(r'46|TP|M[56]00|MERIDIAN',r['MODEL'],re.I)):
        ref[r['CODE']]=r
        print(r['CODE'],r['MFR'],r['MODEL'],r['TYPE-ACFT'],r['TYPE-ENG'],r.get('AC-CAT'),r.get('BUILD-CERT-IND'),r.get('NO-ENG'),sep=' | ',file=out)
eng={}
for r in rd(H+'reg/ENGINE.txt') if os.path.exists(H+'reg/ENGINE.txt') else []:
    eng[r['CODE']]=(r.get('MFR',''),r.get('MODEL',''),r.get('TYPE',''))
print('\n== ENGINE.txt loaded:',len(eng),file=out)
for f,k in (('MASTER.txt','m'),('DEREG.txt','d')):
    c=collections.Counter()
    for r in rd(H+'reg/'+f):
        code=r.get('MFR MDL CODE') or r.get('MFR-MDL-CODE')
        a=ref.get(code)
        if not a: continue
        te=r.get('TYPE ENGINE') or r.get('TYPE-ENGINE') or '?'
        ec=r.get('ENG MFR MDL') or r.get('ENG-MFR-MDL') or ''
        e=eng.get(ec,('','',''))
        c[(a['MFR'],a['MODEL'],a['TYPE-ENG'],te,e[0]+' '+e[1])]+=1
    print(f'\n== {f}: ACFTREF model x ACFTREF eng type x registration TYPE ENGINE x engine (count)',file=out)
    for k2,v in sorted(c.items()): print(v,*k2,sep=' | ',file=out)
out.close()
out=open(O+'/ntsb.txt','w')
for db in ('ntsb','pre'):
    P=H+db+'/csv/'
    en=collections.defaultdict(set)
    allet=collections.Counter()
    for e in csv.DictReader(open(P+'engines.csv',encoding='latin-1')):
        en[(e['ev_id'],e['Aircraft_Key'])].add(e['eng_type'].strip()); allet[e['eng_type'].strip()]+=1
    print(f'\n== {db}: all eng_type values',allet.most_common(),file=out)
    fp=collections.Counter(); c=collections.Counter()
    for a in csv.DictReader(open(P+'aircraft.csv',encoding='latin-1')):
        fp[a['far_part'].strip()]+=1
        mk=a['acft_make'].upper(); md=a['acft_model'].upper()
        if re.search(r'PILATUS|SOCATA|DAHER|EADS|TBM|EPIC|E1000',mk+' '+md) or (mk.startswith('PIPER') and re.search(r'46',md)):
            et=','.join(sorted(en.get((a['ev_id'],a['Aircraft_Key']),set())))
            c[(mk,md,et,a['far_part'].strip(),a['acft_category'].strip())]+=1
    print(f'== {db}: far_part values',fp.most_common(),file=out)
    print(f'== {db}: make | model | eng_type | far_part | category (count)',file=out)
    for k2,v in sorted(c.items()): print(v,*k2,sep=' | ',file=out)
out.close()
print('done')
