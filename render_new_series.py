#!/usr/bin/env python3
"""Damon reels 5-7 — punchy cut: loud hooks, hard cuts, animated counters."""
import re, os, shutil, subprocess, math
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BG = (11, 15, 21); BG2 = (18, 26, 38)
GREEN = (74, 222, 128); WHITE = (235, 237, 239); GRAY = (140, 152, 166)
CARD = (24, 32, 46); LINE = (44, 56, 74)
RED = (255, 107, 107); YELLOW = (250, 204, 21)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def font(sz, bold=True):
    return ImageFont.truetype(FB if bold else FR, sz)

def fit(text, maxw, start=150, bold=True):
    sz = start
    while sz > 20:
        f = font(sz, bold)
        if f.getlength(text) <= maxw: return f
        sz -= 6
    return font(20, bold)

F_TINY = font(30, False); F_SMALL = font(38, False)
F_MED = font(52); F_BIG = font(72); F_HERO = font(110)

rows = []
DATA_PATH = os.environ.get("DAMON_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample-data", "pickup-sample.md"))
with open(DATA_PATH) as f:
    for line in f:
        m = re.match(r'\| (\d+) \| ([\d\- :]+) \| \d+ \| (.+?) \| (\d+) \|', line)
        if m:
            num, ts, cls, lat = m.groups()
            job = cls.split(" / ")[0].replace("Reading - ", "Reading ").replace("Math - ", "Math ")
            rows.append((int(num), ts[:10], job, int(lat)/1000.0))
TOTAL = len(rows)
curated = [rows[0]] + [r for r in rows[1:-1] if r[0] % 3 == 0] + [rows[-1]]
NC = len(curated)

def ease_out_back(t):
    t = min(1, max(0, t))
    c = 1.70158
    return 1 + (c+1)*(t-1)**3 + c*(t-1)**2

def ease_out(t):
    t = min(1, max(0, t)); return 1-(1-t)**3

def bg_base():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.ellipse([-300, -300, 500, 500], fill=BG2)
    return img, d

def beat_pulse(t):
    """subtle brightness pulse on the 128bpm beat"""
    beat = 60.0/128.0
    ph = (t % beat) / beat
    return 1.0 + 0.06 * math.exp(-ph*6)

