"""Numbers for the video scenes, from site/data/accidents.json with GA Accident Stats' own definitions:
piston singles (not turboprop, not a listed twin), Part 91, fatal = highest injury fatal (inj 3),
last year prorated by the NTSB file's as-of date. Writes scene-data.json."""
import json, math, pathlib, datetime as dt
ROOT = pathlib.Path(__file__).resolve().parent
D = json.load(open(ROOT.parent.parent / 'site/data/accidents.json')); M, R = D['meta'], D['rows']
F, E, FL, Y0 = M['fams'], M['eng'], M['fleet'], M['fleetY0']
TW = {'Beech Baron 55/58','Beech Duchess 76','Beech Travel Air 95','Cessna 310/320','Cessna 335/340','Cessna 336/337','Cessna 401-421 twins',
      'Diamond DA42','Diamond DA62','Piper PA-23 Apache/Aztec','Piper PA-30/39 Twin Comanche','Piper PA-31 Navajo','Piper PA-34 Seneca','Piper PA-44 Seminole'}
S = [i for i, f in enumerate(F) if E[i] == 'P' and f[0] + ' ' + f[1] not in TW]
asof = dt.date.fromisoformat(M['ntsbAsOf']); LAST = asof.year
FR = ((asof - dt.timedelta(days=1)) - dt.date(LAST, 1, 1)).days / 365 + 1 / 365   # share of LAST covered
yrs = list(range(2000, LAST + 1))
fleet = {y: sum(FL[i][y - Y0] or 0 for i in S) for y in yrs}
rows = [r for r in R if r[3] in S and r[22] == 0 and 2000 <= r[0] <= LAST]
fat = {y: sum(1 for r in rows if r[0] == y and r[8] == 3) for y in yrs}
allc = {y: sum(1 for r in rows if r[0] == y) for y in yrs}
ay = {y: fleet[y] * (FR if y == LAST else 1) for y in yrs}
def avg3(cnt):
    out = {}
    for y in yrs:
        w = [z for z in (y - 1, y, y + 1) if z in ay]
        out[y] = round(1000 * sum(cnt[z] for z in w) / sum(ay[z] for z in w), 4)
    return out
# funnel (2000..LAST), as the app: exact Poisson verdicts against the pooled average
ev = {}
for r in rows:
    if r[8] == 3: ev[r[3]] = ev.get(r[3], 0) + 1
def cdf(k, l):
    s, lp = 0, -l
    for j in range(k + 1):
        if j: lp += math.log(l / j)
        s += math.exp(lp)
    return min(1, s)
ICAO = {'172':'C172','150/152':'C150','182':'C182','PA-28 Cherokee/Warrior/Archer':'P28A','PA-18 Super Cub':'PA18','180/185':'C180',
        '170':'C170','PA-22 Tri-Pacer/Colt':'PA22','J-3 Cub':'J3','120/140':'C140','PA-46 Malibu/Mirage':'PA46','Bonanza 36':'BE36',
        'PA-32 Cherokee Six/Saratoga':'PA32','SR20':'SR20','SR22':'SR22','M20K/M/R/S/TN/V':'M20T','Bonanza 35 (V-tail)':'BE35','210':'C210',
        'M20 (C/E/F/G/J)':'M20P','205/206/207':'C206','PA-24 Comanche':'PA24','DA40':'DA40','SR22T':'S22T','177/Cardinal':'C177',
        'PA-28R Arrow':'P28R','Bonanza 33':'BE33','Musketeer/Sundowner/Sierra':'BE23','PA-38 Tomahawk':'PA38','PA-12 Super Cruiser':'PA12',
        '175':'C175','195':'C195','DA20':'DV20','350/400 (Columbia)':'COL4','Skipper 77':'BE77','172RG':'C72R','172 Hawk XP':'C172',
        'M20 early (A/B)':'M20P','DA40 NG':'DA40'}
n_yrs = len(yrs) - 1 + FR
pts = []
for i in S:
    a = sum((FL[i][y - Y0] or 0) * (FR if y == LAST else 1) for y in yrs)
    if a < 1: continue
    pts.append({'i': i, 'name': F[i][0] + ' ' + F[i][1], 'icao': ICAO.get(F[i][1], F[i][1]), 'k': ev.get(i, 0), 'ay': a, 'fleet': a / n_yrs})
K = sum(p['k'] for p in pts); AY = sum(p['ay'] for p in pts); P = K / AY
for p in pts:
    l = P * p['ay']; k = p['k']
    p['v'] = 'hi' if k > 0 and 1 - cdf(k - 1, l) < 0.025 else ('lo' if cdf(k, l) < 0.025 else '')
    p['rate'] = round(1000 * k / p['ay'], 4); p['fleet'] = round(p['fleet'], 1); del p['ay']
cat = {}; ph = {}
for r in rows:
    if r[8] != 3: continue
    cat[M['cats'][r[4]]] = cat.get(M['cats'][r[4]], 0) + 1
    ph[M['phases'][r[6]]] = ph.get(M['phases'][r[6]], 0) + 1
out = {'asof': M['ntsbAsOf'], 'regAsOf': M['regAsOf'], 'lastShare': round(FR, 4), 'years': yrs,
       'fatal3': avg3(fat), 'all3': avg3(allc), 'fatal': fat, 'all': allc, 'fleet': fleet,
       'funnel': {'avg': round(1000 * P, 4), 'years': round(n_yrs, 3), 'pts': pts},
       'category': dict(sorted(cat.items(), key=lambda kv: -kv[1])), 'phase': ph, 'fatalTotal': sum(cat.values())}
json.dump(out, open(ROOT / 'scene-data.json', 'w'), indent=1)
print('fatal3', {y: out['fatal3'][y] for y in (2000, 2009, 2024, 2025, LAST)}, 'avg', out['funnel']['avg'], 'share', FR)
print('cats', list(out['category'].items())[:6], out['fatalTotal']); print('phase', ph)
