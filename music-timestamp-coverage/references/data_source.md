# LRCLIB — data source reference

Primary source: **LRCLIB** (https://lrclib.net) — a free, open-source, public lyrics
database. **No API key, no account.** CORS-open. All responses are JSON, UTF-8.
REST base: `https://lrclib.net/api`. (Verified live 2026-09-30.)

## Endpoints
- `GET /api/get` — params: `artist_name` (req), `track_name` (req), `album_name`
  (opt), `duration` (opt, **seconds** int). With `duration`, only returns a track
  within ~±2s (fuzzy; a wrong/rounded value can 404 even when the track exists —
  retry without duration). Returns ONE best-match object, or **HTTP 404** JSON
  `{"message":"Failed to find specified track","name":"TrackNotFound","statusCode":404}`.
- `GET /api/get/{id}` — `{id}` = integer record id from any response. Returns that
  exact record, or 404 TrackNotFound.
- `GET /api/search` — EITHER `q=<free text>` (fuzzy over title+artist+album) OR
  structured `track_name=&artist_name=&album_name=` (`track_name` effectively
  required). Returns a JSON **array** (same shape as `/api/get` plus `lyricsfile`),
  **hard-capped at 20, not paginated**. No match = empty array `[]` with HTTP 200
  (NOT 404). Prefer `/api/get` when you have a confident artist+title; use search for
  discovery.

## Fields
- `id` — int primary key; stable; re-fetch via `/api/get/{id}`.
- `name` / `trackName` — track title (duplicates; prefer `trackName`). Any script
  (Cyrillic/CJK); may be mislabeled.
- `artistName` — free text; may bundle features; cover/karaoke channels appear here
  (a common duplicate/mislabel source).
- `albumName` — often **empty** for singles & uploads. Never require it for a match.
- `duration` — length in **seconds** as a float (e.g. `239.0`), **not** ms. Nullable.
  This is what `/api/get`'s `duration` matches against (±~2s).
- `instrumental` — bool; `true` ⇒ `plainLyrics` and `syncedLyrics` are both null. A
  metadata flag, not a guarantee of silence.
- `hasWordSync` — bool; `true` ⇒ word-level timing exists in the newer `lyricsfile`
  `lines[]` array. Rare. Independent of `syncedLyrics`; does not affect the
  `[mm:ss.xx]` line timestamps.
- `syncedLyrics` — **line-level** LRC string, lines joined by `\n`, each
  `"[mm:ss.xx] text"`. **Primary timestamp source.** `null` when only plain lyrics
  exist or the track is instrumental. A line may carry a timestamp with empty text
  (trailing end marker, e.g. `"[03:50.78] "`).
- `plainLyrics` — un-timed `\n`-joined lyrics; fallback when `syncedLyrics` is null;
  null for instrumentals.
- `lyricsfile` — newer YAML doc: metadata (`duration_ms` is **milliseconds** here),
  `lines[]` (populated only when `hasWordSync=true`), `plain:`. Use `syncedLyrics` for
  line timing; `lyricsfile.lines` only for word-level.

## Parsing the synced LRC
Split `syncedLyrics` on `\n`. Per-line regex:
`^\[(\d+):(\d{2})(?:[.:](\d{1,3}))?\]\s?(.*)$` — the bracket is `[mm:ss.xx]` where
`xx` is **centiseconds** (2 digits); some sources use 3-digit milliseconds, so parse
the fractional field **by its own length**:
`onset = mm*60 + ss + frac/(10**len(frac_digits))`. Skip ID-tag lines
(`[ar:]`,`[ti:]`,`[al:]`,`[length:]`,`[by:]`,`[offset:]`). Count sung lines as regex
matches with non-empty text (exclude blank-text end markers). First onset = min of
matched onsets (LRCLIB emits them ascending).

## Etiquette & limits
No key. Send a descriptive **User-Agent** with app + contact, e.g.
`music-timestamp-coverage/1.0 (student coursework; contact: bigstupidtech@gmail.com)`.
Serialize requests, add a small delay, cache by id, prefer one `/api/get` over
repeated `/api/search`. Cloudflare-fronted; on **HTTP 429** read `Retry-After` and
back off (exponential on repeats).

## Gotchas
- Search capped at 20, not paginated — make queries specific.
- No-match differs: `/api/search` ⇒ `[]` (200); `/api/get` ⇒ 404 TrackNotFound.
- `duration` is seconds (float, nullable); `lyricsfile.duration_ms` is milliseconds —
  don't mix.
- `/api/get` duration match is fuzzy ±2s — on 404 retry without duration or use search.
- Rampant duplicates/mislabels (covers, karaoke, remixes, re-uploads). Disambiguate by
  duration proximity + album + non-null `syncedLyrics` + `artistName` containing the
  real artist.
- `instrumental=true` (or simply no sync) ⇒ `syncedLyrics` null; always null-check.
- `hasWordSync` is almost always false; line timing lives in `syncedLyrics` regardless.
- Everything is UTF-8 (Cyrillic/CJK). URL-encode params and treat all strings as UTF-8.

## Fallback sources (metadata only — none provide synced lyrics)
- **MusicBrainz** — canonical durations + metadata. `GET https://musicbrainz.org/ws/2/recording?query=...&fmt=json`. Strict ~1 req/sec, **requires** a descriptive User-Agent with contact. `length` is in **milliseconds**.
- **Deezer** — `GET https://api.deezer.com/search?q=...` (JSON; `duration` in **seconds**). No auth.
- **iTunes Search** — `GET https://itunes.apple.com/search?term=...&entity=song` (JSON; `trackTimeMillis` in **ms**). No auth.
