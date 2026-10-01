# Music Timestamp Coverage — a reusable research skill

**Course:** Foundations of AI (MSAI5513) · **Week 6: Build a Research Skill**

This repo contains a reusable **Claude Skill** that researches **music timestamps** —
specifically, how much of an artist's catalog has **time-synced lyrics** (the
`[mm:ss.xx]` timing used for karaoke, lyric videos, and subtitles) and how
fine-grained that timing is. It builds on earlier coursework on synced lyrics.

> **The packaged `.skill` file is on the [`feature/skill`](../../tree/feature/skill)
> branch** (per the assignment). `main` holds only this README.

## What a "skill" is
A skill is a small, reusable folder of instructions + scripts that Claude can run
again from one short sentence — you describe the complex job once, then re-run it
with e.g. *"run my music timestamps skill for Radiohead."* This skill contains:

```
music-timestamp-coverage/
├── SKILL.md                   # instructions Claude reads (what it does + how to run)
├── scripts/
│   └── lrclib_sync.py         # Python (stdlib only) — fetches data, builds tables + visualizer
├── references/
│   └── data_source.md         # the LRCLIB API reference
└── assets/
    └── visualizer.html        # standalone karaoke-highlight web page (searches LRCLIB live)
```
(That folder is packaged as `music-timestamp-coverage.skill`.)

## 🎬 Timestamp visualizer (local web page)
Beyond the numbers, the skill ships a **karaoke-style visualizer** — a plain local
HTML page, **no server and no audio**: a timer lights up each line's words by their
`[mm:ss.xx]` timestamps.

- **`assets/visualizer.html`** — open it in a browser and **search LRCLIB live** for
  any artist/song (LRCLIB is CORS-open, so the page fetches directly). Click a result,
  press ▶, and the lyrics light up line-by-line; click any line to jump there.
- **`SLUG_visualizer.html`** — every run of the script also bakes the audited tracks
  into their own offline copy (see `samples/radiohead_visualizer.html`).

A working sample is committed at
[`samples/radiohead_visualizer.html`](../../tree/feature/skill/samples/radiohead_visualizer.html)
— download it and open in any browser.

## The research topic & questions
**Topic:** availability and granularity of time-synced song lyrics, using free,
public data. The skill answers:

1. **Sync coverage** — what share of the catalog has line-level synced lyrics vs. word-level timing, per album?
2. **Timing density** — synced lines per song and per minute (median / mean / p10 / p90)?
3. **Vocal onset** — seconds to the first synced line; the onset distribution; long instrumental intros (>20s)?
4. **Duration distribution** — track-length spread + histogram; does length correlate with timing density?
5. **Instrumental share** — fraction instrumental, and how coverage changes once instrumentals are excluded?

## The data source
**LRCLIB** (https://lrclib.net) — a free, public, open lyrics database that needs
**no API key**. For each track it returns the duration, an `instrumental` flag, a
`hasWordSync` flag, and `syncedLyrics` (an LRC string of `[mm:ss.xx]` line
timestamps). The script parses those timestamps to compute per-track metrics and
catalog-level aggregations. Metadata-only fallbacks (MusicBrainz, Deezer, iTunes
Search) are documented in `references/data_source.md`.

## What the skill produces
Running it writes a Markdown report plus three CSVs (`_report.md`, `_tracks.csv`,
`_summary.csv`, `_by_album.csv`) — headline coverage numbers, a per-album table, a
duration histogram, the vocal-onset distribution, a long-intro list, and a
data-quality footer.

## Sample results (real runs against LRCLIB)
Full reports are in [`samples/`](../../tree/feature/skill/samples) on the
`feature/skill` branch.

| Artist | Matched | % synced (excl. instrumental) | Instrumental | Median lines/min | Median onset | Long intros (>20s) |
|---|--:|--:|--:|--:|--:|--:|
| **Radiohead** | 20 | 100% (100%) | 0% | 7.4 | 24.2s | 12 |
| **Daft Punk** | 20 | 50% (**83.3%**) | 40% | 16.7 | 33.0s | 9 |

Takeaways the skill surfaces automatically: Radiohead's catalog is fully synced with
sparse, slow timing and long intros (Pearson r = **−0.71** between track length and
lines/min — longer songs have fewer lyric lines per minute); Daft Punk looks
half-covered until you exclude its 40% instrumental tracks, after which real sync
coverage jumps to **83%**.

## How to run it
Standard-library Python 3 — no `pip install`, no API key:
```bash
python music-timestamp-coverage/scripts/lrclib_sync.py --artist "Radiohead"
```
Or, inside Claude with the skill installed: *"run my music timestamps skill for Radiohead."*

## Branches
- **`main`** — this README only.
- **`feature/skill`** — the packaged `music-timestamp-coverage.skill`, the unpacked
  skill source, and the sample reports.
