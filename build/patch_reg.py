# Adds/refreshes meta.fleet and meta.newreg in an existing data/accidents.json without a full NTSB rebuild.
# Usage: python3 patch_reg.py <path to site data/accidents.json>   (run build_reg.py first)
import json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from regstats import fleet_and_new
p=sys.argv[1]; d=json.load(open(p)); m=d['meta']
air=json.load(open(os.path.expanduser('~/data/airframes.json')))
fam_i={(b,f):i for i,(b,f) in enumerate(m['fams'])}
Y0=m['fleetY0']; Y1=Y0+len(m['fleet'][0])-1
fl,nw=fleet_and_new(air,fam_i,Y0,Y1)
diff=sum(1 for i in range(len(fl)) for y in range(len(fl[i])) if fl[i][y]!=m['fleet'][i][y])
print('fleet cells that differ from the current file:',diff)
m['fleet']=fl; m['newreg']=nw
json.dump(d,open(p,'w'),separators=(',',':'))
print('wrote',p)
