# Critique: grading every shot

A fresh Critic agent (never the one who built it) grades the snapshots; the builder fixes the three worst problems
and asks a new Critic. Up to 3 rounds; every shot must reach 8/10. The Critic only sees frames, so loudness is
`mix_check.py`'s job and sync is `av_check.py`'s.

## Snapshots to give the Critic
`scripts/py scripts/critic_frames.py P --out critique/round-<n>`: every shot at start + 0.25 s, the middle, end − 0.25 s
and 0.15 s after every beat, tiled into `sheet-*.png` (one row per shot, its narration line under it). Read the
sheets yourself first, then give their paths and this file to a fresh Critic agent.

## The checklist (score each shot 1-10 on the worst item)
1. **Style fidelity:** palette roles respected; every traced asset has the same ink weight as the code ink; no chroma
   fringe or box around any asset; the character looks the same in every shot.
2. **Readability:** headline text fully inside the frame and legible at phone size; nothing important under another
   element; tags not covering faces.
3. **Motion:** pops land on their words; nothing frozen for 2 s; transitions read (zoomIn follows a zoom, whip blur
   is visible); no element jumps between two frames (a missing tween or a wrong initial state).
4. **Sprites** (sprite-video `references/critique.md`): no shake between frames, no sliding feet, no floating torso,
   no missing in-between (a jump in the loop); holds at the top and bottom of the rep.
5. **Composition:** the subject near a third or the centre; balanced negative space; the camera push never cuts the
   head or the floor.
6. **Story:** the picture says what the line says (a list shows the items, a number shows the number).

## The Critic's prompt
> You are a strict motion-design critic. These are frames of a narrated cartoon explainer, one row per shot, with the
> narration line under each row. Grade every shot 1-10 against this checklist: {the 6 items}. For each shot give the
> grade and the single worst problem with the frame where it shows. Then list the three problems that would most
> improve the video, each with a concrete fix (which shot, which param or beat). Do not praise. Grade 8 means "a
> viewer would not notice anything wrong".

Write the grades to `critique/round-<n>.md`; the last round's table goes to the user.

## Fix order
Sequence, timing and camera first (shots.json: `at`, `params`, `push`, `hold`); then scene code; regenerate an
image only for a drawing error, and say what it costs before you do.
