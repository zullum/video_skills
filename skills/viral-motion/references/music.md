# Music: free, local, timed

ACE-Step 1.5 (MIT) runs on this computer: Apple Silicon (MPS + MLX), NVIDIA (CUDA), or CPU (slow).
The turbo model makes a 40 s take in well under a minute on an M-series Mac once loaded. Disk: about 11 GB
of models + its Python environment. Already installed here; `scripts/check.sh` verifies it (path saved in `SKILL/.acestep`).

## audio/song.json

| field | meaning |
|---|---|
| `mode` | `"song"` (vocals; ranked on lyrics) or `"score"` (instrumental story score; ranked on the arc) |
| `caption` | the sound, most important words first: genre, BPM, vocal (or "instrumental"), instruments, production, energy arc in time order. The examples are 450-900 characters. |
| `lyrics` | `[section]` tags + lines. Score mode: tags with directions (`[Intro - solo soft piano, no drums]`), optionally a short wordless chant at the drop |
| `instrumental` | `true` forces no vocals |
| `language` | the vocal language as an ACE-Step code: `en` (default), `hr`/`sr` for Bosnian/Croatian/Serbian (there is no `bs`). stems.sh forces whisper to it |
| `bpm`, `timesignature` | the requested tempo (also the hint for the beat tracker) |
| `duration` | target length + 2-4 s (takes often end early; trim to the musical end later) |
| `target_duration` | the length you need; takes whose music ends before it are penalised |
| `seeds` | 4 per round; use NEW seeds for a new round (the same seed gives back the same take, bit for bit) |
| `drop_window`, `arc` | score mode: where the drop should be, and the target loudness curve `[[t, 0..1], ...]` |
| `fps` | envelope rate in timing.json (30, or 60 for 60 fps pieces) |
| `lm` | `acestep-5Hz-lm-0.6B` (fits 16 GB, the default) or `acestep-5Hz-lm-1.7B` (32 GB+) |

### Writing a song that sings back right
- Short lines, simple words, a hook repeated 3+ times, one idea per line. Tongue-twisters come back as mush.
- Ask for clarity in the caption: "clear lead vocal, every word crisp and intelligible".
- Heavily processed sections (vocoder, chops) won't transcribe. That's fine: timing.py fills them from onsets and flags them.
- Score mode: describe contrast explicitly ("the first fifteen seconds are only a soft, lonely solo piano: no drums,
  no bass, very quiet" … "a breakdown: everything drops out except a riser" … "then the drop hits at full power").
  Models default to "loud all the way through" unless told otherwise.

## The commands

```bash
bash   SKILL/scripts/music/run_music.sh <project>                    # 4 takes → audio/takes/seed*.wav (waits for the lock)
bash   SKILL/scripts/music/stems.sh <project> seed11 seed23 ...      # song mode: stems + whisper vocal-stem transcript per take
SKILL/scripts/py SKILL/scripts/music/rank_takes.py <project>         # ranking table + audio/takes/ranking.json (rejects lost lines)
SKILL/scripts/py SKILL/scripts/music/timing.py <project> --take seed23   # audio/timing.json + assets/js/timing.js
bash   SKILL/scripts/music/trim.sh <project>/audio/takes/seed23.wav <duration> <project>/assets/audio/song.wav
```
Run `run_music.sh` in the background for long rounds and poll the log (`audio/gen.log`). Use absolute paths in
background commands.

## Why it's built this way (lessons that cost a debug round each)

- **Two processes.** On 16 GB, loading the model AND decoding audio in one process gets killed (exit 137). `gen_song.py`
  saves latents, and `decode_latents.py` decodes them in a fresh process with only the VAE loaded. The bf16 patch halves
  the model's memory on Apple GPUs.
- **Keep ~10 GB of disk free while generating.** Loading the model pushes a 16 GB machine into swap. With too little free
  disk macOS can't grow swap and the whole computer restarts (this happened twice, at 0.3 GB and 4 GB free). run_music.sh
  refuses to start below 10 GB free (`MOTION_STUDIO_FORCE=1` overrides it on 32 GB+ machines). Check song.json without
  loading anything: `cd <ACE-Step> && MOTION_STUDIO_DRY_RUN=1 uv run python SKILL/scripts/music/gen_song.py <project>`.
- **One music job per machine.** Two generations at once run out of memory. `run_music.sh` takes a lock in
  `~/.motion-studio/acestep.lock` (stale locks from dead processes are cleared automatically), so parallel chats wait in line.
- **Placeholder WAVs.** ACE-Step writes a silent UUID-named WAV per take. run_music.sh deletes them.
- **Rank on the vocal stem.** Full-mix transcription misranks takes (the music drowns the words).
- **Check the musical end.** One take scored 0.83 on lyrics but its music stopped at 29 s of 38. rank_takes.py
  reports `musical_end` (still audible) and `sustain_end` (band still really playing) and penalises early endings.
- **Recognisers mishear sung words** ("vibe" → "eye", "render" → "Brenda", "type it out, hit enter" → "something else
  should insert"). timing.py aligns the lyric sheet to what was heard **in order**, so misheard words keep their time.
  Unheard lines are mapped onto the leftover tokens or the vocal onsets, phrase by phrase, and flagged with `*`.
- **Word times come from whisper's DTW.** stems.sh runs the user's whisper.cpp large-v3-turbo on the vocal stem with
  `-nfa --dtw` (flash attention silently turns DTW off), the language forced and no lyric prompt; whisper_to_transcript.py
  takes each word's DTW time minus 0.3 s (whisper's late bias on singing). Mean onset error 0.27 s, against 1.19 s for
  `hyperframes transcribe`, which reads token offsets. Auto-detect heard "Music Outro"; a lyric prompt echoes unsung lines.
- **A take that loses a line is rejected.** rank_takes.py rejects a take if any lyric line has no word heard exactly or
  nearly: one take sang the verse twice instead of the Chorus, and the video would show words nobody sings.
- **Seeds are exact.** gen_song.py seeds the MLX LM per take and turns off ACE-Step's caption and language rewriting
  (on by default; it turned "female lead vocal" into "male vocal").
- **Bosnian/Croatian/Serbian songs mostly fail.** A Croatian take was only partly intelligible, and on its vocal stem
  whisper heard only "hvala to pratite" (a stock hallucination). Warn the user and offer their own song early.
- **The drop decides the downbeat.** Kick-based downbeat guessing gets breakbeats wrong by two beats. timing.py anchors
  the bar on the drop (the sharpest rise into the loudest sustained section).
- **ACE-Step doesn't hit the requested BPM exactly** (140 → 139.7-140.0). Always use the measured grid.
- Don't download other models or edit ACE-Step's code beyond the shipped patch.

## The user's own Track

Music the user owns (any WAV/MP3): a song plus its lyrics as text (Lyric video) or an instrumental (Story film). It's
also the way out when the music model can't run (not enough disk, an old machine). No Takes, no ranking, no Checkpoint 2.

1. `bash SKILL/scripts/music/own_track.sh <project> <file> <video-seconds>` → `audio/takes/own.wav`. **Exit 3 is a stop**:
   the file is shorter than the video. Tell the user exactly that and wait for a new file.
2. song.json: `mode`, `language`, `bpm` if known, and for a song the `lyrics` sung inside the video length only
   (timing.py lists any later line as unsung).
3. A song: `stems.sh <project> own`. Then `timing.py <project> --take own --end <video-seconds>`.
4. `trim.sh <project>/audio/takes/own.wav <video-seconds> <project>/assets/audio/song.wav 2` (a 2 s fade). A longer
   Track cut this way is a soft flag: report it at delivery.
