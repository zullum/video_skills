---
name: yellow-dude-4k-animator
description: Create 4K biomechanical calisthenics and fitness animations in the style of Yellow Dude (Gravgear) using 3-Pose Uniform-Scale Biomechanical Articulation, 45-Point Outer/Inner Contour-Following Mesh (0% shark-fin or lat-notch artifacts), Dominant-Ink SDF Blending (0% double lines), 4K Anatomical Equipment Grips, Hollow-Body Core & Leg Kinetics, Natural Gathered-Mouth Effort Expressions, Remotion, and HeyGen HyperFrames. Use when the user asks to generate, critique, or fix Yellow Dude style animations, biomechanical exercise breakdowns, calisthenics explainer videos, 24-frame sprite sheets, or SVG fitness animations for any movement.
allowed-tools: image_gen default_api google
---

# Yellow Dude 4K Animator (v15 Multi-Movement Biomechanical & Critique Engine)

Create broadcast-grade 4K biomechanical fitness and calisthenics explainer animations in the authentic **Yellow Dude (`@yellowdude_co` / Gravgear)** style. This skill provides the complete v15 production pipeline and a **6-Point Automated Visual Critique & Self-Healing Protocol** that generalizes across **all calisthenics and strength movements** (pull-ups, chin-ups, muscle-ups, dips, push-ups, handstand push-ups, rows, front/back levers, planche, squats, pistol squats, and core exercises).

## When to Use

- The user asks for a Yellow Dude or Gravgear style calisthenics, bodyweight, or gym exercise animation.
- The user wants to convert AI-generated exercise poses into smooth 24-frame sprite loops, MP4 explainer videos, Remotion (`TypeScript/React`) compositions, or HeyGen HyperFrames (`HTML/SVG/CSS`).
- The user asks to critique, debug, or fix animation artifacts in any movement (such as double contours, black bridges between legs, notches on the lats/back, shark-fin spikes or bulges on the forearms/elbows, shrunken or ballooned arms at peak contraction, unnatural hand grips around bars/equipment, stiff/dead legs, or unnatural facial expressions).

---

## Core Architecture: 7 Golden Rules Learned from Production (v1 → v15)

### Rule 1: Use Multi-Pose True Joint Articulation at a Locked Uniform Scale (`UNIFORM_S`) — Never Single-Pose Extreme Warping
- **Why Single-Pose Warping Fails:** Warping a single static drawing across a large joint excursion (`>45°`, such as `180°` dead hang to `60°` peak contraction) crushes elbows into flat rectangles and leaves secondary limbs looking stiff and dead.
- **Why Per-Pose Auto-Scaling Fails:** Scaling different poses independently to match a target pixel height or shorts width shrinks the head and arms whenever the AI draws slightly different proportions between poses.
- **The v15 Solution:**
  1. Extract **3 real anatomical key poses** covering the movement arc (`Pose 1: Extended/Start`, `Pose 2: Mid-Range`, `Pose 3: Peak Contraction`).
  2. Scale all 3 poses by the **exact same uniform scale factor `UNIFORM_S`** derived from the pelvis/waist reference (`UNIFORM_S = 100.0 / waist_width_p2`), and lock waist/hip width (`100px`) and the un-warped **Master Head patch (`58px`)** across all 24 frames so head size and torso width have **0.0px drift**.

### Rule 2: 4x Pre-Matting with Inward Aura Stripping & Inter-Limb Pocket Probing
- **Strip Exterior AI Muscle Glow Before Matting:** When AI generates peak-contraction poses with red muscles, it often paints a pink/red halo *outside* the black comic outline. Before 4x upscaling, dilate the background mask inward across non-black exterior pixels (`can_eat = ~(R < 105 & G < 95 & B < 95)`) for 14 iterations so the background eats right up to the outer black comic ink line without touching interior red muscles.
- **Open All Inter-Limb Pockets:** Upscale 4x (`cv2.INTER_LANCZOS4` + `cv2.bilateralFilter`), then run `cv2.floodFill(..., cv2.FLOODFILL_FIXED_RANGE, (28,28,28))` from the corners **and** along vertical/horizontal probes between the thighs, knees, calves, ankles, and between the arms and torso. **Never** apply `cv2.MORPH_CLOSE` across both legs (which fuses calves/ankles into black bridges).

