
import sys, json, wave, subprocess, pathlib, numpy as np
from scipy.signal import butter, sosfilt
from playwright.sync_api import sync_playwright

html, cfg_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.loads(pathlib.Path(cfg_path).read_text(encoding="utf-8"))
FPS, SR = 30, 48000
chrome = next((str(p) for p in pathlib.Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")), None)

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=chrome)
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto(pathlib.Path(html).resolve().as_uri())
    pg.evaluate("document.body.className='render'; document.getElementById('stage').style.transform='none'")
    pg.evaluate("cfg => build(cfg)", cfg)
    total = pg.evaluate("window.TOTAL"); events = pg.evaluate("window.EVENTS")
    silent = out + ".silent.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-r", str(FPS), silent], stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        pg.evaluate(f"render({i / FPS})"); ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
    ff.stdin.close(); ff.wait(); b.close()

N = int(SR * total); L = np.zeros(N); R = np.zeros(N); rng = np.random.default_rng(7)
def add(s, t, g=1.0, pan=0.0):
    i = int(t * SR); j = min(N, i + len(s))
    if i < 0 or i >= N: return
    L[i:j] += s[:j-i] * g * (1 - max(0, pan)); R[i:j] += s[:j-i] * g * (1 + min(0, pan))
ex = lambda n, k: np.exp(-np.linspace(0, k, n))
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
lp = lambda x, f: sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), x)
hp = lambda x, f: sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), x)
note = lambda m: 440 * 2 ** ((m - 69) / 12)
def sweep(f0, f1, d, k):
    n = int(SR*d); t = np.arange(n)/SR; f = f1 + (f0-f1)*np.exp(-t*k); return np.sin(2*np.pi*np.cumsum(f)/SR), n
def pop(f0=900, f1=300, d=.09): s, n = sweep(f0, f1, d, 40); return s * ex(n, 9) * .6
def click(d=.012):
    n = int(SR*d); x = bp(rng.standard_normal(n), 2500, 7000) * ex(n, 7)
    return (x*.5 + np.sin(2*np.pi*180*np.arange(n)/SR) * ex(n, 12) * .3) * 1.1
def whoosh(d=.55):
    n = int(SR*d); x = rng.standard_normal(n); o = np.zeros(n); seg = 24; L_ = n // seg
    for k in range(seg):
        f = 300 + 4500 * (k/seg)**1.6; y = bp(x, max(60, f*.6), min(20000, f*1.4)); w = np.zeros(n); a = k*L_; bb = min(n, a + 2*L_); w[a:bb] = np.hanning(bb - a); o += y*w
    return o * np.sin(np.linspace(0, np.pi, n))**1.5 * .35
def hit(d=.6):
    s, n = sweep(135, 45, d, 18); return (np.tanh(s*2.2)*ex(n, 5) + lp(rng.standard_normal(n), 1800)*ex(n, 40)*.5) * .9
def glitch(d=.38):
    n = int(SR*d); t = np.arange(n)/SR; o = np.zeros(n); st = int(SR*.03)
    for a in range(0, n, st):
        f = rng.choice([220, 330, 440, 660, 880, 1320]); bb = min(n, a+st); o[a:bb] = np.round(np.sign(np.sin(2*np.pi*f*t[a:bb]))*3)/3 * (.6 if rng.random() > .3 else 0)
    return hp(o, 300) * .18
def ding(f, d=.9):
    n = int(SR*d); t = np.arange(n)/SR
    return (np.sin(2*np.pi*f*t) + .35*np.sin(2*np.pi*2.01*f*t) + .15*np.sin(2*np.pi*3.02*f*t)) * np.minimum(1, t/.004) * ex(n, 7) * .32
