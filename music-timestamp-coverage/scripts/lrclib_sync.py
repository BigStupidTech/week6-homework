#!/usr/bin/env python3
"""music-timestamp-coverage — audit time-synced lyric coverage for an artist via LRCLIB.

Free, public, no API key. Fetches tracks from https://lrclib.net, parses the
synced LRC [mm:ss.xx] line timestamps, and computes per-track metrics plus
catalog-level aggregations. Writes a Markdown report + 3 CSVs and prints a short
run log. Standard library only (no pip install).

Examples:
  python scripts/lrclib_sync.py --artist "Radiohead"
  python scripts/lrclib_sync.py --artist "The Weeknd" --album "After Hours"
  python scripts/lrclib_sync.py --tracks setlist.txt --artist "КИНО"
"""
import argparse
import csv
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API_BASE = "https://lrclib.net/api"
DEFAULT_UA = ("music-timestamp-coverage/1.0 "
              "(student coursework; contact: bigstupidtech@gmail.com)")

# LRC timed-line: [mm:ss.xx] text  (fractional part may be 2=centisec or 3=millisec)
LRC_LINE = re.compile(r"^\[(\d+):(\d{2})(?:[.:](\d{1,3}))?\]\s?(.*)$")
# ID-tag metadata lines to ignore, e.g. [ar:Artist] [ti:Title] [length:03:50]
ID_TAG = re.compile(r"^\[(ar|ti|al|au|by|offset|length|re|ve|tool):", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def http_get_json(path, params, ua, delay, stats):
    """GET API_BASE+path?params -> parsed JSON, or None. Handles 404 (expected
    miss), 429 (Retry-After + exponential backoff), and other errors (logged)."""
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params, encoding="utf-8")
    attempt = 0
    while attempt < 4:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            time.sleep(delay)              # polite pause after every call
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(delay)
                return None               # TrackNotFound — normal for /api/get
            if e.code == 429:
                ra = e.headers.get("Retry-After")
                try:
                    wait = float(ra) if ra else 5.0
                except ValueError:
                    wait = 5.0
                wait = min(wait * (2 ** attempt), 60.0)
                sys.stderr.write(f"[429] rate-limited; backing off {wait:.0f}s\n")
                time.sleep(wait)
                attempt += 1
                continue
            sys.stderr.write(f"[http {e.code}] {url}\n")
            stats["lookup_failures"] += 1
            return None
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            sys.stderr.write(f"[error] {url}: {e}\n")
            stats["lookup_failures"] += 1
            return None
    stats["lookup_failures"] += 1
    return None


# --------------------------------------------------------------------------- #
# LRC parsing + per-track metrics
# --------------------------------------------------------------------------- #
def parse_synced(synced):
    """Return (onsets_all, sung) where onsets_all includes blank-text end markers
    and sung = [(onset, text)] for non-empty lines."""
    onsets_all, sung = [], []
    if not synced:
        return onsets_all, sung
    for raw in synced.split("\n"):
        line = raw.rstrip("\r")
        if not line or ID_TAG.match(line):
            continue
        m = LRC_LINE.match(line)
        if not m:
            continue
        mm, ss, frac, text = m.group(1), m.group(2), m.group(3), m.group(4)
        onset = int(mm) * 60 + int(ss)
        if frac:
            onset += int(frac) / (10 ** len(frac))   # parse by own digit length
        onsets_all.append(onset)
        if text and text.strip():
            sung.append((onset, text.strip()))
    return onsets_all, sung