### Rule 3: 45-Point Outer/Inner Contour-Following Mesh (0% Shark-Fin Spikes, 0% Inner-Arm Bulges, 0% Lat Notches)
- **Why Hardcoded Offsets & Unbounded Scans Fail:**
  - Hardcoding an inner joint offset like `[lx_el + 28, ly_el - 18]` lands on the inner boundary in a narrow straight-arm pose (`26px` wide) but lands **in the middle of the muscle (`17px` inside the contour)** in a flexed pose (`45px` wide). During intermediate frames (`F02, F03, F22, F23`), that mismatch pushes the inner arm into a bulge and shears the black outline into a dark grey **shark-fin spike** (`artifakt na unutrašnjoj strani ruke`).
  - Unbounded horizontal scans (`min/max` across `x in [0..212]`) jump across the empty air gap between the arm and head/torso, grabbing the chest or outer elbow instead of the inner arm or lat.
  - Placing armpit and mid-lat landmarks too close vertically (`<10px` apart) creates a skinny horizontal triangle that notches the outer lat contour (`stepenica na leđima/lacima`).
- **The v15 Solution (`get_arm_outer_and_inner_edge_at_y`):**
  1. Track each limb at **3 evenly-spaced fractional levels (`25%, 50%, 75%` between Wrist `y=104` and Shoulder `y=sh_y`)** by marching from the outer edge inward and **stopping at the first `alpha == 0` air gap** before the head/torso. This guarantees that both `x_outer` and `x_inner` lie strictly on the true black comic outline of the limb in every pose.
  2. Separate the **Armpit (`hy + 74`)** and **Mid-Lat (`hy + 118`)** by `>= 44px` vertically along the true torso silhouette so the lat contour is a smooth, unbroken curve.
  3. When aligning hands/feet to a locked grip coordinate (`LOCKED_LX, LOCKED_RX`), taper the horizontal shift `dx` **linearly along the entire limb from Shoulder (`0.0`) → Bicep (`0.18`) → Elbow (`0.44`) → Forearm (`0.72`) → Wrist (`1.00`)** so the limb tilts as a straight anatomical unit without kinking at the elbow.

### Rule 4: Rigid-Limb Peak Extension (`KP3 → KP4`) — Never Squash or Balloon the Arms at Peak Contraction
- **Why Arms Become Thin at Peak Contraction (`v12` error):** Lifting the shoulders/torso by `-26px` while keeping the wrists pinned at `y = 92` and lifting the elbows by only `-16px` crushes the vertical distance between the bicep peak and tricep/armpit by `10–13px`, making the arms look small and thin at the top of the rep.
- **Why Post-Warp Balloon Filters Fail (`v13` error):** Non-linear Gaussian swelling fields bend straight forearm and bicep lines into deformed rubber shapes.
- **The v15 Solution:**
  - In `KP3` and `KP4`, keep the elbows and armpit attachments `+10 to +14px` lower (preserving full forearm length and upper-arm thickness), and between `KP3` and `KP4` **translate both the Torso (`24..44`) AND the Elbows/Biceps (`16..23`) rigidly together by the exact same vertical delta (`-14px`)**. Because $\Delta y_{\text{elbow}} = \Delta y_{\text{shoulder}}$, the upper arm experiences **0.0px vertical compression** and retains 100% of its natural hand-drawn comic anatomy.

