# Registered fleet and new registrations per family per year (shared by bundle.py and patch_reg.py).
# fleet[i][y]  = airframes on the registry at any time in year y (first date to last cancel, or to now if active)
# newreg[i][y] = airframes whose first US registration falls in year y: new production plus used imports.
#   first = earliest airworthiness or certificate-issue date on any record (year built if neither).
#   Returns to the registry after a gap are NOT counted: MASTER and DEREG almost never link an airframe's
#   old deregistration to its later re-registration (checked 19-Oct-2026: 819 of 288,085 airframes have >1 record).
def fleet_and_new(air, fam_i, Y0, Y1):
    n=len(fam_i)
    fl={i:[0]*(Y1-Y0+1) for i in range(n)}; nw={i:[0]*(Y1-Y0+1) for i in range(n)}
    for v in air.values():
        i=fam_i[(v['brand'],v['fam'])]
        first=v['first'] or (v['yr']+'0101' if v['yr'] else None)
        if not first: continue
        fy=int(first[:4]); ly=Y1 if v['active'] else (int(v['last'][:4]) if v['last'] else None)
        if ly is None: continue
        for y in range(max(fy,Y0),min(ly,Y1)+1): fl[i][y-Y0]+=1
        if Y0<=fy<=Y1: nw[i][fy-Y0]+=1
    return [fl[i] for i in range(n)], [nw[i] for i in range(n)]
