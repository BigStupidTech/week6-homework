# Music timestamp coverage — Daft Punk

_Generated 2026-10-01 01:03 UTC · source: LRCLIB (lrclib.net), free public API_

## Run parameters

- Artist: **Daft Punk**
- Queries: search q='Daft Punk'
- Max results: 20
- User-Agent: `music-timestamp-coverage/1.0 (student coursework; contact: bigstupidtech@gmail.com)`

## Research questions this answers

1. **Sync coverage** — what share of the catalog has line-level synced lyrics vs word-level timing, per album?
2. **Timing density** — synced lines per song and per minute (median / mean / p10 / p90)?
3. **Vocal onset** — seconds to the first synced line; onset distribution; long instrumental intros (>20s)?
4. **Duration distribution** — track-length spread and histogram; does length correlate with timing density?
5. **Instrumental share** — fraction instrumental, and coverage once instrumentals are excluded?

## Headline numbers

- **Tracks matched:** 20
- **With synced (line-level) lyrics:** 50.0%  (**83.3%** excluding instrumentals)
- **With word-level sync:** 0.0%
- **Instrumental:** 40.0%  ·  **plain-only:** 10.0%  ·  **no lyrics:** 0.0%
- **Lines per minute (synced):** median 16.66 · mean 14.84 · p10 3.13 · p90 25.37
- **Synced lines per song:** min 12 · median 72.0 · mean 65.8 · max 160
- **First-line onset (s):** median 33.01 · p90 78.68 · max 80.21  ·  **long intros (>20s):** 9
- **Duration (s):** min 156.55 · median 234.0 · mean 277.71 · max 633.0
- **Correlation (duration vs lines/min):** Pearson r = -0.157

## Duration histogram

- <2:00     |  0
- 2:00–3:00 | ██ 2
- 3:00–4:00 | ██████████ 10
- 4:00–5:00 | ███ 3
- 5:00+     | █████ 5

## Per-album coverage

| Album | Tracks | % synced | % word-sync | % instr. | median lines/min | median onset (s) |
|---|--:|--:|--:|--:|--:|--:|
| Daft Punk | 11 | 54.5 | 0.0 | 45.5 | 11.76 | 49.03 |
| Daft Punk - Superheroes | 2 | 100.0 | 0.0 | 0.0 | 18.27 | 20.84 |
| Daft Punk - Aerodynamic | 1 | 0.0 | 0.0 | 100.0 | None | None |
| Daft Punk - Technologic | 1 | 100.0 | 0.0 | 0.0 | 25.23 | 0.01 |
| Daft Punk - Voyager | 1 | 0.0 | 0.0 | 100.0 | None | None |
| Daft Punk - Within | 1 | 100.0 | 0.0 | 0.0 | 8.76 | 64.63 |
| Daft Punk Daft Club | 1 | 0.0 | 0.0 | 0.0 | None | None |
| Daft Punk - Essentials | 1 | 0.0 | 0.0 | 0.0 | None | None |
| Daft Club (Rare Daft Punk Remixes) | 1 | 0.0 | 0.0 | 100.0 | None | None |

## Long instrumental intros (first lyric > 20s)

- **Daft Punk - Make Love (Official Audio)** — first line at 80.2s (duration 4:50)
- **Daft Punk - Something About Us** — first line at 78.5s (duration 3:48)
- **Daft Punk - Within** — first line at 64.6s (duration 3:53)
- **Daft Punk - Robot Rock** — first line at 62.3s (duration 4:47)
- **Get Lucky (Daft Punk Remix)** — first line at 35.8s (duration 10:33)
- **Daft Punk - One More Time** — first line at 30.2s (duration 3:45)
- **Daft Punk - Superheroes** — first line at 20.8s (duration 3:58)
- **Daft Punk - Superheroes** — first line at 20.8s (duration 3:55)
- **Daft Punk - Harder, Better, Faster, Stronger** — first line at 20.2s (duration 3:42)

## Tracks without synced lyrics (10)

- Daft Punk — _instrumental_
- Daft Punk — _instrumental_
- Daft Punk — _instrumental_
- Daft Punk - Electronic Funk — _instrumental_
- Daft Punk - Aerodynamic — _instrumental_
- Daft Punk - Voyager — _instrumental_
- Aerodynamic (Daft Punk Remix) — _plain_only_
- Aerodynamic (Daft Punk Remix) — _plain_only_
- Daft Punk - Veridis Quo (Official Audio) — _instrumental_
- Aerodynamic (Daft Punk Remix) — _instrumental_

## Data quality

- Lookup failures: 0
- Unresolved tracks: 0
- Duplicate ids collapsed: 0
- Non-matching artist records dropped (discovery): 0

> ⚠️ LRCLIB search returns at most --max-results (default 20) results and is not paginated, so broad-artist runs are under-sampled — use `--album` or `--tracks` for fuller coverage. LRCLIB is community data, so duplicates/mislabels exist; instrumentals are excluded from density denominators.
