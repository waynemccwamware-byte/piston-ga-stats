import csv,collections,os,sys,json,re
sys.path.insert(0,os.path.expanduser('~/scripts'))
from families import family
H=os.path.expanduser('~/data/')
byN=json.load(open(H+'byN.json'))
codes=json.load(open(H+'codes.json'))
def sn(s): return re.sub(r'[^0-9A-Z]','',s.upper()).lstrip('0')
def rd(p): return csv.DictReader(open(p,encoding='latin-1'))
def mdlser(m,ser):  # NTSB model + series (upper case), unless the series text is already in the model
    m=m.strip().upper(); ser=ser.strip().upper()
    return m if not ser or ser in m else (m+' '+ser)
def fixenc(t):  # files are read as latin-1; city names are really UTF-8 (Española, Keflavík)
    try: return t.encode('latin-1').decode('utf-8')
    except UnicodeError: return t
# --- category maps
NEWCAT={'240':'LOC-I','241':'LOC-I','271':'LOC-I','230':'LOC-G','120':'CFIT','341':'SCF-PP','342':'SCF-PP','340':'SCF-PP','343':'SCF-PP',
 '330':'SCF-NP','333':'SCF-NP','337':'SCF-NP','338':'SCF-NP','332':'SCF-NP','334':'SCF-NP','331':'SCF-NP','335':'SCF-NP','336':'SCF-NP',
 '192':'FUEL','191':'FUEL','190':'FUEL','193':'FUEL','300':'RE','092':'ARC','090':'ARC','094':'ARC','095':'ARC','096':'ARC','093':'ARC','091':'ARC','097':'ARC',
 '470':'CTOL','490':'CTOL','220':'LALT','250':'MAC','260':'MAC','200':'GCOL','310':'WILD','901':'BIRD','401':'UIMC','402':'UIMC','380':'USOS','370':'USOS',
 '000':'UNK','900':'OTHR','150':'F-NI','160':'F-NI','360':'TURB','361':'TURB','362':'TURB','390':'WSTRW','210':'ICE','850':'MED','500':'LOLI',
 '270':'AMAN','100':'ATM','080':'RAMP','081':'RAMP','082':'RAMP','284':'NAV','280':'NAV','281':'NAV','282':'NAV','440':'OTHR','320':'RI'}
def oldcat(code,phase):
    c=int(code) if code.isdigit() else -1; p=int(phase) if phase.isdigit() else 0
    if c==250: return 'LOC-I'
    if c==260: return 'LOC-G'
    if c in (350,351,352): return 'SCF-PP'
    if c in (353,354): return 'PWR-NM'   # power loss, non-mechanical (fuel, carb ice...)
    if c==130 or c in (131,132): return 'SCF-NP'
    if c==230: return 'CTOL' if 520<=p<530 or 570<=p<580 else 'CFIT'
    if c==220: return 'CTOL' if 520<=p<530 or 570<=p<580 else 'LALT'
    if c==240: return 'WX'
    if c==200 or 190<=c<=199 or c in (160,232,300,290): return 'ARC'
    if c==340: return 'RE'
    if c==390: return 'USOS'
    if c in (310,271,320): return 'GCOL'
    if c in (270,280): return 'MAC'
    if c in (170,171,172): return 'F-NI'
    if c in (410,330): return 'TURB'
    if c==100: return 'AMAN'
    if c==110: return 'LOC-I'
    if c==180: return 'OTHR'
    if c==400: return 'UNK'
    return 'OTHR'
def phase_new(p):
    p=int(p) if p.isdigit() else 990
    if p in (509,504): return 'Go-around'
    if p<200: return 'Standing'
    if p<300: return 'Taxi'
    if p<350: return 'Takeoff'
    if p<400: return 'Initial climb'
    if p<450: return 'Enroute'
    if p<500: return 'Maneuvering'
    if p<550: return 'Approach'
    if p<600: return 'Landing'
    if p in (600,650): return 'Emergency/uncontrolled descent'
    if p<990 and p>=700: return 'Other'
    return 'Unknown'
def phase_old(p):
    p=int(p) if p.isdigit() else 610
    if p in (565,566): return 'Go-around'
    if p<510: return 'Standing'
    if p<520: return 'Taxi'
    if p==522: return 'Initial climb'
    if p<530: return 'Takeoff'
    if p<560: return 'Enroute'
    if p<570: return 'Approach'
    if p<580: return 'Landing'
    if p<600: return 'Maneuvering'
    if p==600: return 'Other'
    return 'Unknown'
