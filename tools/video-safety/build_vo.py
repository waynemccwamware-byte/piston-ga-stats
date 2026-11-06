#!/usr/bin/env python3
"""Voice-over for the Safety and Piston Singles video: tools/video-safety/vo-raw/*.m4a -> vo/<name>.m4a.
RNNoise denoise when the pauses are noisy, head/tail trimmed to 0.4 s, gentle gate, leveled to -21 LUFS.
Same chain as the Claude + ForeFlight Primer's build_vo.py (narration only)."""
import os, subprocess, sys, tempfile, pathlib, json
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent
RAW, OUT = ROOT / 'vo-raw', ROOT / 'vo'
def ff(*args):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *args], check=True)

def lufs(src):
    import re
    e = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(src), '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', e)[-1])

RNN = ROOT / 'models/std.rnnn'   # RNNoise model (github.com/richardpl/arnndn-models); 'sh' ate speech on quiet takes

def gaps_db(src):
    raw = subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-i', str(src), '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32); n = 800
    fr = x[:len(x) // n * n].reshape(-1, n)
    return float(np.percentile(20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), 10))

def denoise(src, tmp):
    """Wayne's takes: RNNoise after raising the take to -20 LUFS (RNNoise misreads quiet input).
    Skipped when the pauses are already clean (it clipped word ends on short, clean takes)."""
    g = -20 - lufs(src)
    if gaps_db(src) + g < -66: return src
    out = tmp / (src.stem + '-dn.wav')
    ff('-i', str(src), '-af', f'aresample=48000,volume={g:.2f}dB,highpass=f=70,arnndn=m={RNN}', str(out))
    return out

NARR_LUFS, PAD = -21.0, 0.4   # narration sits ~2 dB above the bubble clips; keep 0.4 s of quiet at each end

def trim_filter(src, pad):
    """atrim filter keeping `pad` s of quiet around the speech. Speech = a run of >= 250 ms above (loud - 32 dB),
    so a knock or click before the first word or after the last one is cut off."""
    raw = subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-i', str(src), '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32); hop = 800; dur = len(x) / 16000
    r = 20 * np.log10(np.sqrt((x[:len(x) // hop * hop].reshape(-1, hop) ** 2).mean(1)) + 1e-9)
    act = r > np.percentile(r, 95) - 32
    runs, k = [], 0
    while k < len(act):
        if act[k]:
            j = k
            while j < len(act) and act[j]: j += 1
            runs.append((k, j)); k = j
        else: k += 1
    long = [(a, z) for a, z in runs if z - a >= 5] or runs or [(0, len(act))]
    first, last = runs.index(long[0]) if long[0] in runs else 0, runs.index(long[-1]) if long[-1] in runs else len(runs) - 1
    loud = lambda run: r[run[0]:run[1]].max() > np.percentile(r, 95) - 20   # a word, not a click or knock
    while first > 0 and runs[first][0] - runs[first - 1][1] <= 3 and loud(runs[first - 1]): first -= 1   # short words like "Your"
    while last < len(runs) - 1 and runs[last + 1][0] - runs[last][1] <= 3 and loud(runs[last + 1]): last += 1
    # word endings are soft ("-cast", a final "st" hiss): after the last word, keep any sound within 300 ms, loud or not
    while last < len(runs) - 1 and runs[last + 1][0] - runs[last][1] <= 6: last += 1
    a = runs[first][0] * hop / 16000 if runs else 0.0
    z = runs[last][1] * hop / 16000 if runs else dur
    s0, s1 = a, z
    a, z = max(0.0, a - pad), min(dur, z + max(pad, 0.35))
    # the pads are true silence: fade in over the last 80 ms before the first word, out over 200 ms from 120 ms after the last
    fi = max(0.0, s0 - a - 0.08); fo = s1 - a + 0.12
    return (f'atrim={a:.3f}:{z:.3f},asetpts=PTS-STARTPTS,aformat=channel_layouts=mono,'
            f'afade=t=in:st={fi:.3f}:d=0.08,afade=t=out:st={fo:.3f}:d=0.2')

GATE = 'agate=threshold=0.0063:ratio=3:range=0.178:attack=5:release=400:knee=2'   # -44 dBFS: spares soft word endings

def narration(src, dst):
    """Trim long head/tail silence to PAD, then level to NARR_LUFS (two-pass loudnorm), AAC .m4a."""
    import json
    trim = f'{trim_filter(src, PAD)},volume={-20 - lufs(src):.2f}dB,{GATE}'
    ln = f'loudnorm=I={NARR_LUFS}:TP=-1.5:LRA=11'
    m = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(src), '-af', f'{trim},{ln}:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex('{'):m.rindex('}') + 1])
    ff('-i', str(src), '-af', f"{trim},{ln}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
       f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000",
       '-c:a', 'aac', '-b:a', '128k', str(dst))

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        for src in sorted(RAW.glob('*.m4a')) + sorted(RAW.glob('*.mp3')):
            dn = denoise(src, t)
            narration(dn, OUT / (src.stem + '.m4a'))
            print(src.stem, 'denoised' if dn != src else 'clean')
