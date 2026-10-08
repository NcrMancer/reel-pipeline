# Reel Pipeline — an automated TikTok content factory

Turns a data export into finished vertical videos: scripted captions, generated music, burned-in text, hard cuts — rendered to 9:16 MP4 with one command. Built to document [Damon](https://github.com/NcrMancer/damon-proof) in public.

## What it does

```
pickup-sample.md ──▶ render_new_series.py ──▶ damon-reel-N-*.mp4 (1080×1920, 30fps)
                          │
make_banger.py ──▶ banger.wav (128 BPM electronic bed) ──▶ mixed under the reel
```

1. **Data in** — a markdown table of timestamped events (see `sample-data/pickup-sample.md` for the format).
2. **Script** — `render_new_series.py` builds the reel: loud hook frame in the first second, word-by-word pop-in captions, hard cuts, animated counters, claim-card cascades. Pure PIL + ffmpeg, no editor.
3. **Music** — `make_banger.py` synthesizes a 128 BPM electronic track from scratch with numpy (kick, hats, bass, lead). No stock audio, no licensing questions.
4. **Output** — finished 1080×1920 MP4s, ready to post.

## Run it

```bash
pip install pillow numpy
python make_banger.py            # generates banger.wav
python render_new_series.py      # renders reels from sample-data/
```

To render from your own data, point the script at your export:

```bash
DAMON_DATA=/path/to/your-export.md python render_new_series.py
```

The expected row format is `| # | claimed_at | duration_min | class | latency_ms |` — see `sample-data/pickup-sample.md`.

## Design choices

- **Hook-first editing** — the most shocking frame opens every reel. Retention is decided in the first second.
- **Everything generated** — captions, music, and motion graphics are all code. A new data export means new videos, not new editing sessions.
- **No paid tools** — PIL, numpy, ffmpeg. The whole factory runs on free software.

## Built by

Eric Rodriguez (NcrMancer) — I direct AI systems that ship working software. This pipeline was specified, built, and iterated by AI agents under my direction.
