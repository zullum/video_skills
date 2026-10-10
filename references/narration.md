# Narration: English Kokoro, ducking and the mix gate

Generated Narration is English only: Kokoro-82M, local and free. It does not speak Bosnian/Croatian/Serbian; for
those, the Narration is the user's Recording (`references/recording.md`), or the video uses on-screen text only.
Never use /media-use for voice: it has Gemini TTS paths.

## One line per Shot

```bash
SKILL/scripts/hf tts "<line>" -v af_heart -o <project>/audio/narration/s03.raw.wav --json    # → durationSeconds
mkdir -p <project>/assets/audio/narration
ffmpeg -v error -y -i <project>/audio/narration/s03.raw.wav -af "pan=stereo|c0=c0|c1=c0,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 48000 -c:a pcm_s24le <project>/assets/audio/narration/s03.wav
```

- `hf tts` runs Kokoro in the skill's Python 3.12 venv (it sets `HYPERFRAMES_PYTHON` itself). A warm call takes
  ~2-4 s per line; `check.sh` verifies the model and voices are downloaded.
- Voices: `af_heart` (best), `af_bella`. Avoid `am_adam`. `-s` sets the speed.
- Kokoro writes 24 kHz mono. The ffmpeg step makes it stereo (a mono stem plays 3 dB louder than it measures) at
  about -16 LUFS; short lines land at -16 to -18 because the peak ceiling wins. The mix gate judges the total.
- Kokoro gives no word timings: a line's length is its `durationSeconds`.

## The fit rule

lead (0.25-0.4 s) + `durationSeconds` + tail (at least 0.4 s) must fit inside the Shot. If it doesn't, in this
order: shorten the line, then speed it up (`-s` up to 1.15), then (Story film only) extend the Shot and re-time
what follows. Merge lines shorter than ~10-20 tokens into a neighbour.

Place each line at its Shot: `<audio id="nar-s03" src="assets/audio/narration/s03.wav" data-start="<Shot start +
lead>" data-duration="<durationSeconds>">`. Every `<audio>` needs an `id`.

## Ducking

The Score dips -10 dB under every spoken span: down in 150 ms ending AT the first syllable, back up over 400 ms.
`duck_lane.py` measures the spans from the voice files and prints a `data-automation` volume lane:

```bash
SKILL/scripts/py SKILL/scripts/sfx/duck_lane.py assets/audio/narration/s01.wav@0.35 assets/audio/narration/s02.wav@4.2 \
  --base <the Score's data-volume>                      # one item per line: file@data-start
```

Paste the JSON as the Score's `data-automation` attribute. Once a lane exists the renderer ignores `data-volume`,
so `--base` must be the Score's normal volume, and lane values stay at or below 1.

## The mix gate

Targets: the final mix at -14 LUFS ±1 with true peak at or below -1 dBTP. The Score sits around -16 LUFS under
Narration (about -14.5 when the music leads), and Narration at -16. Before rendering, from the project folder:

```bash
SKILL/scripts/py SKILL/scripts/qa/mix_check.py index.html --out renders/mix_sim.wav
```

It rebuilds the renderer's mix from the `<audio>` tags (volume, lane, fades, start, all summed with no limiter),
measures it, and prints the trim that hits the target: PASS, or FAIL when peaks block the target (lower the
hottest stem). It ignores `<hf-audio-group>` effects such as the SFX limiter, so with a group it may read a little
hot. The Critic only sees frames, so these numbers are the mix's check: never skip it.
