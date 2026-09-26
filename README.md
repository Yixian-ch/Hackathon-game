# Muso

**Team: CC's music**

**Play it now: https://muso-brown.vercel.app** (desktop Chrome with keyboard, or a phone in landscape)

Muso is a browser rhythm runner that turns *any* song into a level. Drop in an MP3, and a
signal-processing pipeline listens to the track, finds the beats, and builds a chart in a
few seconds: no hand-made levels, no server needed to play. The whole game is one HTML
file drawn entirely in code, in a street-sticker / printed-comic style.

## How to play

- **↓ (or F)** hits ground enemies, **↑ (or J)** hits air enemies. On a phone (landscape), tap the
  left half of the screen for ↓ and the right half for ↑; the pause sticker sits top-right. Hold
  notes are held until the bar ends, mash monsters take repeated presses, ghosts turn invisible
  mid-flight, so keep the beat.
- **Four difficulties**: Easy, Normal, Hard, Expert. Expert unlocks per song once you have
  finished that song on Hard, and it is the only difficulty where **bosses** appear: two or three
  times per song a boss floats in and summons waves of enemies; clearing at least 80% of a wave
  costs it one HP, and if its HP is empty when the song ends it is defeated and added to your
  collection (escapes are recorded too).
- **Fever**: Perfects fill a gauge (+3, Goods +1). When it fills, fever runs for 8 beats: every hit
  in the Good window counts as Perfect and all score is doubled.
- **Scoring and grades**: Perfect 100, Good 50, Miss 0, times a combo multiplier (+0.1× every 20
  hits, up to 2.0×). Pressing with no enemy in range breaks the combo (off on Easy).
  Accuracy = (Perfect + 0.5 × Good) / notes. **SSS** = 100% with no Miss, **S** ≥ 90%, **A** ≥ 80%,
  **B** ≥ 70%, **C** below. A run with zero Misses also earns the FULL COMBO sticker.
  Esc pauses.

## Quick start

- Open **https://muso-brown.vercel.app** (or the itch.io page), or
- double-click `index.html`. The three bundled songs load from `songs/`, and you can upload your
  own MP3 / WAV / OGG from the "+ UPLOAD YOUR SONG" record.

No install, no build step, no key: everything runs offline in the browser. The "✦ GENERATE A
SONG" record is a placeholder (see Architecture).

## Architecture

```
┌──────────────────────────────────────────────┐
│  Browser: index.html (single file)           │
│  Canvas 2D rendering · Web Audio analysis    │
│  chart generation · gameplay · localStorage  │
└───────────────┬──────────────────────────────┘
                │ planned, only for "Generate a song"
                ▼
┌──────────────────────────────────────────────┐
│  Local proxy (Node) holding the API key      │
└───────────────┬──────────────────────────────┘
                ▼
┌──────────────────────────────────────────────┐
│  Gemini API · Lyria 3.5 (music generation)   │
└──────────────────────────────────────────────┘
```

Today the game is the top box only. Song generation is designed as an add-on behind a small
server-side proxy, so the API key never reaches the page and the browser never calls Google
directly; the generated audio would then go through the same analysis pipeline as an uploaded
file. In the current build the GENERATE record calls the `onGenerateSong()` hook, which is a
stub, so the game never needs a key or a server.

## Chart generation

Every level is generated offline from the decoded audio before play starts, and printed to the
console as `{ bpm, notes, sections }` for inspection.

1. **Onset detection.** The track is down-mixed to mono and framed (2048-sample FFT, 20 ms hop).
   Each spectrum is pooled into **48 log-spaced bands** (40 Hz to 16 kHz), log-compressed, and the
   half-wave-rectified **spectral flux** across bands gives the onset strength. Pooling into bands
   keeps a kick from being outvoted by a thousand high-frequency bins of hi-hat.
2. **Adaptive peak picking.** A frame is an onset if it beats both neighbours and a sliding
   threshold of mean + k·std over ±0.5 s, plus an absolute floor that ignores near-silence.
3. **Sample-level refinement.** A flux peak only says "somewhere in this frame". Each onset is
   refined by finding the steepest energy rise of the pre-emphasised signal in 1.5 ms blocks
   around the frame, which puts enemies within about 1 ms of the drum hit.
4. **Tempo.** Autocorrelation of the onset curve (60 to 180 BPM, mild prior around 120) gives a
   coarse tempo; a comb search over the onset times refines it to 0.01 BPM. Onsets are snapped to
   a **half-beat grid** whose phase is estimated per section, and an onset that sits more than
   70 ms off the grid keeps its detected time (syncopation is preserved, not quantised away).
5. **Lanes.** The spectral centroid of the onset frame splits ground (low) from air (high) at the
   song's median centroid, so each track gets a balanced split. The strongest onsets become
   double hits on both lanes.
