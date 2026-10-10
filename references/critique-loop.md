# The critique loop (the Crew's side)

What separates a finished video from a one-shot: the work is graded and fixed before the user sees it. The Crew never
grades its own work. A **fresh Critic agent** does, every round, from pictures only; `references/critic.md` is its
prompt and its rubric. You capture, spawn, read, fix and stop.

## When

- Rounds start after the full animation pass, sound + mix and `hf check` with 0 errors (SKILL.md §4). Level 3's
  "stills first" step comes earlier and is yours alone: snapshot a key frame per Shot, look, fix. No Critic, no Grades.
- Round limits: level 1: 1 round, level 2: 3, level 3: 4. Then render, `av_check`, and the final pass on the MP4.
- Level 3, before every round, run the animation map and remove the dead zones (stretches where nothing meaningful
  moves) it finds in DOM Shots:
  `node ~/.claude/skills/hyperframes-animation/scripts/animation-map.mjs <project>` (or under `~/.agents/skills/...`).
  It can't see inside a canvas; the Critic judges canvas Shots from their frames.

## Each round (N = 1, 2, …)

1. **Capture** into `critique/round-N/`:
   `SKILL/scripts/hf snapshot <project> --at <t1>,<t2>,... --no-end -o <project>/critique/round-N`
   It writes `frame-NN-at-<t>s.png` per time plus `contact-sheet*.jpg`. The times, in global seconds:
   - every Shot: its start (+0.2-0.3 s, past the incoming transition), its middle, its end (-0.1 s);
   - the key moments: word onsets (level 2: the first word of every lyric line and every hook word), the turn, the
     drop, the end card;
   - every hit (the drop, impacts, slams, cuts on downbeats, the `av_check --expect` times) plus the frame before it
     (t - 1/fps).

   Keep it under ~60 frames. On a long video, thin out the word onsets first, never the hits.
2. **Label** them in `critique/round-N/frames.md`, one row per frame, in time order. The Critic knows a frame only
   by its row: say what it is, not what you hope it shows.

   ```markdown
   | file | t (s) | Shot | what |
   |---|---|---|---|
   | frame-07-at-14.2s.png | 14.20 | F4 writer | middle |
   | frame-12-at-21.34s.png | 21.34 | F5 chorus | word "enter" t=21.34 |
   | frame-31-at-49.998s.png | 49.998 | F11 climax | before hit: drop 50.031 |
   | frame-32-at-50.031s.png | 50.031 | F11 climax | hit: drop 50.031 |
   ```
3. **Spawn a fresh Critic**: a new agent every round (the Agent tool, general-purpose type, the session's model),
   never a resumed one, never yourself. Its prompt is exactly this, with absolute paths:

   ```
   You are the Critic. Read <SKILL>/references/critic.md and follow it exactly.
   Project: <project>
   Level: <1|2|3> <Showreel|Lyric video|Story film> · Round: <N> of <max>
   Frames: critique/round-N/frames.md
   Previous round: critique/round-<N-1>.md   (round 1: none)
   Write critique/round-N.md and nothing else.
   ```

   Add nothing: no code, no account of what you fixed or meant, no Grades you expect. The intent docs speak for you.
4. **Read** `critique/round-N.md`. Don't argue with a Grade. If a frame misled the Critic, label it better next round.
5. **Fix** its 3 worst problems, all three, at the cause: `frame.md` or `STORYBOARD.md` when the plan is wrong, the
   Shot when the build is. Re-run `hf check` (and `mix_check` if the audio changed).
6. **Stop** when the summary line says `All 8+: yes`; its 3 problems become "what I'd fix next". At the round limit,
   fix that round's 3 problems too, then stop. Otherwise go to round N+1.

## The final pass (every level)

1. Render (SKILL.md §4). Then the A/V check, a hard gate (on FAIL, fix the `<audio>` `data-start` or the cue time,
   re-render, and run it again):
   `mkdir -p critique/final && SKILL/scripts/py SKILL/scripts/qa/av_check.py renders/<name>.mp4 --expect <hits> --duration <length> | tee critique/final/av_check.txt`
   A video without sound (a silent Showreel) skips it: write `silent` into that file.
2. Capture the same times from the MP4, not from the composition, and label them in `critique/final/frames.md`:

   ```bash
   n=0; for t in <times>; do ffmpeg -v error -y -ss "$t" -i renders/<name>.mp4 -frames:v 1 \
     "critique/final/frame-$(printf %02d $n)-at-${t}s.png"; n=$((n+1)); done
   bash SKILL/scripts/qa/contact_sheet.sh renders/<name>.mp4 critique/final/contact-sheet.jpg <times>
   ```
3. Spawn a fresh Critic with the same prompt, but `Round: final`, `Frames: critique/final/frames.md`,
   `Previous round: critique/round-<last>.md`, a line `MP4: renders/<name>.mp4`, and
   `Write critique/final.md and nothing else.`
4. No more fixing. Deliver (SKILL.md §5) with its Grades table. If any Grade is below 8, deliver anyway: show the
   table and its "What I'd fix next". There is no third Checkpoint.

## What usually scores low (check these yourself before you spawn)

- Text overlapping text or a key object. Anything clipped by the frame edge, or sitting in a portrait safe zone.
- Something landing **off the beat** (levels 2-3): compare with `TIMING.downbeats` / word `t`.
- A lyric word on screen for less than ~0.3 s, or too small to read (keep lyric words ≥ 96 px at 1080p).
- Everything fading in the same way, or every move having the same ease and duration.
- Dead centre-stacked layouts with nothing in the corners for seconds.
- Low contrast (the check reports WCAG AA). Glow and grain eating small text.
- A world that looks like a different video (palette or fonts not from frame.md).
- No payoff for more than ~5 s (level 3 wants one every 3-5 s).
- Transitions that are plain crossfades where a match-cut or mask reveal was planned.