def thud(d=.3): s, n = sweep(120, 60, d, 25); return s * ex(n, 9) * .8
def tick(d=.06): n = int(SR*d); t = np.arange(n)/SR; return (np.sin(2*np.pi*1800*t)*.6 + bp(rng.standard_normal(n), 3000, 8000)*.4) * ex(n, 14) * .7
def buzz(d=.45):
    n = int(SR*d); t = np.arange(n)/SR; s = np.sign(np.sin(2*np.pi*110*t)) * .5 + np.sign(np.sin(2*np.pi*117*t)) * .5
    return lp(s, 1500) * np.minimum(1, t/.01) * np.minimum(1, (d - t)/.08) * .28
def boing(d=.5): s, n = sweep(260, 520, d, 6); return s * (1 + .5*np.sin(2*np.pi*14*np.arange(n)/SR)) * ex(n, 5) * .35
def swish(d=.22): n = int(SR*d); return bp(rng.standard_normal(n), 3000, 9000) * np.sin(np.linspace(0, np.pi, n))**2 * .25

# trilha de fundo: acordes Am F C G com pulso e batida leve a partir da metade
tt = np.arange(N)/SR; bed = np.zeros(N); prog = [[57,60,64,69],[53,57,60,65],[48,55,60,64],[55,59,62,67]]; seg = total/4
for k, ch in enumerate(prog):
    d = seg + .6; n = int(SR*d); t = np.arange(n)/SR; s = np.zeros(n)
    for m in ch:
        for det in (-.12, 0, .12):
            ff_ = note(m) * 2**(det/12); s += np.sin(2*np.pi*ff_*t) + .3*np.sin(2*np.pi*2*ff_*t + .4)
    s = lp(s, 1400) * np.minimum(1, t/.6) * np.minimum(1, (d - t)/.6); i = int(k*seg*SR); j = min(N, i + n); bed[i:j] += s[:j-i]
beat = 60/104; bed *= .55 + .45*(1 - np.exp(-((tt % beat)/beat)*6)); bed = bed/np.max(np.abs(bed))*.10*np.minimum(1, tt/1.0)*np.minimum(1, (total - tt)/1.2)
L += bed; R += bed
for x in np.arange(total*.5, total - .6, beat): add(thud(.22), x, .35)
for x in np.arange(total*.5 + beat/2, total - .6, beat): add(click(.03), x, .25, .3)

for ev in events:
    t, k, a = ev[0], ev[1], (ev[2] if len(ev) > 2 else None); pan = rng.uniform(-.3, .3)
    if k == "pop": add(pop(a or 700, (a or 700)*.35, .09), t, .6, pan)
    elif k == "click": add(click(), t + rng.uniform(-.008, .008), rng.uniform(.55, .95), pan)
    elif k == "whoosh": add(whoosh(.6), t, .8)
    elif k == "whoosh_s": add(whoosh(.45), t, .4)
    elif k == "hit": add(hit(), t, .55)
    elif k == "glitch": add(glitch(), t, 1.0)
    elif k == "ding": add(ding(note(a or 84)), t, .9)
    elif k == "thud": add(thud(.4), t, .9)
    elif k == "swish": add(swish(), t, 1.0, pan)
    elif k == "tick": add(tick(), t, .9)
    elif k == "buzz": add(buzz(), t, .9)
    elif k == "boing": add(boing(), t, .9)
    elif k == "click2": add(click(.03), t, 1.2); add(pop(1200, 500, .06), t, .4)
    elif k == "correct":
        for i_, m in enumerate((79, 84, 88)): add(ding(note(m), .9), t + i_*.07, .8)
    elif k == "chime":
        for i_, m in enumerate((84, 88, 91, 96)): add(ding(note(m), 1.2), t + i_*.09, .7, -.3 + i_*.2)

mix = np.stack([L, R], 1); mix = np.tanh(mix*1.6)/np.tanh(1.6); mix = mix/max(1e-9, np.max(np.abs(mix)))*.89
wav = out + ".wav"
with wave.open(wav, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
pathlib.Path(silent).unlink(); pathlib.Path(wav).unlink()
print(f"OK {out} ({total:.1f}s)")