def track_metrics(rec):
    """Build the per-track metric dict from a raw LRCLIB record."""
    title = rec.get("trackName") or rec.get("name") or ""
    dur = rec.get("duration")
    dur = float(dur) if isinstance(dur, (int, float)) else None
    instrumental = bool(rec.get("instrumental"))
    has_word = bool(rec.get("hasWordSync"))
    synced = rec.get("syncedLyrics")
    plain = rec.get("plainLyrics")

    onsets_all, sung = parse_synced(synced)
    line_count = len(sung)
    has_synced = bool(synced) and line_count > 0
    first_onset = min((o for o, _ in sung), default=None)
    last_ts = max(onsets_all, default=None)
    span = (last_ts - first_onset) if (first_onset is not None and last_ts is not None) else None
    gaps = [b - a for a, b in zip([o for o, _ in sung], [o for o, _ in sung][1:])]
    median_gap = statistics.median(gaps) if gaps else None
    max_gap = max(gaps) if gaps else None
    lpm = (line_count / (dur / 60.0)) if (dur and dur > 0 and has_synced) else None

    if has_word:
        status = "word_synced"
    elif has_synced:
        status = "synced"
    elif instrumental:
        status = "instrumental"
    elif plain:
        status = "plain_only"
    else:
        status = "none"

    return {
        "id": rec.get("id"),
        "trackName": title,
        "artistName": rec.get("artistName") or "",
        "albumName": rec.get("albumName") or "",
        "duration_sec": dur,
        "duration_mmss": mmss(dur),
        "instrumental": instrumental,
        "hasWordSync": has_word,
        "has_synced_lyrics": has_synced,
        "has_plain_lyrics": bool(plain),
        "synced_line_count": line_count if has_synced else None,
        "lines_per_min": lpm,
        "first_onset_sec": first_onset,
        "last_timestamp_sec": last_ts,
        "timing_span_sec": span,
        "median_inter_line_gap_sec": median_gap,
        "max_inter_line_gap_sec": max_gap,
        "plain_char_count": len(plain or ""),
        "lyric_status": status,
        "source_url": f"{API_BASE}/get/{rec.get('id')}",
    }


def mmss(sec):
    if sec is None:
        return ""
    sec = int(round(sec))
    return f"{sec // 60}:{sec % 60:02d}"


# --------------------------------------------------------------------------- #
# stats helpers (stdlib only)
# --------------------------------------------------------------------------- #
def pct(values, p):
    """Linear-interpolated percentile p in [0,1]; None on empty."""
    xs = sorted(v for v in values if v is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p
    lo = int(math.floor(k))
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def safe(fn, values):
    xs = [v for v in values if v is not None]
    return fn(xs) if xs else None


def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 2:
        return None
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sxx = sum((p[0] - mx) ** 2 for p in pairs)
    syy = sum((p[1] - my) ** 2 for p in pairs)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pairs)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def pctof(num, den):
    return round(100.0 * num / den, 1) if den else 0.0


# --------------------------------------------------------------------------- #
# collection
# --------------------------------------------------------------------------- #
def discover(artist, album, max_results, ua, delay, stats):
    """Discovery mode: search by artist (structured if album), filter to the
    artist, dedupe by id. Returns list of raw records."""
    records = []
    if album:
        records = http_get_json("/search", {"artist_name": artist, "album_name": album}, ua, delay, stats) or []
    if not records:
        records = http_get_json("/search", {"q": artist}, ua, delay, stats) or []
    kept, seen, dropped = [], set(), 0
    tokens = [t for t in re.split(r"\s+", artist.lower()) if t]
    for rec in records[:max_results]:
        an = (rec.get("artistName") or "").lower()
        if tokens and not any(t in an for t in tokens):
            dropped += 1
            continue
        rid = rec.get("id")
        if rid in seen:
            stats["duplicate_id_collisions"] += 1
            continue
        seen.add(rid)
        kept.append(rec)
    stats["dropped_non_matching_artist"] = dropped
    return kept


def parse_tracks_file(path, default_artist):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if " - " in line:
                a, t = line.split(" - ", 1)
                out.append((a.strip(), t.strip()))
            else:
                out.append((default_artist, line))
    return out


def resolve_track(artist, title, album, dur_hint, ua, delay, stats):
    """Track-list mode lookup with fuzzy-duration + search fallbacks."""
    params = {"artist_name": artist, "track_name": title}
    if album:
        params["album_name"] = album
    if dur_hint:
        p = dict(params, duration=dur_hint)
        rec = http_get_json("/get", p, ua, delay, stats)
        if rec:
            return rec
    rec = http_get_json("/get", params, ua, delay, stats)   # retry without duration
    if rec:
        return rec
    arr = http_get_json("/search", {"track_name": title, "artist_name": artist}, ua, delay, stats) or []
    return arr[0] if arr else None


# --------------------------------------------------------------------------- #
# aggregation + output
# --------------------------------------------------------------------------- #
TRACK_COLS = ["id", "trackName", "artistName", "albumName", "duration_sec", "duration_mmss",
              "instrumental", "hasWordSync", "has_synced_lyrics", "has_plain_lyrics",
              "synced_line_count", "lines_per_min", "first_onset_sec", "last_timestamp_sec",
              "timing_span_sec", "median_inter_line_gap_sec", "max_inter_line_gap_sec",
              "plain_char_count", "lyric_status", "source_url"]

HIST_BUCKETS = [("lt120", 0, 120), ("120_180", 120, 180), ("180_240", 180, 240),
                ("240_300", 240, 300), ("300_plus", 300, 10 ** 9)]