### Rule 5: Secondary Kinetic Chain Liveliness (Hollow-Body Core Crunch + Natural Leg Flexion)
- Never overwrite the contracted pose's legs with straight dead-hang legs (`noge vise kao mrtve`).
- In calisthenics movements (pull-ups, dips, muscle-ups, push-ups), preserve the native **Hollow-Body hip and knee flexion** as the athlete ascends (`leg length foreshortens smoothly from ~308px in dead hang to ~266px at peak contraction` as the knees bend slightly forward), and pair it with **Active 6-Pack Abdominal Contraction (`enhance_abs_and_core_contraction`)**:
  1. `9–12px` isometric vertical crunch of the waist toward the ribcage (`sy = hy + 179 - crunch_px`).
  2. `+65%` contrast deepening of the dark comic tendinous inscriptions (`6-pack` and `serratus/oblique` grooves) so the abs visibly pop under tension.
  3. Progressive warm orange-red interior activation (`#FFD42A → #E63723`) on the `Rectus Abdominis`, `Obliques`, and `Iliopsoas / Upper Quads`.

### Rule 6: 3-Layer Equipment Z-Depth & 4K Custom-Illustrated Overhand Grip (`draw_4k_overhand_bar_grip`)
- **3-Layer Z-Depth Ordering:**
  - `Layer 0 (Back)`: Character body, torso, neck, and head passing strictly **behind** the bar, with a localized 3D bar shadow cast **only on the central head/neck (`|x - center_x| < 36 * scale`)** — **never** draw a grey shadow line under the bar across the wrists (`0% sive linije ispod šipke`).
  - `Layer 1 (Middle)`: Continuous foreground steel bar (`#525860` with `#C8D0DC` top specular highlight and `#121212` 4px comic outline).
  - `Layer 2 (Front)`: Trim the old raw AI fist above the wrist (`y < 99`), connect the true hand-drawn wrist (`y = 99`) straight into the bottom of the bar (`y = 91..98`), and render a **4x-supersampled Anatomical Overhand Grip (`draw_4k_overhand_bar_grip`)**: dorsal knuckle bridge, **4 sculpted curled comic fingers** wrapping over the top/front of the bar with 3D knuckle highlights and joint creases, plus a **diagonal thumb locking underneath the bar**.

### Rule 7: Natural 4K Gathered/Pursed Effort Mouth (`render_head_with_natural_gathered_mouth_4k`)
- **What to Avoid:** Never leave the face static across the rep, never draw pink circles/lines on the forehead, and **never draw wide clenched white teeth with sideways steam horns or white triangles over the chin** ("ne puše se kroz zube nego se malo kao skupe usta").
- **The v15 Solution:** Render the head at **4x resolution (`224x240px`)** and animate a natural **4-stage gathered-lip effort & exhale progression**:
  1. `Effort 0.00–0.15 (Start / Dead Hang)`: Calm, focused neutral face (`mouth half-width = 20px` in 4x space).
  2. `Effort 0.15–0.50 (Initial Pull & Core Bracing)`: Eyebrows angle downward with two vertical glabellar frown lines (`||`); lips press tightly and **begin gathering inward** (`half-width narrows from 19px to 14px`) with a lower-lip pucker shadow crease and subtle corner dimples `(   )`.
  3. `Effort 0.50–1.00 (Heavy Pull & Peak Exhale)`: Mouth **gathers/purses inward (`malo se skupe usta`, `half-width = 11px` in 4x space)** with a **compact horizontal-oval parted-lip exhale slit (`ow = 9.5px, oh = 4.0px` in 4x — `2.4:1` aspect ratio, never a round button hole)**, pronounced lower-lip pucker arc underneath, inward-pulled corner creases `( -o- )`, and a subtle warm effort blush on the cheeks.
  4. **Never place a callout pointer dot on top of the mouth (`(240, hy+48)`)** — always anchor facial callout pointers outside the cheek (`x = 268..284`) so 100% of the facial expression remains unobstructed.

---

## Mandatory 6-Point Automated Visual Critique & Self-Healing Protocol (For Any Exercise)

Before delivering any animation or video to the user, you **MUST** run a 3-round visual critique by generating 4x zoomed diagnostic strips of key and intermediate frames (`F01, F02, F03, F05, F07, F09, F13, F22, F23`) and inspecting them via `view_file` against this 6-point checklist:

