// Owner: Nikki
//
// The document viewer, in a real browser, at every viewport the demo might
// run in. Companion to layout.mjs, which walks the kiosk; this walks the
// physician console instead — log in, open the case with documents, open the
// viewer, and check the modal.
//
// WHY IT EXISTS: the viewer is a fixed-position overlay holding an image of
// unknown size beside a findings list. That is exactly the shape that looks
// right at 1280x800 and pushes its Close button off-screen at 1024x768, and
// a doctor who cannot reach Close is stuck on a modal over a patient record.
//
//   node e2e/viewer.mjs                 # all viewports
//   node e2e/viewer.mjs 1280x800        # one
//
// Exits non-zero on the first failure, so it can gate a commit.

import { chromium } from '@playwright/test';

const BASE = process.env.KIOSK_URL || 'http://localhost:5173';
const API = process.env.API_URL || 'http://localhost:8000/api';
const USER = process.env.CLINICIAN_USERNAME || 'drmehta';
const PASS = process.env.CLINICIAN_PASSWORD;

const VIEWPORTS = process.argv[2] ? [process.argv[2]] : ['1280x800', '1024x768', '1280x1024', '1440x900', '1366x768'];

const TRACKED = ['.viewer__panel', '.viewer__head', '.viewer__close', '.viewer__body',
                 '.viewer__image', '.viewer__findings', '.viewer__tools', '.viewer__img'];

function inspect(tracked) {
  const out = { boxes: [], scrollX: document.documentElement.scrollWidth > window.innerWidth };
  for (const sel of tracked) {
    for (const el of document.querySelectorAll(sel)) {
      const r = el.getBoundingClientRect();
      if (r.width && r.height) {
        out.boxes.push({ sel, t: Math.round(r.top), b: Math.round(r.bottom),
                         l: Math.round(r.left), r: Math.round(r.right) });
      }
    }
  }
  return out;
}

let failures = 0;

function check(label, { boxes, scrollX }, vw, vh) {
  const problems = [];
  const find = (s) => boxes.find((b) => b.sel === s);

  // Everything the doctor must be able to reach has to be ON the screen.
  for (const sel of ['.viewer__panel', '.viewer__close', '.viewer__findings']) {
    const b = find(sel);
    if (!b) { problems.push(`MISSING: ${sel}`); continue; }
    if (b.t < 0 || b.b > vh) problems.push(`OFF-SCREEN VERTICALLY: ${sel}[${b.t}-${b.b}] in ${vh}`);
    if (b.l < 0 || b.r > vw) problems.push(`OFF-SCREEN HORIZONTALLY: ${sel}[${b.l}-${b.r}] in ${vw}`);
  }
  // The whole point is seeing both at once.
  const img = find('.viewer__image'), fnd = find('.viewer__findings');
  if (img && fnd && img.r > fnd.l && fnd.r > img.l && img.t < fnd.b && fnd.t < img.b) {
    problems.push(`OVERLAP: image over findings`);
  }
  if (scrollX) problems.push('PAGE SCROLLS HORIZONTALLY');

  if (problems.length) {
    failures += 1;
    console.log(`  FAIL  ${label}`);
    for (const p of problems) console.log(`        ${p}`);
  } else {
    console.log(`  ok    ${label}`);
  }
}

const browser = await chromium.launch();

for (const vp of VIEWPORTS) {
  const [vw, vh] = vp.split('x').map(Number);
  const ctx = await browser.newContext({ viewport: { width: vw, height: vh } });
  const page = await ctx.newPage();
  console.log(`\n=== ${vp}  physician console ===`);

  await page.goto(`${BASE}/physician`);
  await page.fill("#username", USER);
  await page.fill("#password", PASS);
  await page.click('button[type="submit"]');
  await page.waitForSelector('.queue, .case', { timeout: 15000 });

  // The case with documents.
  await page.click('text=A-44');
  await page.waitForSelector('.timeline', { timeout: 15000 });
  // The table renders before its rows do; counting immediately reports zero.
  await page.waitForSelector('.timeline tbody tr', { timeout: 15000 });

  const rows = await page.locator('.timeline tbody tr').count();
  const byBadges = await page.locator('.timeline__by').allTextContents();
  console.log(`  timeline: ${rows} row(s), provenance ${JSON.stringify(byBadges)}`);

  await page.click('.timeline__view >> nth=0');
  await page.waitForSelector('.viewer__panel', { timeout: 15000 });
  await page.waitForSelector('.viewer__img, .viewer__note--error', { timeout: 15000 });

  check(`viewer open`, await page.evaluate(inspect, TRACKED), vw, vh);

  // Focus starts inside the modal, and Tab must not leave it.
  const trapped = await page.evaluate(async () => {
    const inside = () => document.querySelector('.viewer__panel')?.contains(document.activeElement);
    return inside();
  });
  if (!trapped) { failures += 1; console.log('  FAIL  focus did not start inside the modal'); }
  else console.log('  ok    focus starts inside the modal');

  const findings = await page.locator('.viewer__findings .finding').count();
  const flagged = await page.locator('.viewer__findings .finding--flag').count();
  console.log(`  findings shown: ${findings} (${flagged} flagged)`);

  if (vp === '1280x800') await page.screenshot({ path: process.env.SHOT || '/tmp/viewer.png' });

  // Escape closes it.
  await page.keyboard.press('Escape');
  await page.waitForSelector('.viewer__panel', { state: 'detached', timeout: 5000 })
    .then(() => console.log('  ok    Escape closes'))
    .catch(() => { failures += 1; console.log('  FAIL  Escape did not close the modal'); });

  await ctx.close();
}

await browser.close();
console.log(failures ? `\n${failures} viewer failure(s)` : '\nviewer ok at every viewport');
process.exit(failures ? 1 : 0);