def aggregate(tracks):
    n = len(tracks)
    synced = [t for t in tracks if t["has_synced_lyrics"]]
    noninstr = [t for t in tracks if not t["instrumental"]]
    synced_ni = [t for t in synced if not t["instrumental"]]
    lpm = [t["lines_per_min"] for t in synced_ni]
    onset = [t["first_onset_sec"] for t in synced_ni]
    durs = [t["duration_sec"] for t in tracks]

    hist = {}
    for name, lo, hi in HIST_BUCKETS:
        hist[name] = sum(1 for d in durs if d is not None and lo <= d < hi)

    agg = {
        "total_tracks_matched": n,
        "pct_with_synced_lyrics": pctof(len(synced), n),
        "pct_with_word_sync": pctof(sum(1 for t in tracks if t["hasWordSync"]), n),
        "pct_instrumental": pctof(sum(1 for t in tracks if t["instrumental"]), n),
        "pct_plain_only": pctof(sum(1 for t in tracks if t["lyric_status"] == "plain_only"), n),
        "pct_no_lyrics": pctof(sum(1 for t in tracks if t["lyric_status"] == "none"), n),
        "coverage_adjusted_excl_instrumentals": pctof(len(synced_ni), len(noninstr)),
        "synced_line_count_min": safe(min, [t["synced_line_count"] for t in synced_ni]),
        "synced_line_count_median": safe(statistics.median, [t["synced_line_count"] for t in synced_ni]),
        "synced_line_count_mean": round(safe(statistics.mean, [t["synced_line_count"] for t in synced_ni]) or 0, 2) if synced_ni else None,
        "synced_line_count_max": safe(max, [t["synced_line_count"] for t in synced_ni]),
        "lines_per_min_median": roundn(pct(lpm, 0.5)),
        "lines_per_min_mean": roundn(safe(statistics.mean, lpm)),
        "lines_per_min_p10": roundn(pct(lpm, 0.10)),
        "lines_per_min_p90": roundn(pct(lpm, 0.90)),
        "first_onset_sec_median": roundn(pct(onset, 0.5)),
        "first_onset_sec_mean": roundn(safe(statistics.mean, onset)),
        "first_onset_sec_p90": roundn(pct(onset, 0.90)),
        "first_onset_sec_max": roundn(safe(max, onset)),
        "count_long_intro_gt20s": sum(1 for o in onset if o is not None and o > 20),
        "duration_sec_min": roundn(safe(min, durs)),
        "duration_sec_median": roundn(pct(durs, 0.5)),
        "duration_sec_mean": roundn(safe(statistics.mean, durs)),
        "duration_sec_max": roundn(safe(max, durs)),
        "pearson_duration_vs_lines_per_min": roundn(
            pearson([t["duration_sec"] for t in synced_ni], [t["lines_per_min"] for t in synced_ni]), 3),
        "lookup_failures": None,  # filled from stats later
    }
    for name, _, _ in HIST_BUCKETS:
        agg[f"duration_hist_{name}"] = hist[name]
    return agg


def roundn(v, nd=2):
    return round(v, nd) if isinstance(v, (int, float)) else v


def by_album(tracks):
    albums = {}
    for t in tracks:
        albums.setdefault(t["albumName"] or "(no album)", []).append(t)
    rows = []
    for name, ts in sorted(albums.items(), key=lambda kv: -len(kv[1])):
        synced_ni = [t for t in ts if t["has_synced_lyrics"] and not t["instrumental"]]
        rows.append({
            "album": name,
            "track_count": len(ts),
            "pct_synced": pctof(sum(1 for t in ts if t["has_synced_lyrics"]), len(ts)),
            "pct_word_sync": pctof(sum(1 for t in ts if t["hasWordSync"]), len(ts)),
            "pct_instrumental": pctof(sum(1 for t in ts if t["instrumental"]), len(ts)),
            "median_lines_per_min": roundn(pct([t["lines_per_min"] for t in synced_ni], 0.5)),
            "median_onset_sec": roundn(pct([t["first_onset_sec"] for t in synced_ni], 0.5)),
        })
    return rows


def write_csv(path, cols, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: fmt_cell(r.get(c)) for c in cols})


def fmt_cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.2f}"
    return v


