"""Soundtrack: VO clips placed by plan.json + the Ende guitar bed, leveled to -16 LUFS (TP -1.5). Writes out/mix.wav.
Music: under the cold open (low), up for the title card, fades out early in scene 1, back for the end card."""
import json, subprocess, pathlib
ROOT = pathlib.Path(__file__).resolve().parent; OUT = ROOT / 'out'
plan = json.load(open(ROOT / 'plan.json')); P = {s['id']: s for s in plan}
TOTAL = plan[-1]['start'] + plan[-1]['dur']
clips = [(c, P[s['id']]['start'] + off) for s in plan for c, off in s['clips'].items()]
LOW, MID = -22, -15      # dB on the music file (-10 LUFS master): LOW ≈ -32 LUFS under the voice, MID for the title card
s1, s2, s7 = P['s1']['start'], P['s2']['start'], P['s7']['start']
vo_end7 = s7 + P['s7']['clips']['s7-end'] + json.load(open(ROOT / 'cues.json'))['s7-end']['dur']
def gain_expr():
    # piecewise dB, linear ramps: open LOW -> title MID -> out by s2+6 ; end card: in from s7-1 at LOW, MID after the last words
    pts = [(0, LOW), (s1 - 0.5, LOW), (s1 + 0.8, MID), (s2 - 0.3, MID), (s2 + 1.5, LOW), (s2 + 7, -60), (s7 - 2, -60), (s7 + 0.5, LOW),
           (vo_end7, LOW), (vo_end7 + 1.2, MID), (TOTAL - 3, MID), (TOTAL, -60)]
    e = f'{pts[-1][1]}'
    for (t0, g0), (t1, g1) in reversed(list(zip(pts, pts[1:]))):
        e = f'if(lt(t,{t1:.3f}),{g0}+({g1}-({g0}))*(t-{t0:.3f})/{max(t1 - t0, .001):.3f},{e})'
    return e
music_start_end = s7 - 2.5   # second pass of the track for the end card starts here (from the top of the track)
inputs, filt = [], []
for i, (c, t) in enumerate(clips):
    inputs += ['-i', str(ROOT / 'vo' / f'{c}.m4a')]
    filt.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(t * 1000)}:all=1[v{i}]')
n = len(clips)
inputs += ['-i', str(ROOT / 'music/ende-ambient-acoustic-guitars-vol-1.mp3'), '-i', str(ROOT / 'music/ende-ambient-acoustic-guitars-vol-1.mp3')]
filt.append(f'[{n}:a]aresample=48000,atrim=0:{s2 + 8:.2f},asetpts=PTS-STARTPTS[m1]')
filt.append(f'[{n+1}:a]aresample=48000,atrim=0:{TOTAL - music_start_end + 1:.2f},asetpts=PTS-STARTPTS,adelay={int(music_start_end * 1000)}:all=1[m2]')
filt.append(f'[m1][m2]amix=inputs=2:normalize=0:duration=longest,volume=\'pow(10,({gain_expr()})/20)\':eval=frame[m]')
filt.append(''.join(f'[v{i}]' for i in range(n)) + f'[m]amix=inputs={n + 1}:normalize=0:duration=longest,atrim=0:{TOTAL:.3f}[mix]')
pre = OUT / 'mix-pre.wav'
subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', *inputs, '-filter_complex', ';'.join(filt), '-map', '[mix]', '-c:a', 'pcm_s16le', str(pre)], check=True)
m = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(pre), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(m[m.rindex('{'):m.rindex('}') + 1])
subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-i', str(pre), '-af',
    f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000",
    '-c:a', 'pcm_s16le', str(OUT / 'mix.wav')], check=True)
print('total', round(TOTAL, 2), 'pre-mix I', j['input_i'])
