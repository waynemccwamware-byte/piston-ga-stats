import asyncio, json, subprocess, os, sys, math
from playwright.async_api import async_playwright
FD='/tmp/claude-0/-home-claude/94a5b245-d412-5637-a7a2-9ba41dde7b41/scratchpad/vid/node_modules/@fontsource'
CSS=''.join(f"@font-face{{font-family:'{f}';font-weight:{w};src:url(http://localhost:8790/__f/{p}-latin-{w}-normal.woff2)}}" for f,p in (('IBM Plex Sans','ibm-plex-sans'),('IBM Plex Mono','ibm-plex-mono')) for w in (400,500,600))
async def route(r):
    u=r.request.url
    if 'fonts.googleapis.com' in u: return await r.fulfill(status=200,content_type='text/css',body=CSS)
    if '/__f/' in u:
        n=u.split('/__f/')[1]; pk='ibm-plex-mono' if 'mono' in n else 'ibm-plex-sans'
        return await r.fulfill(path=f'{FD}/{pk}/files/{n}',content_type='font/woff2')
    if 'localhost' not in u: return await r.abort()
    await r.continue_()

FPS=30
PLAN=json.load(open('plan.json')); SC=next(x for x in PLAN if x['id']=='s6'); DUR=SC['dur']; C=SC['clips']['s6-tour']
def ease(x): x=max(0,min(1,x)); return 4*x*x*x if x<.5 else 1-(-2*x+2)**3/2
async def m(shots=None):
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1280,'height':720},device_scale_factor=1.5)
        await pg.route('**/*',route); await pg.goto('http://localhost:8790/'); await pg.wait_for_timeout(2500)
        sec=await pg.evaluate("()=>[...document.querySelectorAll('section.step')].map(e=>Math.round(e.getBoundingClientRect().top+scrollY))")
        safe,cat,ph,trend,lst=sec[3],sec[4],sec[5],sec[7],sec[-1]
        # the first accident row from 2023 or earlier (final reports), to open at the end
        rowY=await pg.evaluate("""()=>{const s=[...document.querySelectorAll('section.step')].pop();const r=[...s.querySelectorAll('button.head')].find(b=>{const m=b.textContent.match(/(\\d{4})/);return m&&+m[1]<=2023});r.id='pickRow';return Math.round(r.getBoundingClientRect().top+scrollY)}""")
        K=[(0,0),(C+1.6,0),(C+3.0,250),(C+7.3,250),(C+8.6,safe-8),(C+12.6,safe-8),(C+14.2,cat-8),(C+15.6,cat-8),(C+16.8,ph-8),(C+17.8,ph-8),(C+19.0,trend-8),(C+19.8,trend-8),(C+21.0,rowY-260),(DUR,rowY-260)]
        def y(t):
            for (t0,y0),(t1,y1) in zip(K,K[1:]):
                if t0<=t<=t1: return y0+(y1-y0)*ease((t-t0)/(t1-t0 or 1))
            return K[-1][1]
        CLICK=C+21.4; clicked=False
        tmp='out/s6.part.mp4'
        ff=None if shots else subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-r',str(FPS),tmp],stdin=subprocess.PIPE)
        times=shots or [i/FPS for i in range(round(DUR*FPS))]
        for t in times:
            if t>=CLICK and not clicked: await pg.evaluate("document.getElementById('pickRow').click()"); await pg.wait_for_timeout(250); clicked=True
            await pg.evaluate(f"window.scrollTo(0,{y(t):.1f})")
            fade=max(1-min(1,t/0.5), min(1,(t-(DUR-0.5))/0.5) if t>DUR-0.5 else 0)
            await pg.evaluate(f"(()=>{{let f=document.getElementById('__fade');if(!f){{f=document.createElement('div');f.id='__fade';f.style.cssText='position:fixed;inset:0;background:#000;z-index:99999;pointer-events:none';document.body.appendChild(f)}}f.style.opacity={fade:.3f}}})()")
            img=await pg.screenshot(type='jpeg',quality=92)
            if shots: open(f'out/s6_{t}.jpg','wb').write(img)
            else: ff.stdin.write(img)
        if ff:
            ff.stdin.close(); assert ff.wait()==0; os.replace(tmp,'out/s6.mp4')
        await b.close()
sh=[float(x) for x in sys.argv[1].split(',')] if len(sys.argv)>1 else None
asyncio.run(m(sh))
