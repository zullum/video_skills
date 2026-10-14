# Remotion & HeyGen HyperFrames Templates (3-Layer Z-Depth Rig)

## 1. Remotion Template (`YellowDudeRemotion.tsx`)

```tsx
import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

/**
 * YellowDudeRemotion v4 — 3-Layer Biomechanical Z-Depth Rig (24-Frame SDF Loop)
 *  - Layer 0 (zIndex: 5): Character Body, Torso, Neck, and Head (strictly BEHIND the steel bar!)
 *  - Layer 1 (zIndex: 10): Steel Pull-Up Bar (in front of the character's head, neck, and upper chest!)
 *  - Layer 2 (zIndex: 15): Character's Gripping Fists/Fingers wrapped OVER the front of the steel bar!
 */

export const yellowDudeBezier = Easing.bezier(0.65, 0, 0.35, 1);

export const PullUpBarLayer: React.FC<{
  centerX: number;
  barY: number;
  halfWidth?: number;
}> = ({ centerX, barY, halfWidth = 360 }) => {
  const left = centerX - halfWidth;
  const width = halfWidth * 2;
  return (
    <div
      style={{
        position: 'absolute',
        left,
        top: barY - 8,
        width,
        height: 16,
        background: 'linear-gradient(180deg, #BEC6D2 0%, #555A62 45%, #3A3E45 100%)',
        border: '4px solid #121212',
        borderRadius: 8,
        boxShadow: '0 5px 0 rgba(18,18,18,0.22)',
        zIndex: 10, // Layer 1 (Middle): IN FRONT of the head/neck/chest (zIndex 5), BEHIND the gripping fingers (zIndex 15)!
      }}
    />
  );
};

export const Character3LayerRig: React.FC<{
  frameIndex24: number;
  centerX: number;
  topY: number;
  scale?: number;
  activation: number;
  barHalfWidth?: number;
}> = ({ frameIndex24, centerX, topY, scale = 1.02, activation, barHalfWidth = 360 }) => {
  const w = Math.round(480 * scale);
  const h = Math.round(820 * scale);
  const pasteX = Math.round(centerX - w / 2);
  const pasteY = Math.round(topY);
  const barY = Math.round(pasteY + 92 * scale);
  const framePadded = String(frameIndex24).padStart(2, '0');

  return (
    <>
      {/* Layer 0 (Back, zIndex: 5): Character Body & Head (passes BEHIND the pull-up bar) */}
      <div
        style={{
          position: 'absolute',
          left: pasteX,
          top: pasteY,
          width: w,
          height: h,
          zIndex: 5,
          filter:
            activation > 0.1
              ? `drop-shadow(0px 0px ${Math.round(18 * activation)}px rgba(255, 80, 25, ${(0.55 * activation).toFixed(2)}))`
              : 'none',
        }}
      >
        <Img
          src={staticFile(`frames_24_v4/frame_${framePadded}.png`)}
          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
        />
      </div>

      {/* Layer 1 (Middle, zIndex: 10): Steel Pull-Up Bar (in front of head/neck/upper chest) */}
      <PullUpBarLayer centerX={centerX} barY={barY} halfWidth={barHalfWidth} />

      {/* Layer 2 (Front, zIndex: 15): Gripping Fists/Fingers wrapped OVER the front of the bar */}
      <div
        style={{
          position: 'absolute',
          left: pasteX,
          top: pasteY,
          width: w,
          height: h,
          zIndex: 15,
        }}
      >
        <Img
          src={staticFile(`frames_24_v4/hands_${framePadded}.png`)}
          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
        />
      </div>
    </>
  );
};

export const YellowDudeRemotionV4: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;

  const cyclePeriod = 2.333;
  const u = (t % cyclePeriod) / cyclePeriod;
  const idx24 = Math.floor(u * 24) % 24;
  const activation = Math.max(0, Math.min(1, 1 - Math.abs(idx24 - 12) / 12));
  const microBounce = 1 + 0.025 * Math.exp(-Math.pow((idx24 - 12) / 2.2, 2));

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#F7F5EF',
        backgroundImage:
          'linear-gradient(to right, #EAE7DF 1px, transparent 1px), linear-gradient(to bottom, #EAE7DF 1px, transparent 1px)',
        backgroundSize: '60px 60px',
        fontFamily: 'DejaVu Sans, sans-serif',
      }}
    >
      <Sequence from={0} durationInFrames={210}>
        <Character3LayerRig frameIndex24={idx24} centerX={960} topY={118} scale={1.02 * microBounce} activation={activation} barHalfWidth={360} />
      </Sequence>
      <Sequence from={210} durationInFrames={240}>
        <Character3LayerRig frameIndex24={idx24} centerX={960} topY={115} scale={1.03 * microBounce} activation={Math.max(0.35, activation)} barHalfWidth={365} />
      </Sequence>
      <Sequence from={450} durationInFrames={240}>
        <Character3LayerRig frameIndex24={idx24} centerX={960} topY={115} scale={1.03 * microBounce} activation={activation} barHalfWidth={365} />
      </Sequence>
      <Sequence from={690} durationInFrames={durationInFrames - 690}>
        <Character3LayerRig frameIndex24={0} centerX={490} topY={222} scale={0.82} activation={0} barHalfWidth={290} />
        <Character3LayerRig frameIndex24={idx24} centerX={1430} topY={222} scale={0.82 * microBounce} activation={activation} barHalfWidth={290} />
      </Sequence>
    </AbsoluteFill>
  );
};
export default YellowDudeRemotionV4;

```

