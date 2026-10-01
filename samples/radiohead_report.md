# Music timestamp coverage — Radiohead

_Generated 2026-10-01 00:51 UTC · source: LRCLIB (lrclib.net), free public API_

## Run parameters

- Artist: **Radiohead**
- Queries: search q='Radiohead'
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
- **With synced (line-level) lyrics:** 100.0%  (**100.0%** excluding instrumentals)
- **With word-level sync:** 0.0%
- **Instrumental:** 0.0%  ·  **plain-only:** 0.0%  ·  **no lyrics:** 0.0%
- **Lines per minute (synced):** median 7.4 · mean 7.11 · p10 3.12 · p90 9.37
- **Synced lines per song:** min 15 · median 34.5 · mean 31.65 · max 47
- **First-line onset (s):** median 24.2 · p90 81.06 · max 81.08  ·  **long intros (>20s):** 12
- **Duration (s):** min 218.0 · median 257.0 · mean 280.1 · max 392.0
- **Correlation (duration vs lines/min):** Pearson r = -0.709

## Duration histogram

- <2:00     |  0
- 2:00–3:00 |  0
- 3:00–4:00 | ███████ 7
- 4:00–5:00 | ████████ 8
- 5:00+     | █████ 5

## Per-album coverage

| Album | Tracks | % synced | % word-sync | % instr. | median lines/min | median onset (s) |
|---|--:|--:|--:|--:|--:|--:|
| Radiohead | 15 | 100.0 | 0.0 | 0.0 | 7.05 | 27.6 |
| Radiohead Videos | 3 | 100.0 | 0.0 | 0.0 | 9.06 | 18.98 |
| Radiohead - Creep | 1 | 100.0 | 0.0 | 0.0 | 9.41 | 19.1 |
| Radiohead Songs | 1 | 100.0 | 0.0 | 0.0 | 9.37 | 19.1 |

## Long instrumental intros (first lyric > 20s)

- **Radiohead - Daydreaming** — first line at 81.1s (duration 6:27)
- **Radiohead - Daydreaming** — first line at 81.1s (duration 6:27)
- **Radiohead - Daydreaming** — first line at 81.1s (duration 6:24)
- **Radiohead - Lotus Flower** — first line at 60.0s (duration 5:08)
- **Radiohead - Nude** — first line at 46.8s (duration 4:17)
- **Radiohead - Man Of War** — first line at 40.8s (duration 4:30)
- **Radiohead - The Daily Mail** — first line at 33.6s (duration 3:38)
- **Radiohead - House of Cards** — first line at 29.9s (duration 4:33)
- **Radiohead - High and Dry** — first line at 27.6s (duration 4:17)
- **Radiohead - No Surprises** — first line at 26.8s (duration 3:49)
- **Radiohead - Karma Police** — first line at 21.6s (duration 4:24)
- **Radiohead - Creep (Acoustic)** — first line at 20.5s (duration 4:15)

## Data quality

- Lookup failures: 0
- Unresolved tracks: 0
- Duplicate ids collapsed: 0
- Non-matching artist records dropped (discovery): 0

> ⚠️ LRCLIB search is capped at 20 non-paginated results, so broad-artist runs are under-sampled — use `--album` or `--tracks` for fuller coverage. LRCLIB is community data, so duplicates/mislabels exist; instrumentals are excluded from density denominators.
