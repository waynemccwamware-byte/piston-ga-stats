# Sanity check before the monthly job commits new data. Exits non-zero (job fails, nothing is published)
# if the rebuilt data looks wrong compared with what is live in the repo.
# Usage: python3 check_data.py <old accidents.json> <new accidents.json>
import json,sys
old=json.load(open(sys.argv[1])); new=json.load(open(sys.argv[2])); om,nm=old['meta'],new['meta']
problems=[]
# columns and families may be added (never removed or reordered): 03-Nov-2026 turboprops + 'part' column
if nm['cols'][:len(om['cols'])]!=om['cols']: problems.append(f"columns changed: {nm['cols']}")
lost={tuple(f) for f in om['fams']}-{tuple(f) for f in nm['fams']}
if lost: problems.append(f'model families dropped: {sorted(lost)}')
if len(new['rows'])<0.99*len(old['rows']): problems.append(f"accidents dropped from {len(old['rows'])} to {len(new['rows'])}")
if nm['ntsbAsOf']<om['ntsbAsOf']: problems.append(f"NTSB date went backwards: {om['ntsbAsOf']} -> {nm['ntsbAsOf']}")
if nm['regAsOf']<om['regAsOf']: problems.append(f"registry date went backwards: {om['regAsOf']} -> {nm['regAsOf']}")
if 'newreg' not in nm: problems.append('newreg missing')
blank=sum(1 for r in new['rows'] if len(r)!=len(nm['cols']))
if blank: problems.append(f'{blank} rows have the wrong number of columns')
# compare the same families' fleets (new families are not in the old file)
oi={tuple(f):i for i,f in enumerate(om['fams'])}; ni={tuple(f):i for i,f in enumerate(nm['fams'])}
ol=sum(om['fleet'][oi[f]][-1] for f in oi if f in ni); nl=sum(nm['fleet'][ni[f]][-1] for f in oi if f in ni)
if nl<0.95*ol and len(nm['fleet'][0])==len(om['fleet'][0]): problems.append(f'registered fleet fell from {ol} to {nl}')
print(f"old: {len(old['rows'])} accidents, NTSB {om['ntsbAsOf']}, registry {om['regAsOf']}")
print(f"new: {len(new['rows'])} accidents, NTSB {nm['ntsbAsOf']}, registry {nm['regAsOf']}")
if problems:
    print('REFUSING TO PUBLISH:'); [print(' -',p) for p in problems]; sys.exit(1)
print('checks passed')
