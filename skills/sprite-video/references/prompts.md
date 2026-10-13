# Prompt templates

Replace the parts in <angle brackets>. These are the exact prompts that worked in testing
(Gemini `gemini-3.1-flash-image`, a.k.a. Nano Banana 2). Keep the STRICT RULES blocks: they are what
stops the model from zooming, moving or restyling the character.

## Base pose

Waist-up mid shot (limb motion):

> Redraw this exact character (first image is the full character, second image shows the drawing
> style and detail level) as a WAIST-UP MID SHOT for an animation key frame. Both arms hang relaxed
> straight down at the sides, both hands closed into loose fists. The frame cuts at the upper thighs,
> so the shorts are visible and the bottom edge of the image cuts through the legs just below the
> shorts. The character is centered horizontally at about 35% of the image width (left of center),
> facing the viewer, and the top of the head is at about 18% of the image height, so there is a lot
> of empty space above the head and to the right of the character. Same flat cartoon style: <style
> description>, plain flat cream background (#F7EEDF), no shadow on the background. No text.

Full body side view (whole-body motion):

> Draw this exact character (same design as the reference images: <style description>) doing a
> <EXERCISE>, seen exactly from the SIDE (pure profile), facing RIGHT (head on the right, feet on the
> left). <START POSITION, joint by joint>. A simple thin black horizontal floor line under the hands
> and toes at about 80% of the image height. The whole body is visible, centered, and spans about 70%
> of the image width. Plain flat cream background (#F7EEDF), nothing else, no shadow, no text.

Style description used for the blue character: "light blue muscular faceless body, glowing white
eyes, thick clean black outlines, simple cel shading, dark gray shorts with drawstring, barefoot".

## All-cells grid (template = base pasted in every cell)

Send the template first, then the base image. Describe the motion in frame ranges with degrees per
frame; the model follows ranges better than adjectives.

```text
EDIT this ANIMATION SPRITE SHEET. It is a 6 x 4 grid of 24 cells, read left to right, top to bottom (frames 1 to 24). Every cell already contains the same character, drawn at the same size and position. Your ONLY job is to repaint the character's arm on the viewer's RIGHT side in cells 2 to 24 so the 24 cells form one smooth flex animation.

STRICT RULES (most important):
- Do NOT redraw, resize, zoom, re-crop or move the character in any cell. Head, glowing eyes, chest, abs, the arm on the viewer's LEFT, shorts and legs stay exactly as they are in the template, same size, same place, same outline thickness, in all 24 cells and in all 4 rows. Row 4 must look exactly as big as row 1.
- The bottom edge of every cell keeps cutting the legs exactly where it does now. The top of the head stays at the same height in every cell.
- Keep the gray grid lines exactly where they are. The moving arm and fist must always stay fully inside their own cell, never crossing a grid line.
- The fist stays CLOSED in every frame. Same flat cartoon style, thick black outlines, white glowing eyes, plain cream background. No numbers, no text, no extra characters.

MOTION (small, evenly spaced steps, each frame only slightly different from the previous one):
- Frame 1: arm hangs down (leave cell 1 unchanged).
- Frames 2 to 6 (rest of row 1): the straight arm swings out sideways and up, about 18 degrees more per frame, until in frame 6 it points straight out to the right, horizontal at shoulder height.
- Frames 7 to 14: the upper arm stays horizontal at shoulder height. The elbow bends and the forearm rises from horizontal to straight up, about 11 degrees more per frame (8 even steps). In frame 14 the forearm is vertical with the fist above the elbow.
- Frames 15 to 20: the classic bicep flex. The fist curls a little toward the head and the bicep grows bigger and rounder each frame.
- Frames 21 to 24: peak flex. Biggest bicep with a bright WHITE shine highlight on it. In frames 23 and 24 add three short curved motion lines next to the bicep.
```

Known failure: the model may skip the first big move (frames 2–6 came out already horizontal). Fix
it with a small guided sheet for those in-betweens (next section) instead of regenerating the grid.

## Guided in-betweens (red line + circle per cell)

Template: key frames in the first/last cells, the limb erased in the cells between, a red line from
the joint at the target angle and a red circle where the hand goes (`template.py` `guide` + `circle`).

```text
FINISH this ANIMATION SPRITE SHEET: a 4 x 2 grid of 8 cells (frames 1 to 8, left to right, top to bottom). Cell 1 (arm angled down and out) and cells 6, 7 and 8 (arm straight out almost horizontally) are finished key frames: leave them exactly as they are.
In cells 2 to 5 the arm on the viewer's RIGHT has been erased and replaced by a RED GUIDE: a red line from the shoulder and a red circle. Draw the character's straight muscular arm EXACTLY along each red line, at exactly that angle, with the CLOSED FIST inside the red circle, in the same style as the arm in cell 8 (same thickness, same length, same black outline, same blue colour). Each cell's arm is at a different angle; follow the guide, do not copy cell 8's angle. Repair the side of the torso and the shorts where they were erased. Then remove every trace of red: no red lines or circles may remain.
STRICT RULES: do NOT redraw, resize, zoom, re-crop or move the character. Head, glowing eyes, torso, the arm on the viewer's LEFT, shorts and legs stay identical in all 8 cells, same size and same place. Keep the gray grid lines exactly where they are. Same flat cartoon style, thick black outlines, plain cream background. No numbers, no text.
```

## Rigged whole-body grid (IK guide: shoulder, elbow, wrist dots)

Template from `examples/pushup_spec.py` (body rotated about the toes, arm erased, hand kept, guide).

```text
FINISH this ANIMATION SPRITE SHEET of a push-up, seen from the side: a 3 x 3 grid of 9 cells (frames 1 to 9, left to right, top to bottom). Frame 1 is the top position (arm straight), frame 9 the bottom position; the frames between go smoothly down.
In ALL 9 cells the body is already placed at the right angle, but the near arm was erased and replaced by a RED GUIDE (three red dots joined by two red lines: shoulder, elbow, wrist). In each of these cells:
- Draw the character's muscular arm EXACTLY along the red guide: upper arm from the shoulder dot to the elbow dot, forearm from the elbow dot to the wrist dot, the hand flat on the floor where it already is. The elbow is exactly at the middle red dot and points back toward the feet. As the elbow bends it flares slightly OUT toward the viewer, so the upper arm looks a little shorter (foreshortened) in the lower frames; the forearm keeps its length. Draw all 9 arms in one consistent style: same thickness, light blue colour, cel shading and thick black outline as the rest of the body.
- Repair the chest, shoulder and torso where they were erased so the body looks complete and clean, and clean up any stray lines near the toes.
- Then remove every trace of red: no red lines or dots may remain.
STRICT RULES: do NOT move, resize, rotate or re-crop the body, head, legs, feet, hand or the black floor line in any cell; keep each body exactly at the angle and place it has in the template. Keep the gray grid lines exactly where they are. Same flat cartoon style, thick black outlines, white glowing eye, plain cream background. No numbers, no text.
```

## Checks after every generation

- Same character size in every row (slice and compare, or look at head size in row 1 vs row 4).
- No red pixels left: `python3 -c "import numpy as n;from PIL import Image as I;a=n.array(I.open('sheet.png').convert('RGB')).astype(int);print(((a[...,0]>180)&(a[...,1]<90)&(a[...,2]<90)).sum())"` → 0.
- The moving limb is present and different in every cell; the fist is closed; nothing crosses a grid line.