## 2. HeyGen HyperFrames Template (`yellow_dude_hyperframes.html`)

```html
<!DOCTYPE html>
<html lang="bs">
<head>
  <meta charset="UTF-8" />
  <title>Yellow Dude — 3-Layer Z-Depth HyperFrames Pull-Up Composition (v4)</title>
  <style>
    :root {
      --bg-grid: #F7F5EF;
      --grid-line: #E8E4DA;
      --yd-yellow: #FFD42A;
      --yd-red: #E63723;
      --yd-ink: #121212;
      --yd-ease: cubic-bezier(0.65, 0, 0.35, 1);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #181818;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: 'DejaVu Sans', system-ui, -apple-system, sans-serif;
    }
    #stage {
      position: relative;
      width: 1920px;
      height: 1080px;
      background-color: var(--bg-grid);
      background-image:
        linear-gradient(to right, var(--grid-line) 1px, transparent 1px),
        linear-gradient(to bottom, var(--grid-line) 1px, transparent 1px);
      background-size: 60px 60px;
      overflow: hidden;
      border: 4px solid var(--yd-ink);
    }
    /* 3-LAYER BIOMECHANICAL Z-DEPTH HIERARCHY:
       - Layer 0 (#character-body-layer): z-index 5 (Head, Neck, Torso, Legs pass BEHIND the bar)
       - Layer 1 (#pullup-bar):           z-index 10 (Steel Bar in front of neck/upper chest)
       - Layer 2 (#front-hands-layer):    z-index 15 (Gripping Fists/Fingers wrapped OVER the front of the bar)
    */
    #character-body-layer {
      position: absolute;
      top: 118px;
      left: 720px;
      width: 480px;
      height: 820px;
      z-index: 5;
    }
    #pullup-bar {
      position: absolute;
      top: 210px;
      left: 600px;
      width: 720px;
      height: 16px;
      background: linear-gradient(to bottom, #bec6d2 0%, #555a62 40%, #3a3e45 100%);
      border: 4px solid var(--yd-ink);
      border-radius: 8px;
      box-shadow: 0 5px 0 rgba(0,0,0,0.18);
      z-index: 10;
    }
    #front-hands-layer {
      position: absolute;
      top: 118px;
      left: 720px;
      width: 480px;
      height: 820px;
      z-index: 15;
      pointer-events: none;
    }
  </style>
</head>
<body>
  <div id="stage" data-composition-id="yellow-dude-v4" data-fps="30" data-duration-frames="900" data-width="1920" data-height="1080">
    <!-- Layer 0 (Back, z-index: 5): Character Body & Head (passes BEHIND the steel bar) -->
    <svg id="character-body-layer" viewBox="0 0 480 820" xmlns="http://www.w3.org/2000/svg">
      <g id="character-rig">
        <rect x="172" y="348" width="136" height="96" rx="12" fill="#181818" stroke="#121212" stroke-width="4" />
        <ellipse id="head-node" cx="240" cy="70" rx="28" ry="34" fill="#FFD42A" stroke="#121212" stroke-width="4" />
        <path id="torso-lats" d="M168,125 C145,195 170,285 182,348 L298,348 C310,285 335,195 312,125 Z" fill="#E63723" stroke="#121212" stroke-width="4" />
      </g>
    </svg>

    <!-- Layer 1 (Middle, z-index: 10): Steel Pull-Up Bar (in front of head, neck, and upper chest) -->
    <div id="pullup-bar"></div>

    <!-- Layer 2 (Front, z-index: 15): Gripping Fists/Fingers wrapped OVER the front of the steel bar -->
    <svg id="front-hands-layer" viewBox="0 0 480 820" xmlns="http://www.w3.org/2000/svg">
      <rect id="left-fist-grip" x="112" y="78" width="38" height="28" rx="9" fill="#FFD42A" stroke="#121212" stroke-width="4" />
      <rect id="right-fist-grip" x="330" y="78" width="38" height="28" rx="9" fill="#FFD42A" stroke="#121212" stroke-width="4" />
    </svg>
  </div>
  <script>
    window.seekToFrame = function(frameIdx) {
      const u = ((frameIdx / 30) % 2.4) / 2.4;
      const idx = Math.floor(u * 24) % 24;
      const act = Math.max(0, Math.min(1, 1 - Math.abs(idx - 12) / 12));
      const liftY = -52 * act;
      document.getElementById('character-rig').setAttribute('transform', `translate(0, ${liftY.toFixed(1)})`);
    };
  </script>
</body>
</html>

```
