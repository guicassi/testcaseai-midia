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
    pg.evaluate("cfg => build(cfg)", cfg)
    total = pg.evaluate("window.TOTAL"); events = pg.evaluate("window.EVENTS"); style = cfg["style"]
    silent = out + ".silent.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-r", str(FPS), silent], stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        pg.evaluate(f"render({i / FPS})"); ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
    ff.stdin.close(); ff.wait(); b.close()

N = int(SR * total); L = np.zeros(N); R = np.zeros(N); rng = np.random.default_rng(11)
tt = np.arange(N) / SR
def add(s, t, g=1.0, pan=0.0):
    i = int(t * SR); j = min(N, i + len(s))
    if i < 0 or i >= N: return
    L[i:j] += s[:j-i] * g * (1 - max(0, pan)); R[i:j] += s[:j-i] * g * (1 + min(0, pan))
ex = lambda n, k: np.exp(-np.linspace(0, k, n))
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)
lp = lambda x, f: sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), x)
hp = lambda x, f: sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), x)
note = lambda m: 440 * 2 ** ((m - 69) / 12)
T = lambda d: np.arange(int(SR*d)) / SR
noise = lambda d: rng.standard_normal(int(SR*d))
def sq(f, d, duty=.5): t = T(d); return np.where((t*f) % 1 < duty, 1.0, -1.0)
def tri(f, d): t = T(d); return 2*np.abs(2*((t*f) % 1) - 1) - 1
def env(d, a=.005, k=6):
    t = T(d); return np.minimum(1, t/a) * np.exp(-t*k)
def kick(d=.35, f0=150, f1=45, g=1.0):
    t = T(d); f = f1 + (f0-f1)*np.exp(-t*30); return np.tanh(np.sin(2*np.pi*np.cumsum(f)/SR)*2.5) * np.exp(-t*9) * g
def snare(d=.22): return (bp(noise(d), 1500, 7000)*.8 + np.sin(2*np.pi*190*T(d))*.4) * env(d, .002, 18)
def clap(d=.25):
    n = noise(d); e = np.zeros(len(n)); t = T(d)
    for o in (0, .012, .024): e += np.exp(-np.maximum(0, t-o)*60) * (t >= o)
    return bp(n, 900, 5000) * (e*.5 + np.exp(-t*12)*.5) * .9
def hat(d=.05, g=.4): return hp(noise(d), 7000) * env(d, .001, 60) * g
def mix_bed(bed, gain): bed = bed / max(1e-9, np.max(np.abs(bed))) * gain; fade = np.minimum(1, tt/.4) * np.minimum(1, np.maximum(0, total - tt)/1.0); return bed * fade

bed = np.zeros(N)
def put(buf, s, t, g=1.0):
    i = int(t*SR); j = min(N, i + len(s))
    if 0 <= i < N: buf[i:j] += s[:j-i] * g