6. **Density control.** Strongest onsets are kept first under three limits: max two enemies per
   timestamp, a per-second cap, and 80 ms between enemies on the same lane.
7. **Section intensity.** The song is cut into ~12 s sections; mean onset strength, normalised to
   0–1, drives the difficulty curve (low-intensity sections halve the density cap), the boss
   placement (Expert), and the background atmosphere. The intensity → density mapping is a single
   function so it can later be replaced by a learned curve.
8. **Note types.** Taps followed by a gap on their lane become hold bars; strong onsets in lively
   sections become mash monsters that clear their window of other enemies; some single taps
   become ghosts. All choices are seeded per song, so a chart is reproducible.

| Difficulty | Onset threshold k | Max / second | Double hits | Perfect / Good | Empty-press penalty | Holds | Ghosts | Monster every | Bosses |
|---|---|---|---|---|---|---|---|---|---|
| Easy   | 1.30 | 3 | none    | ±80 / ±160 ms | off | 35% | 0%  | 30 s | no |
| Normal | 1.25 | 3 | top 3%  | ±60 / ±140 ms | on  | 35% | 5%  | 30 s | no |
| Hard   | 0.95 | 6 | top 8%  | ±50 / ±120 ms | on  | 45% | 20% | 20 s | no |
| Expert | 0.70 | 8 | top 10% | ±50 / ±120 ms | on  | 50% | 30% | 18 s | yes, unlocked by finishing Hard |

All of these live in one `DIFFICULTY` object; the analysis constants live in `ANALYSIS`.

## APIs, frameworks and tools

| Component | Used for |
|---|---|
| Web Audio API | Decoding audio, offline analysis, sample-accurate playback clock (`audioContext.currentTime`) |
| Canvas 2D | All rendering; every sprite, texture and UI element is drawn in code |
| Gemini API / Lyria 3.5 | Planned: song generation behind a local proxy (not in this build) |
| Node.js | Planned: the proxy that keeps the API key server-side (not in this build) |
| localStorage | Best scores per song and difficulty, boss collection, uploaded-song metadata, settings |
| Vercel | Hosting of the live build (static, no build step): https://muso-brown.vercel.app |
| itch.io | Distribution of the HTML5 build |
| Claude Code | AI-assisted development: the code, art pass and tests were written with Claude Code as a pair programmer (matching the AI disclosure on the itch page) |
| ffmpeg | Transcoding the bundled songs to MP3 |

No game framework, build tool or npm dependency is used by the game itself.

**Music**

| Track | Source | License |
|---|---|---|
| Belle U | _fill in_ | _fill in_ |
| Bocci | _fill in_ | _fill in_ |
| Metro | _fill in_ | _fill in_ |

## Project structure

```
index.html          the whole game, in four commented blocks:
                    (0) art constants: PALETTE and STYLE
                    (1) audio analysis and chart generation
                    (2) game state, judgment, scoring, fever, bosses
                    (3) rendering: textures built once, sticker art, HUD, results
                    (4) song library, vinyl song-select, input
songs/              bundled songs plus songs/<file>.js base64 bundles for double-click play
tools/bundle_songs.py  regenerates those bundles after adding or replacing a song
vercel.json, .vercelignore   static deployment config for Vercel (songs get immutable cache headers)
```

## Performance

Steady 60 fps at 1280×720: all timing comes from `audioContext.currentTime` (no timers, no
frame counting), only enemies inside the visible time window are touched each frame, every
texture and pattern is generated once at start-up into offscreen canvases, and there is no
`shadowBlur` anywhere. Measured render cost in the densest Expert section with fever and a boss
on screen is about 1.3 ms of JavaScript per frame.

## Known limitations and roadmap

- **iOS / Safari**: audio needs a user gesture (handled), but iOS was not tested in depth and
  large uploads may hit memory limits on older devices.
- **Mobile**: the 1280×720 stage is scaled to fit the window and gameplay has left/right tap
  zones, but only landscape is laid out (portrait shrinks the stage), and phones were tested in
  Chrome's device emulation rather than on a wide range of real devices.
- **Bundled songs on `file://`**: Chrome blocks `fetch` for double-clicked pages, so bundled
  songs load from base64 `.js` bundles instead (about 1.33× the audio size); over http(s) and on
  itch.io they load directly.
- **Song generation** is not implemented: the GENERATE record shows COMING SOON and calls the
  `onGenerateSong()` hook.
- **Chart quality** is best on music with clear drums. Ambient or heavily swung material can get
  a half-tempo estimate or sparse charts; a tempo override is on the list.
- Not built yet: a chart editor, sharing charts and scores with other players, more boss types,
  and a proper mobile layout.

Where this is going: Muso treats a song as input, not content to be authored. The next steps are
letting players tune the generated chart, sharing the result as a small JSON, and using the
section-intensity curve as the seam where a learned difficulty model can plug in.
