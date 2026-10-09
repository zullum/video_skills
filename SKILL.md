---
name: viral-motion
description: A director's workflow for making high-end motion-graphics videos with Claude at three levels. (1) An aesthetic showreel with no music, (2) a kinetic lyric music video with an ORIGINAL song generated locally (ACE-Step 1.5), every word landing on its sung onset, (3) a short cinematic story film with an original score, full sound design and a critique loop graded by a separate Critic. A fork of motion-studio for this Mac: a Watercolor style, the user's own voice Recording (any language) or own music, English Kokoro narration, two checkpoints, portrait by default, and no Gemini. Everything is $0 and local (HyperFrames, ACE-Step, demucs, whisper.cpp, Kokoro, numpy, ffmpeg). Use this skill whenever someone wants a motion graphics video, showreel, kinetic typography piece, lyric video, music video, animated story or short film, a video "like the viral Claude motion graphics", an original song or score for a video, synced lyrics, or sound effects for an animation; a watercolor or painted look; a video with narration, "my voice" or "my recording"; a Bosnian, Croatian or Serbian video; a portrait video for Reels or TikTok; or when they say "motion studio", "viral motion", "level 1/2/3" or "make it like the three videos". It works alongside the HyperFrames skills (/hyperframes, /general-video): this skill directs, they build.
---

# Viral Motion

Claude can't output an MP4. It writes code, a web page that knows what the screen looks like at every
moment, and HyperFrames screenshots every frame and glues them into a video. Whether the result looks
like everyone else's or like a real motion designer made it comes down to **the setup around the prompt**.
In the viral videos the prompt is 10% and the setup is 90%. This skill is that setup, taken from three
finished videos:

| level | example | what makes it work |
|---|---|---|
| 1 Showreel | 16 s, 60 fps, pastel, one violet shape that never cuts, 7 labelled techniques, no music | a tight art direction plus one continuous idea |
| 2 Lyric video | 35.6 s, an original hyperpop song made locally, 9 visual worlds, every word on its sung onset | free local music, vocal-stem word timing, cuts on downbeats, banned defaults |
| 3 Story film | 68.5 s "One Conversation", 12 shots, score with a drop, 375 synthesized sound effects | a story, colour as story, gates it can't skip, a critique loop until every shot is 8/10+ |

`SKILL` below means the folder this file is in. Run Python scripts with `SKILL/scripts/py` (its Python 3.12
venv has numpy). Run shell scripts with `bash`. Run HyperFrames only as `SKILL/scripts/hf <args>`.

## Cost: $0. Keep it that way.

HyperFrames (open source) renders. ACE-Step 1.5 (MIT) makes the music on this computer. demucs splits
the vocals. The user's whisper.cpp build (`~/myprojects/whisper.cpp`, large-v3-turbo) times the words. Every sound effect
is synthesized with numpy. Never route anything through paid music, voice, image or video APIs,
credit-based tools or sign-ups. Narration is the user's own Recording (any language) or English Kokoro
through `SKILL/scripts/hf tts`, never /media-use. Without either, the stories work with on-screen text.

## No Gemini, ever

- `SKILL/scripts/hf` strips `GEMINI_API_KEY`/`GOOGLE_API_KEY` and adds `--describe false` to every snapshot.
  Whenever any HyperFrames skill or example prompt says `npx hyperframes X`, run `SKILL/scripts/hf X` instead.
- Never use /media-use or its audio helpers: they have Gemini TTS and Lyria paths.
- You read frames and contact sheets yourself (Read the PNG/JPG). No frame goes to a vision API.

## 0. Setup check (first use on a machine)

- `bash SKILL/scripts/check.sh` checks everything and installs nothing: Node, ffmpeg, HyperFrames + Chrome, ACE-Step (`SKILL/.acestep`) and its checkpoints, demucs, the user's whisper-cli and models, the skill's venv and the Kokoro models, and that the Gemini keys are blank. If it fails, show the user its printed fixes.
- Levels 2 and 3 need the music studio. Check the free disk first (`df -h ~`). If there's no room, tell the user, and offer level 1 or a level 2/3 with music they supply (any WAV/MP3 they own the rights to).
- HyperFrames refuses to render below 1 GB of free disk. A long 1080p render wants 3+ GB.
- Music generation needs ~10 GB free disk on top (swap headroom). Below that, a 16 GB machine can restart while the model loads. `run_music.sh` refuses to start, so free up space rather than forcing it.

## 1. Pick the level and write the director's brief (decide, then stop at Checkpoint 1)

