// usage: node shoot.cjs "player.html?dir=frames&seq=..." OUT.mp4 --video SECONDS [--fps 30] [--scale 2]
//        node shoot.cjs "player.html?..." OUT.png --still SECONDS [--scale 2]
// Films a page that exposes window.render(t) and window.ready with headless Chromium and pipes the
// frames to ffmpeg (H.264). --scale 2 renders the 1920x1080 page at 3840x2160: the SVG frames are
// re-rasterised at 4K, not upscaled. Needs: node, playwright (npm i -D playwright), ffmpeg.
// CHROMIUM=/path/to/chrome overrides the browser binary.
const path = require('path'), { spawn } = require('child_process');
let playwright;
try { playwright = require('playwright'); }
catch { playwright = require(path.join(process.execPath, '../../lib/node_modules/playwright')); }
const a = process.argv.slice(2), [html, out] = a;
const opt = n => { const i = a.indexOf(n); return i >= 0 ? a[i + 1] : null; };
const fps = Number(opt('--fps') || 30), scale = Number(opt('--scale') || 1);
(async () => {
  const b = await playwright.chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
  const [hp, hq] = html.split('?');
  await p.goto('file://' + path.resolve(hp) + (hq ? '?' + hq : ''));
  await p.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
  if (opt('--still') !== null) {
    await p.evaluate(t => window.render(t), Number(opt('--still')));
    await p.screenshot({ path: out });
  } else {
    const dur = Number(opt('--video') || await p.evaluate(() => window.duration));
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < Math.round(dur * fps); i++) {
      await p.evaluate(t => window.render(t), i / fps);
      ff.stdin.write(await p.screenshot({ type: 'jpeg', quality: 92 }));
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await b.close(); console.log('wrote', out);
})();
