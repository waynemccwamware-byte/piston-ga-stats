"""Scene timeline: where each VO clip starts inside its scene, and each scene's length. Writes plan.json."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
cues = json.load(open(ROOT / 'cues.json'))
GAP = 0.5
SCENES = [  # id, title, lead-in, clips, tail
    ('s0', 'Cold open', 1.5, ['s0-open'], 1.5),
    ('s1', 'Title', 0, [], 7.0),
    ('s2', "What's counted", 0.8, ['s2-sources', 's2-yardstick'], 1.2),
    ('s3', 'The trend', 0.6, ['s3-trend', 's3-footnotes', 's3-all'], 1.6),
    ('s4', 'The funnel plot', 0.6, ['s4-intro', 's4-history', 's4-axes', 's4-coin', 's4-limits', 's4-dots', 's4-caveat'], 1.6),
    ('s5', 'Where fatal accidents still happen', 0.6, ['s5-category', 's5-phase'], 1.4),
    ('s6', 'Try it yourself', 0.5, ['s6-tour'], 1.0),
    ('s7', 'End card', 0.8, ['s7-end'], 7.0),
]
plan, t0 = [], 0.0
for sid, title, lead, clips, tail in SCENES:
    t, cl = lead, {}
    for c in clips:
        cl[c] = round(t, 3); t += cues[c]['dur'] + GAP
    dur = round((t - GAP if clips else t) + tail, 3)
    plan.append({'id': sid, 'title': title, 'start': round(t0, 3), 'dur': dur, 'clips': cl}); t0 += dur
json.dump(plan, open(ROOT / 'plan.json', 'w'), indent=1)
for s in plan: print(s['id'], s['start'], s['dur'])
print('total', round(t0, 1), 's =', f'{int(t0//60)}:{int(t0%60):02d}')
