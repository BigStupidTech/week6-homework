---
name: music-timestamp-coverage
description: Audits the availability and granularity of time-synced song lyrics ("music timestamps") for an artist using LRCLIB (lrclib.net), a free public API needing no key. For each matched track it parses the synced LRC [mm:ss.xx] timestamps and computes per-track metrics (synced-line count, lines-per-minute, vocal-onset seconds, duration) plus catalog aggregations (sync coverage %, word-sync %, instrumental %, onset and duration distributions, per-album breakdown), writing a Markdown report and CSVs. Use when asked to measure, audit, or compare how many of an artist's songs have synced/timestamped lyrics, how dense the timing is, how long the intros are, or how instrumental a catalog is — e.g. "run my music timestamps skill for <artist>" or "check synced-lyric coverage for <artist>". Re-runnable with one short sentence naming the artist (optionally an album or track-list file). Handles UTF-8 (Cyrillic/CJK) names.
---

# Music Timestamp Coverage

## What this skill does
Audits how much of an artist's catalog has **time-synced lyrics** (the `[mm:ss.xx]`
timestamps used for karaoke, lyric videos, and subtitles) and how fine-grained that
timing is — using **LRCLIB** (lrclib.net), a free, public, open lyrics database that
needs **no API key**. It fetches each matched track, parses the synced LRC, computes
per-track and catalog-level metrics, and writes a Markdown report plus three CSVs. It
is re-runnable with one short sentence and needs no setup beyond Python 3.

## Research questions it answers
1. **Sync coverage** — what share of the catalog has line-level synced lyrics vs. word-level timing, and how does that break down per album?
2. **Timing density** — for non-instrumental synced tracks, how many timestamped lines appear per song and per minute (median / mean / p10 / p90)?
3. **Vocal onset** — how many seconds until the first synced line, what's the onset distribution (median / p90 / max), and which tracks have long instrumental intros (>20s)?
4. **Duration distribution** — the spread of track lengths (min/median/mean/max + histogram), and does length correlate with timing density (Pearson r)?
5. **Instrumental share** — what fraction is instrumental, and how does coverage change once instrumentals are excluded from the denominator?

## How to run it
Standard-library Python 3 — **no `pip install`, no API key.**

```bash
python scripts/lrclib_sync.py --artist "<ARTIST>" [--album "<ALBUM>"] \
    [--tracks tracks.txt] [--duration-hint <sec>] [--max-results 20] \
    [--out-dir ./out] [--user-agent "..."] [--delay 0.3]
```

The default User-Agent already carries a contact (LRCLIB asks for one) — normally
leave it as-is.

## Inputs
- `--artist` — the artist to audit (required unless `--tracks` is given).
- `--album` — optional; narrows discovery and annotates the per-album table.
- `--tracks` — optional path to a newline-delimited file; each line is `Title` (uses
  `--artist`) or `Artist - Title` (split on the first ` - `); `#` lines are comments.
  Use this for a specific catalog, since broad search is capped (see Limits).
- `--duration-hint` — optional seconds, to disambiguate a track in `--tracks` mode.
- `--max-results` — cap results kept per search (default 20).
- `--out-dir` — where to write outputs (default `./out`).
- `--user-agent`, `--delay` — etiquette knobs (defaults are fine).

## What it outputs
Written to `--out-dir` (`<slug>` = the artist name slugified):
- `<slug>_report.md` — the human-readable report (headline numbers, per-album table, duration histogram, long-intro list, missing-sync list, data-quality footer).
- `<slug>_tracks.csv` — one row per track with all per-track metrics.
- `<slug>_summary.csv` — every aggregate statistic as `metric,value`.
- `<slug>_by_album.csv` — the per-album coverage rollup.
- stdout — a short run log and the headline numbers.

## How to present results to the user
After running, **read `<slug>_report.md`** and summarize the headline numbers: total
matched, % synced (and the instrumental-adjusted figure), % word-sync, % instrumental,
median lines/min, median & p90 onset, and the long-intro count. Show the per-album
table and flag any data-quality warnings (unresolved tracks, dropped cover/karaoke
channels, duplicate ids). Point the user to the CSVs for drill-down. Always restate
the caveats below so the numbers aren't over-read.

## Example invocations
```bash
python scripts/lrclib_sync.py --artist "Radiohead"
python scripts/lrclib_sync.py --artist "Daft Punk"          # shows instrumental share
python scripts/lrclib_sync.py --artist "The Weeknd" --album "After Hours"
python scripts/lrclib_sync.py --tracks setlist.txt --artist "Кино"   # UTF-8 works
```
Natural-language trigger: *"run my music timestamps skill for Radiohead."*

## Data source & fallbacks
Primary source is **LRCLIB** — see [`references/data_source.md`](references/data_source.md)
for endpoints, fields, and parsing details. LRCLIB is the only source here that
provides **synced** (timestamped) lyrics. If LRCLIB is down, or a track's duration is
unknown and needed for matching, recover **metadata only** (duration/title) from
MusicBrainz, Deezer, or the iTunes Search API, then re-query LRCLIB.

## Etiquette & limits
- LRCLIB needs no key but asks for a descriptive **User-Agent** (the default includes one). Requests are serialized with a small `--delay`; on HTTP 429 the script reads `Retry-After` and backs off.
- **Search returns at most `--max-results` (default 20) and is not paginated**, so a broad `--artist` run under-samples prolific artists — use `--album` or `--tracks` for fuller coverage.
- LRCLIB is community-contributed, so **duplicates and mislabels exist** (covers, karaoke, re-uploads). Discovery mode drops records whose artist doesn't match and dedupes by id, but review the per-album table and data-quality footer.
- **Instrumentals** are excluded from timing-density denominators so they aren't misread as "missing lyrics."
