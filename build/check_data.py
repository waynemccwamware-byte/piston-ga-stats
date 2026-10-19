# Sanity check before the monthly job commits new data. Exits non-zero (job fails, nothing is published)
# if the rebuilt data looks wrong compared with what is live in the repo.
# Usage: python3 check_data.py <old accidents.json> <new accidents.json>
import json,sys
old=json.load(open(sys.argv[1])); new=json.load(open(sys.argv[2])); om,nm=old['meta'],new['meta']
problems=[]
if nm['cols']!=om['cols']: problems.append(f"columns changed: {nm['cols']}")
if [tuple(f) for f in nm['fams']]!=[tuple(f) for f in om['fams']]: problems.append('model family list changed')
if len(new['rows'])<0.99*len(old['rows']): problems.append(f"accidents dropped from {len(old['rows'])} to {len(new['rows'])}")
if nm['ntsbAsOf']<om['ntsbAsOf']: problems.append(f"NTSB date went backwards: {om['ntsbAsOf']} -> {nm['ntsbAsOf']}")
if nm['regAsOf']<om['regAsOf']: problems.append(f"registry date went backwards: {om['regAsOf']} -> {nm['regAsOf']}")
if 'newreg' not in nm: problems.append('newreg missing')
blank=sum(1 for r in new['rows'] if len(r)!=len(nm['cols']))
if blank: problems.append(f'{blank} rows have the wrong number of columns')
ol=sum(om['fleet'][i][-1] for i in range(len(om['fleet']))); nl=sum(nm['fleet'][i][-1] for i in range(len(nm['fleet'])))
if nl<0.95*ol and len(nm['fleet'][0])==len(om['fleet'][0]): problems.append(f'registered fleet fell from {ol} to {nl}')
print(f"old: {len(old['rows'])} accidents, NTSB {om['ntsbAsOf']}, registry {om['regAsOf']}")
print(f"new: {len(new['rows'])} accidents, NTSB {nm['ntsbAsOf']}, registry {nm['regAsOf']}")
if problems:
    print('REFUSING TO PUBLISH:'); [print(' -',p) for p in problems]; sys.exit(1)
print('checks passed')