def write_report(path, artist, params_desc, agg, albums, tracks, stats):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    long_intro = sorted([t for t in tracks if (t["first_onset_sec"] or 0) > 20 and t["has_synced_lyrics"]],
                        key=lambda t: -(t["first_onset_sec"] or 0))
    missing = [t for t in tracks if not t["has_synced_lyrics"]]
    L = []
    L.append(f"# Music timestamp coverage — {artist}")
    L.append(f"\n_Generated {now} · source: LRCLIB (lrclib.net), free public API_\n")
    L.append("## Run parameters\n")
    L.append(params_desc + "\n")
    L.append("## Research questions this answers\n")
    L.append("1. **Sync coverage** — what share of the catalog has line-level synced lyrics vs word-level timing, per album?\n"
             "2. **Timing density** — synced lines per song and per minute (median / mean / p10 / p90)?\n"
             "3. **Vocal onset** — seconds to the first synced line; onset distribution; long instrumental intros (>20s)?\n"
             "4. **Duration distribution** — track-length spread and histogram; does length correlate with timing density?\n"
             "5. **Instrumental share** — fraction instrumental, and coverage once instrumentals are excluded?\n")

    L.append("## Headline numbers\n")
    L.append(f"- **Tracks matched:** {agg['total_tracks_matched']}")
    L.append(f"- **With synced (line-level) lyrics:** {agg['pct_with_synced_lyrics']}%  "
             f"(**{agg['coverage_adjusted_excl_instrumentals']}%** excluding instrumentals)")
    L.append(f"- **With word-level sync:** {agg['pct_with_word_sync']}%")
    L.append(f"- **Instrumental:** {agg['pct_instrumental']}%  ·  **plain-only:** {agg['pct_plain_only']}%  ·  **no lyrics:** {agg['pct_no_lyrics']}%")
    L.append(f"- **Lines per minute (synced):** median {agg['lines_per_min_median']} · mean {agg['lines_per_min_mean']} · p10 {agg['lines_per_min_p10']} · p90 {agg['lines_per_min_p90']}")
    L.append(f"- **Synced lines per song:** min {agg['synced_line_count_min']} · median {agg['synced_line_count_median']} · mean {agg['synced_line_count_mean']} · max {agg['synced_line_count_max']}")
    L.append(f"- **First-line onset (s):** median {agg['first_onset_sec_median']} · p90 {agg['first_onset_sec_p90']} · max {agg['first_onset_sec_max']}  ·  **long intros (>20s):** {agg['count_long_intro_gt20s']}")
    L.append(f"- **Duration (s):** min {agg['duration_sec_min']} · median {agg['duration_sec_median']} · mean {agg['duration_sec_mean']} · max {agg['duration_sec_max']}")
    L.append(f"- **Correlation (duration vs lines/min):** Pearson r = {agg['pearson_duration_vs_lines_per_min']}\n")

    L.append("## Duration histogram\n")
    for name, lo, hi in HIST_BUCKETS:
        c = agg[f"duration_hist_{name}"]
        label = {"lt120": "<2:00", "120_180": "2:00–3:00", "180_240": "3:00–4:00",
                 "240_300": "4:00–5:00", "300_plus": "5:00+"}[name]
        L.append(f"- {label:<9} | {'█' * c} {c}")
    L.append("")

    L.append("## Per-album coverage\n")
    L.append("| Album | Tracks | % synced | % word-sync | % instr. | median lines/min | median onset (s) |")
    L.append("|---|--:|--:|--:|--:|--:|--:|")
    for r in albums:
        L.append(f"| {r['album']} | {r['track_count']} | {r['pct_synced']} | {r['pct_word_sync']} | "
                 f"{r['pct_instrumental']} | {r['median_lines_per_min']} | {r['median_onset_sec']} |")
    L.append("")

    if long_intro:
        L.append("## Long instrumental intros (first lyric > 20s)\n")
        for t in long_intro[:15]:
            L.append(f"- **{t['trackName']}** — first line at {t['first_onset_sec']:.1f}s (duration {t['duration_mmss']})")
        L.append("")

    if missing:
        L.append(f"## Tracks without synced lyrics ({len(missing)})\n")
        for t in missing[:20]:
            L.append(f"- {t['trackName']} — _{t['lyric_status']}_")
        L.append("")

    L.append("## Data quality\n")
    L.append(f"- Lookup failures: {stats['lookup_failures']}")
    L.append(f"- Unresolved tracks: {stats['unresolved_tracks']}")
    L.append(f"- Duplicate ids collapsed: {stats['duplicate_id_collisions']}")
    L.append(f"- Non-matching artist records dropped (discovery): {stats.get('dropped_non_matching_artist', 0)}")
    L.append("\n> ⚠️ LRCLIB search is capped at 20 non-paginated results, so broad-artist runs are "
             "under-sampled — use `--album` or `--tracks` for fuller coverage. LRCLIB is community data, "
             "so duplicates/mislabels exist; instrumentals are excluded from density denominators.")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Audit synced-lyric (timestamp) coverage for an artist via LRCLIB.")
    ap.add_argument("--artist")
    ap.add_argument("--album")
    ap.add_argument("--tracks")
    ap.add_argument("--duration-hint", type=int)
    ap.add_argument("--max-results", type=int, default=20)
    ap.add_argument("--out-dir", default="./out")
    ap.add_argument("--user-agent", default=DEFAULT_UA)
    ap.add_argument("--delay", type=float, default=0.3)
    a = ap.parse_args()

    if not a.artist and not a.tracks:
        ap.error("provide --artist and/or --tracks")
    os.makedirs(a.out_dir, exist_ok=True)
    stats = {"lookup_failures": 0, "unresolved_tracks": 0,
             "duplicate_id_collisions": 0, "dropped_non_matching_artist": 0}

    queries = []
    raw = []
    if a.tracks:
        pairs = parse_tracks_file(a.tracks, a.artist or "")
        queries.append(f"track-list ({len(pairs)} tracks) from {a.tracks}")
        print(f"Resolving {len(pairs)} tracks from {a.tracks} ...", flush=True)
        seen = set()
        for art, title in pairs:
            rec = resolve_track(art, title, a.album, a.duration_hint, a.user_agent, a.delay, stats)
            if not rec:
                stats["unresolved_tracks"] += 1
                print(f"  · unresolved: {art} - {title}", flush=True)
                continue
            if rec.get("id") in seen:
                stats["duplicate_id_collisions"] += 1
                continue
            seen.add(rec.get("id"))
            raw.append(rec)
            print(f"  · {rec.get('artistName')} - {rec.get('trackName')} (id {rec.get('id')})", flush=True)
    else:
        queries.append(f"search q={a.artist!r}" + (f" + album={a.album!r}" if a.album else ""))
        print(f"Searching LRCLIB for {a.artist!r} ...", flush=True)
        raw = discover(a.artist, a.album, a.max_results, a.user_agent, a.delay, stats)
        print(f"  kept {len(raw)} records (dropped {stats['dropped_non_matching_artist']} non-matching).", flush=True)

    artist_label = a.artist or (raw[0].get("artistName") if raw else "tracklist")
    tracks = [track_metrics(r) for r in raw]

    agg = aggregate(tracks)
    agg["lookup_failures"] = stats["lookup_failures"]
    albums = by_album(tracks)

    slug = re.sub(r"[^\w]+", "_", (artist_label or "artist").lower(), flags=re.UNICODE).strip("_") or "artist"
    tracks_csv = os.path.join(a.out_dir, f"{slug}_tracks.csv")
    summary_csv = os.path.join(a.out_dir, f"{slug}_summary.csv")
    album_csv = os.path.join(a.out_dir, f"{slug}_by_album.csv")
    report_md = os.path.join(a.out_dir, f"{slug}_report.md")

    write_csv(tracks_csv, TRACK_COLS, tracks)
    write_csv(summary_csv, ["metric", "value"], [{"metric": k, "value": v} for k, v in agg.items()])
    write_csv(album_csv, ["album", "track_count", "pct_synced", "pct_word_sync",
                          "pct_instrumental", "median_lines_per_min", "median_onset_sec"], albums)

    params_desc = (f"- Artist: **{artist_label}**\n- Queries: {'; '.join(queries)}\n"
                   f"- Max results: {a.max_results}\n- User-Agent: `{a.user_agent}`")
    write_report(report_md, artist_label, params_desc, agg, albums, tracks, stats)

    # stdout headline
    print("\n=== Headline ===", flush=True)
    print(f"matched={agg['total_tracks_matched']}  synced={agg['pct_with_synced_lyrics']}% "
          f"(excl-instr {agg['coverage_adjusted_excl_instrumentals']}%)  "
          f"word-sync={agg['pct_with_word_sync']}%  instrumental={agg['pct_instrumental']}%", flush=True)
    print(f"lines/min median={agg['lines_per_min_median']}  onset median={agg['first_onset_sec_median']}s "
          f"(p90 {agg['first_onset_sec_p90']}s)  long-intros={agg['count_long_intro_gt20s']}", flush=True)
    print(f"\nWrote:\n  {report_md}\n  {tracks_csv}\n  {summary_csv}\n  {album_csv}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
