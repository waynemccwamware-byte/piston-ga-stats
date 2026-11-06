"""YouTube captions (out/safety-piston-singles.en.srt, plus .en_US.srt for Facebook) and chapters, from cues.json + plan.json.
Each sentence is split into pieces of at most ~80 characters at commas or spaces, timed by their share of the sentence."""
import json, pathlib, re, shutil
ROOT = pathlib.Path(__file__).resolve().parent; OUT = ROOT / 'out'
plan = json.load(open(ROOT / 'plan.json')); cues = json.load(open(ROOT / 'cues.json'))
def pieces(s, n=80):
    if len(s) <= n: return [s]
    words, out, cur = s.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: out.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
        if cur.endswith((',', ':', ';')) and len(cur) > n * 0.45: out.append(cur); cur = ''
    if cur: out.append(cur)
    return out
def ts(t): h, r = divmod(t, 3600); m, s = divmod(r, 60); return f'{int(h):02d}:{int(m):02d}:{s:06.3f}'.replace('.', ',')
import subprocess, numpy as np
def gaps(clip):
    raw = subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-i',str(ROOT/'vo'/f'{clip}.m4a'),'-f','f32le','-ac','1','-ar','16000','-'],capture_output=True).stdout
    x = np.frombuffer(raw, np.float32); hop = 160
    r = 20*np.log10(np.sqrt((x[:len(x)//hop*hop].reshape(-1,hop)**2).mean(1))+1e-9)
    act = r > np.percentile(r,95)-30; idx = np.flatnonzero(act); g=[]; k=idx[0]
    while k <= idx[-1]:
        if not act[k]:
            j=k
            while j<=idx[-1] and not act[j]: j+=1
            if (j-k)*hop/16000 >= .22: g.append((k*hop/16000, j*hop/16000))
            k=j
        else: k+=1
    return idx[0]*hop/16000, (idx[-1]+1)*hop/16000, g
subs = []
for sc in plan:
    for c, off in sc['clips'].items():
        base = sc['start'] + off; s0, s1, G = gaps(c)
        # speaking time only: subtract pauses, then place pieces by character share along the speaking time
        ps = [p for s in cues[c]['sentences'] for p in pieces(s['text'])]
        L = sum(len(p) for p in ps); acc = 0; starts = [s0]
        for p in ps[:-1]:
            acc += len(p); est = s0 + (s1 - s0) * acc / L
            near = [g for g in G if abs(g[1] - est) < 1.4 and g[1] > starts[-1] + .3 * len(p.split())]
            starts.append(min(near, key=lambda g: abs(g[1] - est))[1] if near else est)
        ends = []
        for i in range(len(ps)):
            if i + 1 < len(ps): ends.append(starts[i + 1] - .05)
            else: ends.append(s1 + .3)
        subs += [(base + a, base + b, p) for a, b, p in zip(starts, ends, ps)]
srt = '\n'.join(f'{i}\n{ts(a)} --> {ts(b)}\n{p}\n' for i, (a, b, p) in enumerate(subs, 1))
(OUT / 'safety-piston-singles.en.srt').write_text(srt)
shutil.copy(OUT / 'safety-piston-singles.en.srt', OUT / 'safety-piston-singles.en_US.srt')
ch = [(0, 'Cold open'), (plan[1]['start'], 'Title'), (plan[2]['start'], "What's being counted"), (plan[3]['start'], 'The trend'),
      (plan[4]['start'], 'The funnel plot'), (plan[5]['start'], 'Where fatal accidents still happen'), (plan[6]['start'], 'Try it yourself'), (plan[7]['start'], 'The apps')]
print('\n'.join(f'{int(t // 60)}:{int(t % 60):02d} {n}' for t, n in ch)); print(len(subs), 'captions')