Read the request and pick a level. Say it in one line ("Level 2: lyric video, original song, ~35 s, portrait, English") and keep going.
- No music, short, "showreel", "aesthetic", "logo sting", or the user just wants to test: **Level 1**. Read `references/level-1-showreel.md`.
- A song, lyrics, a music video, "with music", "go crazy": **Level 2**. Read `references/level-2-lyric-video.md`.
- A story, a film, an ad with an arc, 45-90 s, "the most impressive": **Level 3**. Read `references/level-3-story-film.md`.

**Defaults** unless the user says otherwise: portrait 1080x1920, English. **Visual style**: one the user names wins.
Pick Watercolor unasked only when the request clearly fits (painted, storybook, fairy tale): `references/watercolor.md`.

**Audio routing:**
- Showreel: silent.
- Lyric video: a generated song, or the user's song file plus its lyrics as text (no Takes, no Checkpoint 2). No
  Narration. Bosnian/Croatian/Serbian songs are allowed, with a warning that the model may sing them less clearly.
- Story film: a generated Score or the user's instrumental. Narration: the user's Recording in any language
  (Shots are cut to it: `references/recording.md`), English Kokoro (`references/narration.md`), or none. Without a
  Recording, Bosnian/Croatian/Serbian videos are on-screen text only.

Then **expand the user's sentence into a full director's brief** using that level's template. This is the
step that makes the difference: the three example prompts (`examples/prompts/`) are 1.4k, 8k and 10k
characters. Make every creative decision yourself, say what you chose in one line, and only ask if
something truly can't be decided (a brand name you can't guess, for example). The user approves it at Checkpoint 1.

Before writing any composition HTML, write in the project:
1. `BRIEF.md` (HyperFrames brief contract: workflow general-video, flow automation, aspect, fps, length, message).
2. `frame.md`, the design truth: palette (hex, with roles), 2-3 fonts with their jobs, materials, motion rules, transitions, the **ban list** (below) and, in portrait, the safe zones (`references/art-direction.md`).
3. `STORYBOARD.md`, the **Beat sheet**, at every level: one `## Frame N` block per Shot (a technique in a Showreel, a world in a Lyric video, a shot in a Story film): timestamps, on-screen text, the visual payoff, the transition, the cited blueprint/rules from /hyperframes-animation, and the sound cues. With a Recording, add the Narration script, line by line per Shot.

## Checkpoints (the only two stops)

**Checkpoint 1**, after the Beat sheet and before any composition HTML or music. Show:
- one line: level, length, format, language, Visual style;
- the art direction (from `frame.md`) and the Beat sheet as a table;
- the lyrics (Lyric video);
- with a Recording: the Narration script, and how to record it (a phone memo in a quiet room, ~1 s pause between
  lines, then send the file path).

The user replies "ok" or with edits.

**Checkpoint 2**, after the Takes are ranked (skipped when the user supplies the Track). Show a ranked table of
Takes (length, sung-lyric accuracy or arc fit, notes, path), then your pick and its reason. The user replies with
a number or "regenerate: <change>". Open nothing automatically. With a Recording, the Score is generated after
the Recording is timed, to its length.

**Extra stops**, only for hard fails that only the user can fix: a Recording with under 70% of the Narration
script heard (wrong language or garbage), or an own Track shorter than the video. Say exactly what's wrong and
wait for a new file. Soft flags (a skipped line, fillers, a longer Track trimmed with a fade) don't stop the run;
report them at delivery.

## 2. Ban the defaults (the trick nobody uses)

If you don't ban the defaults, every video comes out the same: centred text, a purple-blue gradient,
everything fading in, Inter/Helvetica, glassmorphism cards. In `frame.md` write an explicit **"Do NOT use"**
list:
- the generic AI look above, always;
- every look already used: read the `frame.md` / `BRIEF.md` of every project in `~/myprojects/musicmodel/videos/*` and `~/myprojects/original_viral_claude_video/videos/*` and ban their palettes, fonts and signature techniques, so each video looks new;
- anything the user said they're tired of.
A Visual style the user names wins over the ban. The ban then covers that earlier video's palette, fonts and signature techniques.
Then pick ONE bold, cohesive art direction (see `references/art-direction.md`) and commit.

## 3. Build (through HyperFrames)