1. **Check 1 — Inner & Outer Limb Contours on Intermediate Frames (`F02, F03, F07, F22, F23`):**
   - *Look for:* Dark grey triangle "shark-fin" spikes, double contours, or unnatural bulges along the inner forearm, elbow, bicep, shin, or thigh.
   - *Auto-Fix:* Ensure all limb landmarks use `get_arm_outer_and_inner_edge_at_y` (stopping at the first `alpha == 0` air gap) at evenly-spaced fractions `[0.25, 0.50, 0.75]` and that `blend_sdf_zero_double_lines` uses Dominant-Ink selection (`is_dom_ink = (gray_dom < 105) & (sdf_dom > 3.5)`).
2. **Check 2 — Torso & Back Silhouette Smoothness (`Latissimus Dorsi`, `Serratus`, `Waist`):**
   - *Look for:* Step-notches or diagonal triangle shears on the outer back/lat contour (`stepenice na leđima/lacima`).
   - *Auto-Fix:* Verify that the Armpit landmark (`hy + 74`) and Mid-Lat landmark (`hy + 118`) are separated by at least `40px` vertically and lie strictly on the torso silhouette (never on the elbow).
3. **Check 3 — Peak-Contraction Limb Volume Conservation (`F09–F15`):**
   - *Look for:* Arms/legs becoming thin or squashed at peak contraction (`<85%` of mid-rep thickness) OR becoming warped/ballooned.
   - *Auto-Fix:* Enforce rigid joint translation (`dy_elbow == dy_shoulder`) between `KP3` and `KP4` with zero non-linear balloon warping.
4. **Check 4 — Equipment Grip, Wrist Alignment & Bar Z-Depth:**
   - *Look for:* Old raw AI thumbs sticking out below the bar, sideways wrist kinks below the pinky finger, head clipping through the bar, or grey shadow lines crossing over the wrists.
   - *Auto-Fix:* Lock explicit Wrist landmarks at `y = 104` to `LOCKED_LX / LOCKED_RX`, trim old fist pixels above `y = 99`, remove any full-width under-bar shadow line, and render `draw_4k_overhand_bar_grip` on Layer 2.
5. **Check 5 — Secondary Kinetic Chain (Abs & Legs Liveliness):**
   - *Look for:* Legs hanging like dead weight (`mrtve noge`) or torso inflating sideways.
   - *Auto-Fix:* Preserve native Hollow-Body leg flexion across poses while locking waist/hip width to `100px` and applying `enhance_abs_and_core_contraction`.
6. **Check 6 — Natural Gathered-Mouth Effort & Unobstructed Callouts:**
   - *Look for:* Static faces, unnatural teeth/steam-horn graphics, or callout dots covering the mouth/eyes.
   - *Auto-Fix:* Use `render_head_with_natural_gathered_mouth_4k` and offset facial callout anchors to `x >= 268`. Always increment the output version suffix (`_v15.mp4`, `_v16.mp4`) when calling `google:show_file` to bypass player caching.

## Bundled Scripts & Templates

- **`scripts/yellow_dude_4k_pipeline.py`**: Complete, self-contained v15 Python + OpenCV + SciPy + PIL + FFmpeg production script implementing the 45-point outer/inner contour-following mesh, Dominant-Ink SDF blending, 4K overhand bar grip, Hollow-Body core/leg kinetics, and 4K gathered-mouth effort progression.
- **`assets/pullup_poses.jpg`**: example pull-up pose sheet (dead hang → mid → peak → peak with red muscles), the script's default input. Pass another sheet as `python scripts/yellow_dude_4k_pipeline.py my_sheet.png` (or `YD_RAW_SHEET`). Poses must sit side by side in the same layout; the sheet is resized to 1376 px wide. A bigger source (1376×768 or more) gives cleaner edges than this small example.
- **`references/remotion-and-hyperframes-templates.md`**: Ready-to-use Remotion (`YellowDudeRemotion.tsx`) and HeyGen HyperFrames (`yellow_dude_hyperframes.html`) 3-layer Z-depth templates.
