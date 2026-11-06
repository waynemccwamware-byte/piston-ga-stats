"""Film scenes from scenes.html, one MP4 per scene (1920x1080, 30 fps, x264 veryfast CRF 18).
Usage: python3 film.py FONTDIR s0 s2 ...   (FONTDIR = a node_modules/@fontsource folder with ibm-plex-sans and ibm-plex-mono)
       add --shots t1,t2 to save JPEG frames instead of filming."""
import sys, json, asyncio, subprocess, os, pathlib
import qrcode
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent; OUT = ROOT / 'out'; OUT.mkdir(exist_ok=True)
FPS = 30
def fontcss(d):
    css = ''
    for fam, pkg, ws in (('IBM Plex Sans', 'ibm-plex-sans', (400, 500, 600)), ('IBM Plex Mono', 'ibm-plex-mono', (400, 500, 600))):
        for w in ws: css += f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(file://{d}/{pkg}/files/{pkg}-latin-{w}-normal.woff2)}}"
    return css
def qr_svg(url='https://geezer-geek-pilot-control-panel.netlify.app/'):
    q = qrcode.QRCode(border=0); q.add_data(url); q.make(fit=True); m = q.get_matrix(); n = len(m)
    cells = ''.join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for y, r in enumerate(m) for x, v in enumerate(r) if v)
    return f'<svg viewBox="-2 -2 {n+4} {n+4}" width="100%" height="100%" shape-rendering="crispEdges"><rect x="-2" y="-2" width="{n+4}" height="{n+4}" fill="#e7e4dc"/><g fill="#10141a">{cells}</g></svg>'
async def main(fontdir, scenes, shots):
    data = json.load(open(ROOT / 'scene-data.json')); data['qr'] = qr_svg()
    plan = json.load(open(ROOT / 'plan.json')); cues = json.load(open(ROOT / 'cues.json'))
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for sid in scenes:
            dur = next(s for s in plan if s['id'] == sid)['dur']
            pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
            errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.add_init_script(f'window.DATA={json.dumps(data)};window.PLAN={json.dumps(plan)};window.CUES={json.dumps(cues)};window.SCENE="{sid}";')
            await pg.goto('file://' + str(ROOT / 'scenes.html'))
            await pg.evaluate('css => document.getElementById("fontcss").textContent = css', fontcss(fontdir))
            await pg.evaluate('document.fonts.ready.then(()=>Promise.all([...document.fonts].map(f=>f.load())))')
            await pg.evaluate('setup()')
            if shots:
                for t in shots:
                    await pg.evaluate(f'render({t})'); await pg.screenshot(path=str(OUT / f'{sid}_{t}.jpg'), type='jpeg', quality=85)
            else:
                tmp = OUT / f'{sid}.part.mp4'
                ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS), str(tmp)], stdin=subprocess.PIPE)
                for i in range(round(dur * FPS)):
                    await pg.evaluate(f'render({i / FPS})'); ff.stdin.write(await pg.screenshot(type='jpeg', quality=92))
                ff.stdin.close()
                if ff.wait() == 0: os.replace(tmp, OUT / f'{sid}.mp4')
                else: sys.exit('ffmpeg failed on ' + sid)
            if errs: print(sid, 'page errors:', errs)
            await pg.close(); print(sid, 'done')
        await b.close()
a = sys.argv[1:]; shots = None
if '--shots' in a: i = a.index('--shots'); shots = [float(x) for x in a[i + 1].split(',')]; del a[i:i + 2]
asyncio.run(main(a[0], a[1:], shots))