1. Start the project from `~/myprojects/musicmodel`: `bash SKILL/scripts/new_project.sh videos/<name> <1|2|3> [portrait|landscape|square]` (portrait by default). It runs `hf init` and adds `audio/song.json` / `audio/sfx_cues.json` templates.
2. Invoke **/hyperframes** (mandatory entry point) and follow **/general-video** for the composition. Treat your director's brief as the confirmed brief (flow automation, storyboard no). Use /hyperframes-animation for blueprints and rules and /hyperframes-registry before hand-building any named effect (`SKILL/scripts/hf catalog --query "<effect>" --json`).
3. Levels 2-3: **music first, then timing, then animation.** Every animation time comes from `audio/timing.json`. Never guess a beat. See `references/music.md`.
   With a Recording, time it first: Shot times come from it (`references/recording.md`). English Narration: `references/narration.md`.
4. Multi-scene pieces: one sub-composition per scene. Level 3 builds scenes with parallel sub-agents (2-3 scenes per worker, all workers in one wave), each writing its `compositions/frames/<id>.html` and a `<id>.motion.json` of the events that need sound.
5. Sound design: `references/sound-design.md`. Every whoosh, impact, click and riser is synthesized at an exact time. Mix with /hyperframes-audio. Every `<audio>` element needs an `id`.

## 4. Quality gates (in order, no skipping)

plan → music + timing → stills (a key frame of every shot) → full animation pass → polish → sound + mix → check → render → verify

- `SKILL/scripts/hf check` passes with **0 errors**. Fix contrast, layout and lint findings properly. Only mark truly decorative elements with `data-layout-ignore` / `data-layout-allow-overlap`.
- **Critique loop** (`references/critique-loop.md`): take snapshots (`SKILL/scripts/hf snapshot`) at every Shot's midpoint and key moments. A **fresh Critic agent** per round (`references/critic.md`), never the Crew, grades each Shot 1-10 on the level's axes and writes down the 3 worst problems. Fix them and repeat until every Grade is 8+ (max 1 round for level 1, 3 for level 2, 4 for level 3). Level 3 also runs the animation map and removes dead zones.
- Render: `SKILL/scripts/hf render -o renders/<name>.mp4 --fps <fps> --workers 2` (2 workers: other chats may be rendering).
- Verify: `SKILL/scripts/py SKILL/scripts/qa/av_check.py renders/<name>.mp4 --expect <the big hit times> --duration <length>`. It needs an audio stream, the right length, and hits within one frame. Then make a contact sheet: `bash SKILL/scripts/qa/contact_sheet.sh renders/<name>.mp4 renders/<name>-contact.jpg <times...>`. Look at it yourself.
- Final Critic pass on the MP4: a fresh Critic writes the Grades the user receives to `critique/final.md`.

Read `references/lessons.md` before building. Every item in it cost a debug round once.

## 5. Deliver

Open the MP4 (`open` on macOS). Then tell the user, briefly:
- the MP4 path, the contact sheet, and the length / fps;
- levels 2-3: the paths of **all** music takes, which one you chose and why (and that swapping takes means re-timing), the lyrics or the beat sheet with timestamps, and the SFX cue sheet;
- the Critic's final Grades table (`critique/final.md`) and any soft flags (a skipped line, fillers, a trimmed Track);
- what you'd improve with another round.

## Script reference

| script | what it does |
|---|---|
| `scripts/check.sh` | check the local toolchain (installs nothing) |
| `scripts/hf <args>` | HyperFrames without Gemini: every `npx hyperframes` call goes through it |
| `scripts/new_project.sh <dir> <level> [format]` | HyperFrames project (portrait by default) + audio templates |
| `scripts/selftest.sh [dir]` | SFX → check → render → A/V check on a 3 s clip |
| `scripts/music/run_music.sh <project> [seeds]` | generate + decode ACE-Step takes under the one-job lock |
| `scripts/music/stems.sh <project> <take...>` | demucs vocal/instrumental stems + vocal-stem transcript |
| `scripts/music/rank_takes.py <project>` | rank takes: lyrics sung (song) or story-arc fit (score), early-ending check |
| `scripts/music/timing.py <project> --take seedN` | beats, downbeats, drop, sections, word onsets, envelopes → `audio/timing.json` + `assets/js/timing.js` |
| `scripts/music/trim.sh <take.wav> <end> <out.wav>` | trim to the musical end with a fade |
| `scripts/music/score_viz.py` | bake the real score's waveform + piano roll into JSON for an on-screen "composer" |
| `scripts/sfx/build_sfx.py <project>` | `audio/sfx_cues.json` + scene `*.motion.json` events → SFX stems + cue sheet |
| `scripts/qa/av_check.py <mp4>` | audio stream, length, hit sync |
| `scripts/qa/contact_sheet.sh <mp4> <jpg> [t...]` | labelled frame grid |
