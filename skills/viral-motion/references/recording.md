# Recording: the user's own voice, Shots cut to it

Story film only. The user reads the approved Narration script into a phone memo, in any language (this is how
Bosnian/Croatian/Serbian Narration is done). The timing is **voice-led**: Shot times come from the Recording, and
the Score is generated afterwards to fit it.

## The memo

At Checkpoint 1 the user gets the Narration script and how to record it: a phone memo in a quiet room, no music or
TV underneath, ~1 s pause between lines, read as written. They send a file path (m4a, mp3, wav or aiff).

## The command

1. Write the approved Narration script to `<project>/audio/recording/script.txt`: one script line per text line,
   exactly as approved. Lines are the units the Shots are cut on.
2. Run it (once warm, ~6 s per 24 s of speech; a cold model load adds 10-15 s):
   ```bash
   bash SKILL/scripts/recording/pipeline.sh <memo> <project>/audio/recording/script.txt <project>/audio/recording <lang>
   ```
   `<lang>` is the script's language: `hr` for any Bosnian/Croatian/Serbian (it measured better than `bs`/`sr`),
   `en` for English. Whisper is the user's build (large-v3-turbo with DTW; `-nfa` is mandatory and VAD stays off).
3. `audio/recording/` then holds `source.<ext>` (untouched), `clean.wav` (trimmed, de-noised, 48 kHz stereo at
   -16 LUFS: the mix stem), `recording.json`, and whisper's files and logs.

## Exit 3 is a hard fail: stop

The `HARD FAIL` line says which of the two it is:
- **"sounds like 'xx' but -l is 'yy'"**: if you passed the wrong `<lang>`, rerun with the right one. Otherwise
  the user recorded in another language than the script. A faithful translation can still pass the word match,
  because whisper translates into the forced language, so this check uses whisper's own language ID.
- **"only N% of the script heard clearly"** (under 70%): a different text, music under the voice, noise, or a
  whisper loop.

Tell the user exactly what's wrong (quote the line) and wait for a new file. Never cut Shots from a failed Recording.

## Chants and repeated lines: write the script as sung, and check the Shots

The script is also whisper's prompt, and a repetitive text (a children's alphabet song: "Slovo A. A kao auto. A, a,
auto. A kao auto.") makes whisper unstable: the same memo gave 88%, 13% and 11% "heard" for three near-identical
scripts. What worked (first real Recording, 2026-10-12):
- List every repeat exactly as sung, one script line per section, and no more than was sung. Extra or missing
  repeats shift the in-order alignment: one stutter ("Č, č, čokolada") pushed the next line's start 4 s early
  with a PASS.
- After a pass, always compare each line's `start` with whisper's raw DTW onsets of its first word
  (`whisper.json`, `t_dtw` / 100 s, minus ~0.12): a PASS with low-confidence (`*`) words in the last lines means
  the Shots may be wrong, and the user's ear is the judge.
- A short memo (under ~30 s) of a sung or chanted text may need `-l hr` with a separated vocal stem
  (`python -m demucs --two-stems vocals`, the ACE-Step venv has it): whisper on the full mix heard only
  "Hvala što pratite".

## Soft flags: carry on, report at delivery

`recording.json` `flags` (also printed):
- `line N NOT FOUND`: a skipped line. It gets no Shot; keep it as on-screen text or drop it.
- `unscripted speech '...'`: fillers, ad-libs, retakes.
- a word with `conf` < 0.35: mumbled or misheard. Its time is interpolated from its neighbours.
- Shot splits (over 5 s, at the best pause) and merges (under 1.2 s).

## recording.json → the Beat sheet

`{duration, lufs, language, heard_share, hard_fail, lines: [{i, text, start, end, missing, words: [{text, start,
end, heard, src, confidence}]}], shots: [{i, start, end, line_ids, note?}], flags}`. Times are seconds on
`clean.wav`'s timeline.

- **Shots**: each starts 0.3 s before its line (the cut lands just ahead of the voice) and ends where the next
  begins. The first starts at 0; the last ends at the end of `clean.wav`. Re-time the Beat sheet to them: one
  `## Frame N` per `shots[]` entry. An end card after the voice extends the film; add it as a last Shot.
- **Words**: `lines[].words` times are good to ~30-40 ms at line starts (tested on synthetic voices; the first
  real Recording validates it), so word-by-word captions can use them.
- **The voice in index.html**: copy `clean.wav` to `assets/audio/voice.wav` and place it at the film's start:
  `<audio id="voice" src="assets/audio/voice.wav" data-start="0" data-duration="<duration>">`.

## The Score, after the Recording

song.json `duration` = the film length (voice + end card) + 2-4 s, `target_duration` = the film length, and
`drop_window` around the climax Shot's start. Then Takes, ranking and Checkpoint 2 as usual. Shot times stay on the
voice: land the climax visuals on `drop` inside the climax Shot instead of moving the cut.

## Mix

Duck the Score under the voice (it is already -16 LUFS stereo), then run the mix gate. Both are in
`references/narration.md` (Ducking and the mix gate); for a Recording the duck is
`duck_lane.py <project>/assets/audio/voice.wav --at 0 --base <the Score's data-volume>`.
