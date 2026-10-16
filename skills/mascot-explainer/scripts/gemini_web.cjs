// One image from the Gemini web app, drawn in the user's logged-in Chrome on CDP (default 9003, gemini_chrome.sh).
//   node gemini_web.cjs OUT.png "prompt" [ref.png ...]      (gen_asset.py runs it; it is the default PROVIDER)
// env: ASPECT (one of the app's: 1:1 16:9 9:16 4:3 3:4; default 16:9), GEMINI_WEB_MODE (mode-menu label regex,
//      default "Flash All-around"), GEMINI_CDP (default http://127.0.0.1:9003).
// It opens its own tab on /images, sets the aspect ratio and the mode, uploads the references, sends the prompt,
// waits for "Download full-sized image" and saves the download (a JPEG; gen_asset stores it as a PNG).
// Exit 0: written, 5: Gemini is logged out (the tab stays open on it; nothing is ever typed into a login page),
// 6: Gemini answered without an image (its words are printed), 1: anything else (a screenshot goes to OUT.fail.png).
const os = require('os'), path = require('path');
const { execFileSync } = require('child_process');

const CDP = process.env.GEMINI_CDP || 'http://127.0.0.1:9003';
const MODE = new RegExp(process.env.GEMINI_WEB_MODE || 'Flash All-around');
const WAIT_MS = 6 * 60 * 1000;
const log = (...a) => console.error('[gemini-web]', ...a);

function loadPlaywright() {
  const tries = ['playwright', path.join(process.execPath, '../../lib/node_modules/playwright'),
    path.join(os.homedir(), '.claude/skills/playwright-skill/node_modules/playwright')];
  for (const t of tries) { try { return require(t); } catch { /* next */ } }
  throw new Error('playwright not found (npm i -g playwright)');
}

async function cdpUp() {
  try { return (await fetch(CDP + '/json/version')).ok; } catch { return false; }
}

async function ensureChrome() {
  if (await cdpUp()) return;
  if (!CDP.endsWith(':9003')) throw new Error(`no Chrome listening on ${CDP}`);
  execFileSync('bash', [path.join(__dirname, 'gemini_chrome.sh')], { stdio: 'ignore' });
  if (!(await cdpUp())) throw new Error(`Chrome did not come up on ${CDP}`);
}

// One-time tooltips and dialogs ("A new home for Spark") lay a backdrop over the page that swallows clicks.
async function calm(page) {
  for (let i = 0; i < 3 && await page.locator('.cdk-overlay-backdrop-showing').count(); i++) {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
  }
}

async function setUp(page, aspect) {
  await page.goto('https://gemini.google.com/images', { waitUntil: 'domcontentloaded' });
  const box = page.getByRole('textbox', { name: 'Enter a prompt for Gemini' });
  const signIn = page.locator('a:has-text("Sign in"), button:has-text("Sign in")');
  await Promise.race([box.waitFor({ timeout: 45000 }), signIn.first().waitFor({ timeout: 45000 })]);
  if (await signIn.count()) return null;
  await calm(page);
  await page.getByRole('button', { name: 'Aspect ratio' }).click();
  await page.getByRole('menuitemradio', { name: aspect, exact: true }).click();
  await calm(page);
  await page.getByRole('button', { name: /Open mode picker/ }).click();
  await page.getByRole('menuitem', { name: MODE }).first().click();
  return box;
}

async function upload(page, refs) {
  if (!refs.length) return;
  await calm(page);
  await page.getByRole('button', { name: 'Upload and tools' }).click();
  const [chooser] = await Promise.all([page.waitForEvent('filechooser'),
    page.getByRole('menuitem', { name: /Upload files/ }).click()]);
  await chooser.setFiles(refs);
  // Each reference shows as img "attachment" with a "Loading image" bar until it is uploaded.
  for (const t0 = Date.now(); Date.now() - t0 < 90000; await page.waitForTimeout(500)) {
    const shown = await page.getByRole('img', { name: 'attachment' }).count();
    const loading = await page.getByRole('progressbar', { name: 'Loading image' }).count();
    if (shown >= refs.length && !loading) return;
  }
  throw new Error('the references did not finish uploading');
}

async function lastAnswer(page) {
  return (await page.locator('message-content').last().innerText().catch(() => '')).trim();
}

// Resolves to the new download button, or null when Gemini finished its answer without an image.
async function generate(page, box, prompt) {
  const download = page.getByRole('button', { name: 'Download full-sized image' });
  const before = await download.count();
  await box.click();
  await box.fill(prompt);
  await page.getByRole('button', { name: 'Send message' }).click();
  let quiet = 0;
  for (const t0 = Date.now(); Date.now() - t0 < WAIT_MS;) {
    await page.waitForTimeout(2000);
    if (await download.count() > before) return download.last();
    const busy = await page.getByRole('button', { name: /^Stop/ }).count();
    quiet = !busy && Date.now() - t0 > 30000 && (await lastAnswer(page)) ? quiet + 1 : 0;
    if (quiet >= 8) return null;                         // 16 s with a finished text answer and no image
  }
  throw new Error(`no image after ${WAIT_MS / 1000} s`);
}

async function save(page, button, out) {
  await button.scrollIntoViewIfNeeded();
  await button.hover({ force: true });
  const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 120000 }), button.click({ force: true })]);
  await dl.saveAs(out);
}

(async () => {
  const [out, prompt, ...refs] = process.argv.slice(2);
  if (!out || !prompt) { console.error('usage: node gemini_web.cjs OUT.png "prompt" [ref.png ...]'); process.exit(1); }
  await ensureChrome();
  const browser = await loadPlaywright().chromium.connectOverCDP(CDP);
  const page = await browser.contexts()[0].newPage();     // its own tab: the user's tabs are left alone
  let code = 1;
  try {
    const box = await setUp(page, process.env.ASPECT || '16:9');
    if (!box) {
      code = 5;
      log(`Gemini is logged out: log in in the Chrome on ${CDP} (the tab is open), then run again`);
    } else {
      await upload(page, refs.map(r => path.resolve(r)));
      const button = await generate(page, box, prompt);
      if (!button) {
        code = 6;
        log('Gemini answered without an image:', (await lastAnswer(page)).slice(0, 600));
      } else {
        await save(page, button, out);
        code = 0;
        console.log('wrote', out);
      }
    }
  } catch (e) {
    log('FAIL', e.message);
    await page.screenshot({ path: out + '.fail.png' }).catch(() => {});
  } finally {
    if (code !== 5) await page.close().catch(() => {});
    await browser.close();
    process.exit(code);
  }
})().catch(e => { log('FAIL', e.message); process.exit(1); });
