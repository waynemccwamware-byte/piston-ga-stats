"""Sentence start times per VO clip: the longest pauses are taken as sentence breaks. Writes cues.json."""
import re, json, subprocess, numpy as np, pathlib
md = open(pathlib.Path(__file__).parent / 'vo-script.md').read()
out = {}
for m in re.finditer(r'^### `([^`]+)\.m4a` — .+?\n\n(.+?)(?=\n\n###|\Z)', md, re.S | re.M):
    n, t = m.group(1), ' '.join(m.group(2).split())
    sents = re.split(r'(?<=[.?!])\s+(?=[A-Z0-9])', t)
    raw = subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-i',f'vo/{n}.m4a','-f','f32le','-ac','1','-ar','16000','-'],capture_output=True).stdout
    x = np.frombuffer(raw, np.float32); hop = 160
    r = 20*np.log10(np.sqrt((x[:len(x)//hop*hop].reshape(-1,hop)**2).mean(1))+1e-9)
    act = r > np.percentile(r, 95) - 30
    idx = np.flatnonzero(act); s0, s1 = idx[0]*hop/16000, (idx[-1]+1)*hop/16000
    gaps = []; k = idx[0]
    while k <= idx[-1]:
        if not act[k]:
            j = k
            while j <= idx[-1] and not act[j]: j += 1
            gaps.append(((j-k)*hop/16000, k*hop/16000, j*hop/16000)); k = j
        else: k += 1
    # estimate each sentence start from its share of the text, then snap to the nearest pause (>= 0.25 s) within 1.5 s
    L = sum(len(z) for z in sents); starts = [round(float(s0),2)]; acc = 0; used = []
    for z in sents[:-1]:
        acc += len(z); est = s0 + (s1 - s0) * acc / L
        cand = [g for g in gaps if g[0] >= 0.25 and abs(g[2] - est) < 1.5 and g not in used]
        if cand: g = max(cand, key=lambda g: g[0] - abs(g[2]-est)/3); used.append(g); starts.append(round(float(g[2]),2))
        else: starts.append(round(float(est),2))
    br = used
    out[n] = {'dur': round(len(x)/16000, 2), 'speech': [round(s0,2), round(s1,2)],
              'sentences': [{'t': st, 'text': s} for st, s in zip(starts, sents)],
              'snapped': len(br)}
json.dump(out, open(pathlib.Path(__file__).parent / 'cues.json','w'), indent=1)
for n,v in out.items(): print(n, v['dur'], v['snapped'], len(v['sentences'])-1, [s['t'] for s in v['sentences']])