OLDPH={r['code']:r['meaning'] for r in rd(H+'pre/csv/ct_seqevt.csv')} if os.path.exists(H+'pre/csv/ct_seqevt.csv') else {}
out=[]; stat=collections.Counter()
for db in ('pre','ntsb'):
    P=H+db+'/csv/'
    if not os.path.exists(P+'events.csv'): print('skipping missing',db); continue
    ev={r['ev_id']:r for r in rd(P+'events.csv')}
    en=collections.defaultdict(set)
    for e in rd(P+'engines.csv'): en[(e['ev_id'],e['Aircraft_Key'])].add(e['eng_type'].strip())
    de={}
    if db=='ntsb':
        for x in rd(P+'Events_Sequence.csv'):
            if x['Defining_ev']=='1': de[(x['ev_id'],x['Aircraft_Key'])]=(NEWCAT.get(x['eventsoe_no'],'OTHR'),phase_new(x['phase_no']),codes['phase'].get(x['phase_no']) or '','ntsb')
    else:
        for x in rd(P+'Occurrences.csv'):
            if x['Occurrence_No']=='1': de[(x['ev_id'],x['Aircraft_Key'])]=(oldcat(x['Occurrence_Code'],x['Phase_of_Flight']),phase_old(x['Phase_of_Flight']),(OLDPH.get(x['Phase_of_Flight']) or '').title(),'derived')
    for a in rd(P+'aircraft.csv'):
        e=ev.get(a['ev_id'])
        if not e: continue
        if db=='pre' and e['ev_year']>='2008': continue
        b0,f0=family(a['acft_make'],a['acft_model'])
        N=re.sub(r'^N','',a['regis_no'].upper().strip())
        cand=byN.get(N,[]); s=sn(a['acft_serial_no'])
        hit=[c for c in cand if c[0]==s] if s else []
        if not hit and s: hit=[c for c in cand if c[0] and (c[0].endswith(s) or s.endswith(c[0]))]
        b1,f1=(hit[0][2],hit[0][1]) if hit else (None,None)
        fam=f1 or f0; br=b1 or b0
        if not fam: continue
        if not (hit or N[:1].isdigit()): stat[db+' foreign']+=1; continue
        if a['acft_category'] not in ('AIR','') or a['homebuilt']=='Y': continue
        et=en.get((a['ev_id'],a['Aircraft_Key']),set())
        if et and 'REC' not in et: continue
        if a['far_part'].strip() not in ('091','091K','') : stat[db+' non-91']+=1; continue
        cat,ph,phd,cs=de.get((a['ev_id'],a['Aircraft_Key']),('UNK','Unknown','','none'))
        stat[db+' kept']+=1; stat[db+(' reg' if hit else ' name')]+=1
        out.append(dict(id=a['ev_id'],k=a['Aircraft_Key'],n=a['ntsb_no'].strip(),reg='N'+N,d=e['ev_date'][:8],y=int(e['ev_year']),t=e['ev_type'],
            b=br,f=fam,dm=a['damage'].strip(),hi=e['ev_highest_injury'].strip(),fat=int(e['inj_tot_f'] or 0),ser=int(e['inj_tot_s'] or 0),
            pu=a['type_fly'].strip(),c=cat,cs=cs,ph=ph,phd=phd,st=e['ev_state'],src='reg' if hit else 'name',
            # v0.2 columns. model: registry model when matched, else NTSB model + series
            mdl=(hit[0][3] if hit else mdlser(a['acft_model'],a.get('acft_series') or '')),
            # year built: registry year of manufacture when matched, else the NTSB's own year
            yb=((hit[0][7] if hit and len(hit[0])>7 else '') or (a.get('acft_year') or '').strip()),
            wx=(e.get('wx_cond_basic') or '').strip(), lt=(e.get('light_cond') or '').strip(),
            city=fixenc((e.get('ev_city') or '').strip()).title()))
print(stat)
json.dump(out,open(H+'all_rows.json','w'))
c=collections.Counter((r['y']//5*5) for r in out); print(sorted(c.items()))