def center_text(d, y, text, f, fill, cx=W//2):
    d.text((cx - f.getlength(text)/2, y), text, font=f, fill=fill)

def hook_scene(lines, colors, t):
    """LOUD first frame: full-width stacked lines, word-by-word pop."""
    img, d = bg_base()
    bp = beat_pulse(t)
    # flash wash behind text
    wash = Image.new("RGB", (W, H), (int(20*bp), int(30*bp), int(42*bp)))
    img = Image.blend(img, wash, 0.35); d = ImageDraw.Draw(img)
    y = 640
    wi = 0
    for txt, col in lines:
        words = txt.split(" ")
        f = fit(txt, W-160, start=132)
        lh = f.size + 28
        # final slot positions (full-size advances), words pop in place
        slots = []
        x = 80
        for w in words:
            slots.append((x, f.getlength(w)))
            x += f.getlength(w + " ")
        for w, (wx, ww0) in zip(words, slots):
            appear = 0.12 * wi
            sc = ease_out_back((t - appear) / 0.35)
            if sc > 0:
                fs = max(10, int(f.size * sc))
                wf = font(fs)
                cx = wx + ww0 / 2
                d.text((cx - wf.getlength(w)/2, y + (f.size - fs)//2), w, font=wf, fill=col)
            wi += 1
        y += lh
    return img

def duel_scene(t):
    """YOU vs DAMON split screen."""
    img, d = bg_base()
    # YOU side (top, red)
    p1 = ease_out(t/0.5)
    d.rounded_rectangle([80, int(300+(1-p1)*80), W-80, 800], radius=30, fill=(46, 24, 28), outline=RED, width=3)
    center_text(d, 360, "YOU", font(64), RED)
    d.text((140, 470), "refresh...", font=F_MED, fill=GRAY)
    if t > 0.9: d.text((140, 550), "click...", font=F_MED, fill=GRAY)
    if t > 1.5: d.text((140, 630), "GONE.", font=font(64), fill=RED)
    # DAMON side (bottom, green)
    p2 = ease_out(max(0, t-0.7)/0.5)
    d.rounded_rectangle([80, int(900+(1-p2)*80), W-80, 1400], radius=30, fill=(18, 40, 30), outline=GREEN, width=3)
    center_text(d, 960, "DAMON", font(64), GREEN)
    if t > 1.2:
        lt = min(6.0, (t-1.2)*4.0)
        center_text(d, 1080, f"{lt:.1f}s", font(110), GREEN)
    if t > 2.7:
        center_text(d, 1230, "CLAIMED", font(56), WHITE)
    return img

def race_scene(t, dur):
    """Big stopwatch 0.0 -> 6.0s while claim cards stack."""
    img, d = bg_base()
    pr = min(1.0, t / dur)
    sec = pr * 6.0
    center_text(d, 200, "CLAIM RACE", F_TINY, GRAY)
    sf = font(190)
    center_text(d, 330, f"{sec:.1f}", sf, GREEN if sec < 6.0 else WHITE)
    center_text(d, 560, "seconds", F_MED, GRAY)
    # progress ring-ish bar
    d.rectangle([140, 700, W-140, 716], fill=LINE)
    d.rectangle([140, 700, 140+int((W-280)*pr), 716], fill=GREEN)
    # stacking claim cards
    n = min(4, int(pr*5))
    for i in range(n):
        num, date, job, lat = curated[(i*7) % NC]
        y = 800 + i*250
        if y > H-320: break
        d.rounded_rectangle([140, y, W-140, y+210], radius=24, fill=CARD, outline=LINE, width=2)
        d.text((180, y+24), f"Claim #{num}", font=F_TINY, fill=GRAY)
        d.text((180, y+64), job[:30], font=F_MED, fill=WHITE)
        ls = f"{lat:.1f}s"
        d.text((W-180-font(52).getlength(ls), y+64), ls, font=font(52), fill=GREEN)
        d.text((W-260, y+24), "CLAIMED", font=F_TINY, fill=GREEN)
    if pr >= 1.0:
        fl = int(255*(0.6+0.4*math.sin(t*10)))
        center_text(d, H-260, "RACE OVER. DAMON WINS.", font(60), (fl, 255, fl))
    return img

def money_scene(t, dur):
    """Counter $0 -> $1,990 with popping claim cards."""
    img, d = bg_base()
    pr = ease_out(t / dur)
    amt = int(pr * 1990)
    center_text(d, 220, "EARNED WHILE TEACHING", F_TINY, GRAY)
    mf = fit(f"${amt:,}", W-200, start=200)
    center_text(d, 330, f"${amt:,}", mf, GREEN)
    d.rectangle([140, 620, W-140, 636], fill=LINE)
    d.rectangle([140, 620, 140+int((W-280)*pr), 636], fill=YELLOW)
    n = min(3, int(pr*4))
    for i in range(n):
        num, date, job, lat = curated[(i*11+3) % NC]
        y = 720 + i*300
        if y > H-380: break
        d.rounded_rectangle([140, y, W-140, y+240], radius=24, fill=CARD, outline=LINE, width=2)
        d.text((180, y+30), f"+${10}  Claim #{num}", font=F_MED, fill=GREEN)
        d.text((180, y+100), job[:32], font=F_SMALL, fill=WHITE)
        d.text((180, y+160), date, font=F_TINY, fill=GRAY)
    return img

def cascade_scene(t, dur):
    """Fast claim cards flying past."""
    img, d = bg_base()
    center_text(d, 140, "LIVE CLAIM LOG", F_TINY, GRAY)
    idx_f = (t / dur) * NC
    idx = min(int(idx_f), NC-1)
    cy = 620
    for off in (-1, 0, 1):
        j = idx + off
        if j < 0 or j >= NC: continue
        num, date, job, lat = curated[j]
        yy = cy + off*270
        card = Image.new("RGB", (W-180, 230), CARD)
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, W-180, 230], radius=26, outline=LINE, width=2)
        cd.text((40, 26), f"Claim #{num} of {TOTAL}", font=F_TINY, fill=GRAY)
        cd.text((40, 70), job[:34], font=F_MED, fill=WHITE)
        cd.text((40, 140), date, font=F_SMALL, fill=GRAY)
        ls = f"{lat:.1f}s"
        cd.text((W-180-40-font(60).getlength(ls), 70), ls, font=font(60), fill=GREEN if lat < 5 else WHITE)
        cd.text((W-180-40-font(30, False).getlength("CLAIMED"), 26), "CLAIMED", font=F_TINY, fill=GREEN)
        if off != 0:
            card = Image.blend(Image.new("RGB", (W-180, 230), BG), card, 0.35)
        img.paste(card, (90, yy))
    return img

def stats_punch(lines, t):
    img, d = bg_base()
    y = 480
    for i, (txt, col) in enumerate(lines):
        ap = ease_out_back((t - i*0.25)/0.4)
        if ap <= 0: continue
        f = fit(txt, W-160, start=120)
        fs = max(12, int(f.size*ap))
        wf = font(fs)
        center_text(d, y, txt, wf, col)
        y += fs + 40
    return img

def gap_scene(line1, line2, t):
    """Curiosity-gap end card."""
    img, d = bg_base()
    p = ease_out(t/0.8)
    f1 = fit(line1, W-160, start=84)
    center_text(d, int(700+(1-p)*60), line1, f1, WHITE)
    if t > 1.0:
        q = ease_out((t-1.0)/0.8)
        f2 = fit(line2, W-160, start=84)
        c = tuple(int(GREEN[i]*q + BG[i]*(1-q)) for i in range(3))
        center_text(d, 830, line2, f2, c)
    if t > 2.0:
        r = ease_out((t-2.0)/0.8)
        c2 = tuple(int(GRAY[i]*r + BG[i]*(1-r)) for i in range(3))
        center_text(d, 1150, "@ericbuildsbots", font(56), c2)
        center_text(d, 1230, "follow for the how", F_SMALL, c2)
    return img

def progress_bar(img, p):
    d = ImageDraw.Draw(img)
    d.rectangle([90, H-90, W-90, H-82], fill=LINE)
    d.rectangle([90, H-90, 90+int((W-180)*p), H-82], fill=GREEN)
    return img

# ---------------- reel definitions: (duration, fn) ----------------
REELS = {
    "reel5": {
        "file": "damon-reel-5-boss-doesnt-know.mp4",
        "scenes": [
            (2.4, lambda t, p: hook_scene(
                [("MY BOSS", WHITE), ("DOESN'T KNOW", WHITE), ("I BUILT THIS.", GREEN)], None, t)),
            (3.2, lambda t, p: hook_scene(
                [("While I sleep,", WHITE), ("it works.", GREEN)], None, t)),
            (3.2, lambda t, p: hook_scene(
                [("While I teach,", WHITE), ("it hunts.", GREEN)], None, t)),
            (6.5, lambda t, p: cascade_scene(t, 6.5)),
            (3.5, lambda t, p: stats_punch(
                [("206 claims.", GREEN), ("85 days.", WHITE), ("$1,990.", GREEN)], t)),
            (4.5, lambda t, p: gap_scene("He thinks I'm just fast.", "Wait till he sees the bot.", t)),
        ],
    },
    "reel6": {
        "file": "damon-reel-6-six-second-race.mp4",
        "scenes": [
            (2.4, lambda t, p: hook_scene(
                [("6.0 SECONDS.", GREEN), ("That's the whole race.", WHITE)], None, t)),
            (3.6, lambda t, p: duel_scene(t)),
            (7.0, lambda t, p: race_scene(t, 7.0)),
            (3.2, lambda t, p: stats_punch(
                [("206 claims.", GREEN), ("85 days.", WHITE), ("6.0s median claim.", GREEN)], t)),
            (4.5, lambda t, p: gap_scene("The secret isn't speed.", "It's never blinking.", t)),
        ],
    },
    "reel7": {
        "file": "damon-reel-7-money-while-teaching.mp4",
        "scenes": [
            (2.4, lambda t, p: hook_scene(
                [("$1,990", GREEN), ("MADE WHILE I TAUGHT.", WHITE)], None, t)),
            (3.2, lambda t, p: hook_scene(
                [("I didn't click once.", WHITE), ("I was in class.", GREEN)], None, t)),
            (7.0, lambda t, p: money_scene(t, 7.0)),
            (3.2, lambda t, p: stats_punch(
                [("206 pickups.", GREEN), ("85 days.", WHITE), ("0 keyboard touches.", WHITE)], t)),
            (4.5, lambda t, p: gap_scene("Your job has tasks like this too.", "What would YOU automate?", t)),
        ],
    },
}

base = os.environ.get("REEL_OUT", os.path.dirname(os.path.abspath(__file__)))
for key, reel in REELS.items():
    scenes = reel["scenes"]
    total = sum(d for d, _ in scenes)
    bounds = []
    acc = 0
    for d, _ in scenes:
        bounds.append((acc, acc+d)); acc += d
    nfr = int(total * FPS)
    fdir = os.path.join(base, "frames_" + key)
    os.makedirs(fdir, exist_ok=True)
    for n in range(nfr):
        t = n / FPS
        for (s0, s1), (d, fn) in zip(bounds, scenes):
            if s0 <= t < s1:
                img = fn(t - s0, t / total)
                break
        else:
            dlast, fnlast = scenes[-1]
            img = fnlast(dlast, 1.0)
        img = progress_bar(img, t / total)
        img.save(f"{fdir}/f{n:04d}.png")
    out = os.path.join(base, reel["file"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30",
                    "-i", fdir + "/f%04d.png", "-i", base + "/banger.wav",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-c:a", "aac", "-shortest", out], check=True)
    shutil.rmtree(fdir)
    print("done:", reel["file"], f"{total:.1f}s")
