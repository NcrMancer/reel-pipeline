#!/usr/bin/env python3
"""Energetic 128 BPM electronic banger for the new punchy reels (~25s)."""
import numpy as np
import wave

SR = 44100
DUR = 25.0
t = np.arange(int(SR * DUR)) / SR
mix = np.zeros_like(t)

BPM = 128.0
BEAT = 60.0 / BPM  # 0.46875s

def add(start, sig):
    s = int(start * SR); e = s + len(sig)
    if s >= len(t): return
    e = min(e, len(t))
    mix[s:e] += sig[:e-s]

# --- KICK: four on the floor ---
nbeats = int(DUR / BEAT)
for b in range(nbeats):
    n = int(0.28 * SR); bt = np.arange(n) / SR
    f = 150 - 110 * (bt / 0.28)  # pitch drop
    kick = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-bt*9) * 0.95
    add(b * BEAT, kick)

# --- HATS: offbeat 8ths ---
rng = np.random.default_rng(11)
for b in range(nbeats * 2):
    st = b * BEAT / 2 + BEAT / 4
    n = int(0.04 * SR); ht = np.arange(n) / SR
    hat = rng.standard_normal(n) * np.exp(-ht*220) * (0.10 if b % 2 else 0.06)
    add(st, hat)

# --- CLAP on 2 & 4 ---
for b in range(nbeats):
    if b % 4 in (1, 3):
        n = int(0.18*SR); ct = np.arange(n)/SR
        clap = rng.standard_normal(n) * np.exp(-ct*40) * 0.28
        clap += np.sin(2*np.pi*1800*ct) * np.exp(-ct*60) * 0.10
        add(b*BEAT, clap)

# --- BASS: driving 8th-note saw-ish line, Am F C G (2 bars each) ---
roots = [55.00, 43.65, 65.41, 49.00]  # A1 F1 C2 G1
bar = BEAT * 4
pattern = [0, 0, 1, 0, 0, 2, 0, 1]  # semitone offsets
for ci, root in enumerate(roots):
    for rep in range(2):
        base_st = ci * 2 * bar + rep * bar
        for i, off in enumerate(pattern):
            f = root * 2**(off/12)
            st = base_st + i * BEAT / 2
            n = int(0.20*SR); xt = np.arange(n)/SR
            saw = (2*((f*xt) % 1.0) - 1.0)
            tone = saw * 0.5 + np.sin(2*np.pi*f*xt)*0.5
            tone *= np.exp(-xt*7) * 0.42
            add(st, tone)

# --- LEAD STABS: minor pentatonic hits every 2 beats, rising energy ---
scale = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0]
for b in range(0, nbeats, 2):
    f = scale[(b//2) % len(scale)]
    n = int(0.30*SR); xt = np.arange(n)/SR
    stab = (np.sin(2*np.pi*f*xt) + 0.4*np.sin(2*np.pi*f*2*xt)
            + 0.25*np.sin(2*np.pi*f*3*xt)) * np.exp(-xt*8) * 0.16
    add(b*BEAT + BEAT/2, stab)

# --- RISER into 12s and 19s ---
for rs in (10.0, 17.0):
    n = int(2.0*SR); rt = np.arange(n)/SR
    riser = np.sin(2*np.pi*(400 + 900*rt/2.0)*rt) * (rt/2.0)**1.6 * 0.22
    add(rs, riser)
    # impact
    n2 = int(0.5*SR); it = np.arange(n2)/SR
    impact = np.sin(2*np.pi*60*it) * np.exp(-it*8) * 0.8
    impact += rng.standard_normal(n2) * np.exp(-it*25) * 0.12
    add(rs+2.0, impact)

# --- master ---
fi = int(0.3*SR); fo = int(2.0*SR)
mix[:fi] *= np.linspace(0, 1, fi)
mix[-fo:] *= np.linspace(1, 0, fo)
mix = mix / np.max(np.abs(mix)) * 0.9

with wave.open("/home/hatch/workspace/your_files/damon-proof/banger.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix*32767).astype(np.int16).tobytes())
print("banger done")