if style == "editorial":
    bpm = 118; bt = 60/bpm; roots = [45, 41, 36, 43]
    for k, x in enumerate(np.arange(0, total, bt)):
        put(bed, kick(.4), x, 1.0)
        if k % 2 == 1: put(bed, clap(), x, .55)
        put(bed, hat(.04, .35), x + bt/2)
        if k % 4 == 3: put(bed, hat(.04, .25), x + bt*.75)
        r = roots[(k // 8) % 4]
        for s16 in (0, .5):
            d = bt*.42; b_ = (sq(note(r), d, .5)*.5 + np.sin(2*np.pi*note(r)*T(d))) * env(d, .004, 5)
            put(bed, lp(b_, 500), x + s16*bt, .55)
    # sidechain
    sc = np.ones(N);
    for x in np.arange(0, total, bt): i = int(x*SR); j = min(N, i + int(.18*SR)); sc[i:j] = np.linspace(.35, 1, j-i)
    bed = mix_bed(bed * sc, .22)
elif style == "terminal":
    bpm = 140; s16 = 60/bpm/4; chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    for k, x in enumerate(np.arange(0, total, s16)):
        ch = chords[(k // 32) % 4]; m = ch[k % 3] + (12 if (k // 3) % 2 else 0)
        put(bed, sq(note(m), s16*.9, .25) * env(s16*.9, .002, 10), x, .22)
        if k % 4 == 0: put(bed, tri(note(ch[0] - 24), s16*3.6) * env(s16*3.6, .003, 3), x, .6)
        if k % 8 == 4: put(bed, hp(noise(.08), 2000) * env(.08, .001, 40), x, .35)
        if k % 2 == 0: put(bed, hp(noise(.02), 8000) * env(.02, .001, 120), x, .15)
        if k % 16 == 0: put(bed, kick(.2, 120, 50, .8), x)
    bed = mix_bed(bed, .17)
elif style == "quadro":  # violão dedilhado (Karplus-Strong) + palmas leves
    def pluck(f, d=1.6, bright=.5):
        n = int(SR*d); p = max(2, int(SR/f)); buf = rng.uniform(-1, 1, p) * 1.0; o = np.zeros(n)
        buf = lp(buf, 1500 + 4000*bright) if p > 12 else buf
        for i in range(n): o[i] = buf[i % p]; buf[i % p] = .5*(buf[i % p] + buf[(i+1) % p]) * .996
        return o * np.minimum(1, np.arange(n)/40)
    bpm = 96; e8 = 60/bpm/2; chords = [[48, 55, 64, 67], [45, 52, 60, 64], [41, 48, 57, 65], [43, 50, 59, 67]]
    patt = [0, 2, 1, 3, 2, 1, 3, 2]; cache = {}
    for k, x in enumerate(np.arange(0, total, e8)):
        ch = chords[(k // 8) % 4]; m = ch[patt[k % 8]] if k % 8 else ch[0]
        if m not in cache: cache[m] = pluck(note(m), 1.4)
        put(bed, cache[m], x + rng.uniform(0, .008), .5 if k % 8 else .7)
    for k, x in enumerate(np.arange(0, total, e8*2)):
        if k % 4 == 3: put(bed, clap(.2), x, .18)
        put(bed, hp(noise(.03), 6000) * env(.03, .001, 70), x + e8, .12)
    bed = mix_bed(lp(bed, 6000), .2)
elif style == "trailer":  # drone grave + pulsação de relógio
    d0 = np.zeros(N)
    for m, g in ((33, 1), (40, .6), (45, .4), (28, .8)):
        for det in (-.08, .08):
            f = note(m) * 2**(det/12); d0 += g * (2*((tt*f) % 1) - 1)
    d0 = lp(d0, 380) * (.7 + .3*np.sin(2*np.pi*.11*tt)); bed += d0
    for x in np.arange(0, total, .5): put(bed, hp(noise(.02), 3000) * env(.02, .001, 120), x, .9 if int(x*2) % 2 == 0 else .6)
    bed = mix_bed(bed, .2)
elif style == "pop":  # marimba + baixo funk + palmas
    bpm = 112; s16 = 60/bpm/4; prog = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]
    mel = [0, None, 2, 1, None, 3, 2, None, 0, 2, None, 3, 1, None, 2, None]
    def marimba(f, d=.5): t = T(d); return (np.sin(2*np.pi*f*t) + .3*np.sin(2*np.pi*4*f*t)*np.exp(-t*30) + .15*np.sin(2*np.pi*10*f*t)*np.exp(-t*60)) * env(d, .001, 7)
    def fbass(f, d=.18): t = T(d); saw = 2*((t*f) % 1) - 1; return lp(saw, 900) * env(d, .002, 9)
    bpatt = [0, None, None, 12, None, 0, None, None, 0, None, 7, None, None, 0, 12, None]
    for k, x in enumerate(np.arange(0, total, s16)):
        ch = prog[(k // 16) % 4]; mi = mel[k % 16]
        if mi is not None: put(bed, marimba(note(ch[mi] + 12)), x, .45)
        bi_ = bpatt[k % 16]
        if bi_ is not None: put(bed, fbass(note(ch[0] - 24 + bi_)), x, .9)
        if k % 4 == 0: put(bed, kick(.25, 130, 50, .8), x)
        if k % 8 == 4: put(bed, clap(), x, .45)
        if k % 2 == 1: put(bed, hp(noise(.04), 5000) * env(.04, .001, 40), x, .18)
    bed = mix_bed(bed, .2)
else:  # chat: lo-fi
    bpm = 78; bt = 60/bpm; chords = [[50, 53, 57, 60, 64], [43, 53, 57, 59, 64], [48, 52, 55, 59, 62], [45, 48, 52, 55, 59]]
    bar = bt*4
    for k, x in enumerate(np.arange(0, total + bar, bar)):
        ch = chords[k % 4]; d = bar + .3; t = T(d); s = np.zeros(len(t))
        for m in ch:
            f = note(m + 12); s += (np.sin(2*np.pi*f*t) + .25*np.sin(2*np.pi*2*f*t)*np.exp(-t*3) + .12*np.sin(2*np.pi*3.01*f*t)*np.exp(-t*6))
        s *= np.minimum(1, t/.01) * np.exp(-t*.9) * (1 + .12*np.sin(2*np.pi*4.5*t))
        put(bed, lp(s, 2400), x, .5)
        put(bed, np.sin(2*np.pi*note(ch[0]-12)*T(bt*1.8)) * env(bt*1.8, .01, 1.5), x, .9)
        put(bed, np.sin(2*np.pi*note(ch[0]-12)*T(bt*1.5)) * env(bt*1.5, .01, 1.8), x + bt*2.5, .7)
    for k, x in enumerate(np.arange(0, total, bt)):
        sw = .06 if k % 2 else 0
        if k % 4 in (0, 2) or (k % 8 == 7): put(bed, lp(kick(.3, 110, 48), 900), x + sw, .7)
        if k % 2 == 1: put(bed, lp(snare(.25), 3500), x, .35)
        for e in (0, .5): put(bed, lp(hat(.04, .3), 9000), x + e*bt + (.05 if e else 0), .6)
    crack = np.zeros(N); idx = rng.integers(0, N, int(total*24)); crack[idx] = rng.uniform(-1, 1, len(idx))
    bed = lp(bed, 5000) + lp(hp(crack, 1500), 6000) * .6 + lp(noise(total)[:N], 800) * .01
    bed = mix_bed(bed, .2)
L += bed; R += bed

def mixv(*a):
    n = max(len(x) for x in a); o = np.zeros(n)
    for x in a: o[:len(x)] += x
    return o
def scratch():
    d = .45; t = T(d); m = np.sin(2*np.pi*3.2*t)
    return bp(noise(d), 300, 3000) * (.6 + .4*m) * np.sin(np.linspace(0, np.pi, len(t))) * .7
def rip():
    d = .3; n = noise(d); o = np.zeros(len(n)); seg = 12; Ls = len(n)//seg
    for k in range(seg):
        f = 6000 - 5000*k/seg; a = k*Ls; b_ = min(len(n), a + 2*Ls); w = np.zeros(len(n)); w[a:b_] = np.hanning(b_-a); o += bp(n, max(80, f*.5), min(20000, f*1.5)) * w
    return o * .6
def stamp(): return mixv(kick(.35, 180, 60, .9), hp(noise(.03), 2000) * env(.03, .001, 50) * .6)
def snap(): return hp(noise(.04), 2500) * env(.04, .0005, 70) * 1.2
def typer(n=10, gap=.06):
    o = np.zeros(int(SR*(n*gap + .1)))
    for i in range(n): s = (bp(noise(.02), 1500, 6000) + np.sin(2*np.pi*120*T(.02))*.5) * env(.02, .0005, 120); j = int(i*gap*SR); o[j:j+len(s)] += s
    return o * .5
def bell(f, d=1.0): t = T(d); return (np.sin(2*np.pi*f*t) + .4*np.sin(2*np.pi*2.76*f*t)*np.exp(-t*4)) * env(d, .002, 4) * .35
def blip(hi=True): f = 1320 if hi else 880; d = .07; return sq(f, d, .5) * env(d, .002, 25) * .25
def key(): return (bp(noise(.025), 2000, 8000) * .7 + sq(160, .025) * .15) * env(.025, .0005, 90)
def err():
    d = .45; t = T(d); f = 440*np.exp(-t*2.5); return np.sign(np.sin(2*np.pi*np.cumsum(f)/SR)) * env(d, .002, 3) * .22
def boot():
    d = .5; t = T(d); f = 200 + 1400*t/d; return np.sign(np.sin(2*np.pi*np.cumsum(f)/SR)) * np.sin(np.pi*t/d) * .15
def tickb(i): return sq(600 + i*30, .03, .5) * env(.03, .001, 50) * .18
def win():
    o = np.zeros(int(SR*.8))
    for i, m in enumerate((72, 76, 79, 84)): s = sq(note(m), .16, .25) * env(.16, .002, 8) * .22; j = int(i*.09*SR); o[j:j+len(s)] += s
    return o
def recv():
    o = np.zeros(int(SR*.25))
    for i, f in enumerate((880, 1320)): s = np.sin(2*np.pi*f*T(.12)) * env(.12, .003, 22) * .35; j = int(i*.06*SR); o[j:j+len(s)] += s
    return o
def send():
    d = .18; t = T(d); f = 500 + 900*t/d; return np.sin(2*np.pi*np.cumsum(f)/SR) * np.sin(np.pi*t/d) * .25 + hp(noise(d), 3000) * np.sin(np.pi*t/d)**2 * .05
def pling(): return bell(1568, .8) * .8
def popn(f): d = .09; t = T(d); ff = f*.35 + f*.65*np.exp(-t*40); return np.sin(2*np.pi*np.cumsum(ff)/SR) * env(d, .002, 9) * .5

bi = 0
for ev in events:
    t, k, a = ev[0], ev[1], (ev[2] if len(ev) > 2 else None); pan = rng.uniform(-.25, .25)
    if k == "scratch": add(scratch(), t, .8)
    elif k == "rip": add(rip(), t, .8)
    elif k == "stamp": add(stamp(), t, .9)
    elif k == "thump": add(mixv(kick(.6, 120, 40, 1.0), hp(noise(.05), 1500)*env(.05, .001, 40)*.7), t, 1.0)
    elif k == "snap": add(snap(), t, .7, pan)
    elif k == "type_s": add(typer(14, .055), t, .7)
    elif k == "end":
        add(kick(.5), t, .9)
        for i, m in enumerate((76, 81, 88)): add(bell(note(m), 1.4), t + i*.06, .7)
    elif k == "key": add(key(), t + rng.uniform(-.005, .005), rng.uniform(.5, .9), pan)
    elif k == "enter": add(mixv(key() * 1.4, sq(110, .04)*env(.04, .001, 30)*.2), t, .9)
    elif k == "blip": add(blip(bool(a)), t, .9)
    elif k == "err": add(err(), t, 1.0)
    elif k == "boot": add(boot(), t, .9)
    elif k == "tickb": add(tickb(bi), t, .9); bi += 1
    elif k == "win": add(win(), t, 1.0)
    elif k == "recv": add(recv(), t, 1.0)
    elif k == "send": add(send(), t, 1.0)
    elif k == "pling": add(pling(), t, 1.0)
    elif k == "pop": add(popn(a or 700), t, .6, pan)
    elif k == "marker":
        d = a or .5; n = noise(d); m = .5 + .5*np.abs(np.sin(2*np.pi*np.cumsum(5 + 9*rng.random(int(SR*d)))/SR))
        add(bp(n, 2500, 7000) * m * np.sin(np.pi*T(d)/d)**.5 * .22, t, 1.0)
    elif k == "squeak": d = .18; ff = 1800 + 400*np.sin(2*np.pi*12*T(d)); add(np.sin(2*np.pi*np.cumsum(ff)/SR) * np.sin(np.pi*T(d)/d) * .12, t, 1.0)
    elif k == "scribble": d = .3; add(bp(noise(d), 1500, 6000) * (.5 + .5*np.sign(np.sin(2*np.pi*22*T(d)))) * .35, t, 1.0)
    elif k == "tick_pen": add(mixv(bp(noise(.12), 2500, 7000)*np.linspace(1, 0, int(SR*.12))*.3, np.sin(2*np.pi*1760*T(.2))*env(.2, .002, 12)*.18), t, 1.0)
    elif k == "strum_end":
        for i_, m in enumerate((48, 55, 60, 64, 67, 72)): f = note(m); d = 2.2; tt_ = T(d); add((np.sin(2*np.pi*f*tt_) + .4*np.sin(4*np.pi*f*tt_)) * env(d, .002, 1.8) * .12, t + i_*.025, 1.0)
    elif k == "swell":
        d = 2.0; tt_ = T(d); s_ = np.zeros(len(tt_))
        for m in (57, 64, 69): s_ += 2*((tt_*note(m)) % 1) - 1
        add(lp(s_, 1200) * np.sin(np.pi*tt_/d)**2 * .12, t, 1.0)
    elif k == "boom": add(mixv(kick(2.0, 70, 28, 1.2), lp(noise(1.5), 200)*env(1.5, .005, 2.5)*.6), t, 1.0)
    elif k in ("braam", "braam_s"):
        d = 2.4 if k == "braam" else .55; tt_ = T(d); s_ = np.zeros(len(tt_))
        for m in (33, 40, 45, 48):
            for det in (-.1, .1): s_ += 2*((tt_*note(m)*2**(det/12)) % 1) - 1
        cut = 300 + 2200*np.exp(-tt_*3); out_ = np.zeros(len(tt_)); seg = 30; Ls = len(tt_)//seg
        for i_ in range(seg): a_ = i_*Ls; b_ = min(len(tt_), a_ + Ls); out_[a_:b_] = lp(s_, float(cut[min(len(cut)-1, a_)]))[a_:b_]
        add(mixv(np.tanh(out_*.6) * env(d, .01, 1.2 if k == "braam" else 5) * .5, kick(1.0, 60, 30, .9)), t, 1.0)
    elif k == "riser":
        d = 1.2; tt_ = T(d); f = 200 + 2400*(tt_/d)**2; add(mixv(bp(noise(d), 800, 9000) * (tt_/d)**2 * .5, np.sin(2*np.pi*np.cumsum(f)/SR) * (tt_/d)**2 * .12), t, 1.0)
    elif k == "slide": d = .35; tt_ = T(d); f = 600 + 1200*(tt_/d); add(np.sin(2*np.pi*np.cumsum(f)/SR) * np.sin(np.pi*tt_/d) * .2, t, 1.0)
    elif k == "mar":
        sc = [72, 74, 76, 79, 81, 84, 86, 88]; f = note(sc[(a or 0) % len(sc)]); tt_ = T(.45)
        add((np.sin(2*np.pi*f*tt_) + .3*np.sin(2*np.pi*4*f*tt_)*np.exp(-tt_*30)) * env(.45, .001, 8) * .35, t, 1.0, pan)
    elif k == "boing": d = .45; tt_ = T(d); f = 220 + 160*np.sin(2*np.pi*9*tt_)*np.exp(-tt_*4) + 200*tt_; add(np.sin(2*np.pi*np.cumsum(f)/SR) * env(d, .003, 5) * .35, t, 1.0)
    elif k == "pop_hi": add(popn(1300), t, 1.0)
    elif k == "fanfare":
        for i_, m in enumerate((72, 76, 79, 84)): tt_ = T(.5); f = note(m); add((np.sin(2*np.pi*f*tt_) + .3*np.sin(2*np.pi*4*f*tt_)*np.exp(-tt_*30)) * env(.5, .001, 6) * .35, t + i_*.08, 1.0)
        add(clap(), t + .32, .7)
    elif k == "chimeLo":
        for i, m in enumerate((74, 79, 83, 86)): add(bell(note(m), 1.6), t + i*.11, .6, -.3 + i*.2)

mx = np.stack([L, R], 1); mx = np.tanh(mx*1.5)/np.tanh(1.5); mx = mx/max(1e-9, np.max(np.abs(mx)))*.89
wav = out + ".wav"
with wave.open(wav, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mx*32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
pathlib.Path(silent).unlink(); pathlib.Path(wav).unlink()
print(f"OK {out} ({total:.1f}s, {style})")
