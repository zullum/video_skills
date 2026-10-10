# Viral Motion: a fork of Motion Studio

The author's Motion Studio skill (everything behind three motion-graphics videos made with Claude), forked for
this Mac. It keeps the three levels:

1. **Showreel** (no music): one simple prompt with a real art direction. 16 s, 60 fps, 7 techniques.
2. **Lyric music video**: Claude writes an original song, makes it ON YOUR COMPUTER, picks the best take,
   finds the exact moment every word is sung, and animates to it. The sound effects are made with code.
3. **Story film**: a director's brief, a score with a drop, hundreds of synthesized sound effects, and a
   critique loop where every shot is graded and fixed until each one is 8/10 or better.

It adds: a Watercolor style, your own voice Recording (any language) or your own music, English Kokoro
narration, a separate Critic, two checkpoints (approve the beat sheet, then the music take), portrait
1080x1920 by default, and no Gemini anywhere (`scripts/hf`). The git history shows every change: the first
commit is the untouched original.

## Cost: $0

| piece | what it is | price |
|---|---|---|
| HyperFrames + its skills | open-source HTML → video renderer, run through `scripts/hf` | free |
| ACE-Step 1.5 | open-source music model (MIT) that runs locally | free |
| demucs, whisper.cpp | vocal separation and word timing, local | free |
| Kokoro-82M | English narration, local | free |
| Sound effects | 18 effects synthesized with numpy (no downloads) | free |
| Node.js, ffmpeg, Python | standard tools | free |

No API keys, credits, subscriptions or sign-ups on top of Claude.
**Disk:** keep ~10 GB free while it makes music: on a 16 GB computer it swaps hard, and with a full disk the
computer can restart. Level 1 works without the music model.

## Install

Already installed at `~/.claude/skills/viral-motion/`. Check the toolchain with
`bash ~/.claude/skills/viral-motion/scripts/check.sh` (it installs nothing and prints the fix for anything
missing), then prove it with `bash ~/.claude/skills/viral-motion/scripts/selftest.sh`.

## Use

Run sessions from `~/myprojects/musicmodel` (its settings blank the Gemini keys). Just ask:
- "Make me a 15-second showreel that shows off what you can do. Pastel, one accent colour, no music." (level 1)
- "Make a lyric music video for an original song about my coffee shop opening. Make it go crazy." (level 2)
- "Make a 60-second story film about a nurse's night shift, with a score and full sound design." (level 3)

Each video gets its own project folder in `videos/` with `renders/<name>.mp4`, a contact sheet, the music
takes, the timing file and the sound-effect cue sheet.

## What's inside

```
SKILL.md                    the workflow Claude follows (levels, brief, ban list, checkpoints, gates)
references/                 level guides, music, sound design, critique loop, lessons, art direction
examples/prompts/           the three real prompts the example videos were made from
scripts/check.sh            checks the local toolchain (installs nothing)
scripts/hf                  the only way to run HyperFrames: no Gemini keys, no frame descriptions
scripts/music/              ACE-Step generation, stems, take ranking, beat + lyric timing, trimming
scripts/sfx/                the numpy sound-effect library + cue builder, the Narration duck lane
scripts/recording/          the user's voice Recording → clean stem, word timing, Shots
scripts/qa/                 mix loudness gate, A/V sync check, contact sheets
templates/                  song / score / cue templates, a self-test clip
```

Third-party licences: see LICENSES.md.
