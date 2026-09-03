// Owner: Nikki
//
// Layout guard. Walks a real interview in a real browser and fails if anything
// overlaps, hides behind the bottom bar, or makes the page scroll.
//
//   node e2e/layout.mjs                 # all viewports, Hindi
//   node e2e/layout.mjs 1280x800        # one viewport
//   node e2e/layout.mjs 1280x800 తెలుగు # one viewport, another language
//
// Exits non-zero on the first failure, so it can gate a commit.
//
// WHY MORE THAN ONE VIEWPORT: the Next-over-transcript overlap was "fixed and
// verified across 22 screens" on Sep 1, and came back — except it never left.
// The fix lived inside @media (min-width:1100px) and (max-height:900px), and
// every audit ran at 1280x800, which is inside that band. Outside it the
// collision was untouched and simply waited for the content to grow: a
// two-line phase label, translated panel values, bilingual danger tiles. One
// viewport is not a layout test, it is a spot check.
//
// WHY IT WALKS TO THE END: earlier audits stopped after three interview
// screens and never reached the danger-symptom question, which carries the
// most tiles and the most text. The screens most likely to break are the ones
// furthest into the flow.

import { chromium } from '@playwright/test';

const BASE = process.env.KIOSK_URL || 'http://localhost:5173';

// 1280x800 is the kiosk. The rest are the windows a demo actually gets run in,
// and two of them sit outside the landscape media query on purpose.
const VIEWPORTS = ['1280x800', '1024x768', '1280x1024', '1440x900', '1366x768'];

const LANGS = {
  हिन्दी: '^एक क्षण|^One moment',
  తెలుగు: '^ఒక్క? క్షణం|^One moment',
  English: '^One moment',
};

// Everything a patient has to be able to see and reach at once.
const TRACKED = [
  '.shell__phase', '.shell__question', '.grid-2', '.grid-3', '.mic-block',
  '.transcript', '.understanding', '.btn--primary', '.shell__bar',
  '.listen--question', '.interview__row', '.consent__text', '.stack',
  '.consent__actions', '.keypad',
];

function inspect(tracked) {
  const boxes = [];
  for (const sel of tracked) {
    for (const el of document.querySelectorAll(sel)) {
      const r = el.getBoundingClientRect();
      if (r.width && r.height) {
        boxes.push({ sel, t: Math.round(r.top), b: Math.round(r.bottom),
                     l: Math.round(r.left), r: Math.round(r.right) });
      }
    }
  }
  const overlaps = [];
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const A = boxes[i], B = boxes[j];
      if (A.sel === B.sel) continue;
      // A row legitimately contains its children; that is not a collision.
      const holds = (X, Y) => X.t <= Y.t && X.b >= Y.b && X.l <= Y.l && X.r >= Y.r;
      if (holds(A, B) || holds(B, A)) continue;
      if (A.l < B.r && B.l < A.r && A.t < B.b && B.t < A.b) {
        overlaps.push(`${A.sel}[${A.t}-${A.b}] over ${B.sel}[${B.t}-${B.b}]`);
      }
    }
  }
  const bar = document.querySelector('.shell__bar')?.getBoundingClientRect();
  const behindBar = boxes
    .filter((x) => bar && x.sel !== '.shell__bar' && x.b > bar.top + 1)
    .map((x) => `${x.sel} reaches ${x.b}, bar starts ${Math.round(bar.top)}`);
  // Contrast of the bilingual English line against whatever it actually sits
  // on. It was set to --ink-soft regardless of background, which scored
  // 1.04:1 on the filled primary button — the most important control on the
  // screen, effectively invisible. Measured rather than assumed, because the
  // fix is a list of filled classes and a new one can be added and forgotten.
  const lum = (c) => {
    const f = (x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
  };
  const parse = (v) => (v.match(/[\d.]+/g) || []).map(Number);
  const backdrop = (el) => {
    for (let n = el; n; n = n.parentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c.length >= 3 && (c[3] === undefined || c[3] > 0.5)) return c.slice(0, 3);
    }
    return [255, 255, 255];
  };
  const lowContrast = [];
  for (const el of document.querySelectorAll('.bilingual__english')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const fg = parse(getComputedStyle(el).color).slice(0, 3);
    const bg = backdrop(el);
    const a = lum(fg), b = lum(bg);
    const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    if (ratio < 4.5) {
      const owner = el.closest('[class]')?.className || '?';
      lowContrast.push(`${ratio.toFixed(2)}:1 "${(el.textContent || '').trim().slice(0, 20)}" in .${String(owner).split(/\s+/)[0]}`);
    }
  }

  const panel = document.querySelector('.understanding');
  return {
    overlaps, behindBar, lowContrast,
    pageScrolls: document.documentElement.scrollHeight > window.innerHeight,
    // The panel may scroll internally by design; the transcript may not.
    transcriptClipped: (() => {
      const t = document.querySelector('.transcript__input');
      return t ? t.scrollHeight > t.clientHeight + 4 : false;
    })(),
    panelRows: document.querySelectorAll('.understanding__item').length,
    tiles: document.querySelectorAll('.tile').length,
    hasPanel: !!panel,
  };
}

let failures = 0;

async function run(size, langName) {
  const [width, height] = size.split('x').map(Number);
  const loading = LANGS[langName];
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height } });
  console.log(`\n=== ${size}  ${langName} ===`);

  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.locator('button').first().click();
  await page.waitForTimeout(1800);
  await page.locator('button', { hasText: langName }).first().click();
  await page.waitForTimeout(2200);

  const settle = async () => {
    for (let i = 0; i < 130; i++) {
      const h = await page.locator('h1').first().innerText().catch(() => '');
      if (h && !new RegExp(loading).test(h)) return h;
      await page.waitForTimeout(500);
    }
    return '';
  };

  let worstCaseSeen = false;
  let realScreens = 0;

  for (let step = 0; step < 20; step++) {
    const heading = await settle();
    if (!heading) break;

    const r = await page.evaluate(inspect, TRACKED);
    const bad =
      r.overlaps.length || r.behindBar.length || r.pageScrolls || r.transcriptClipped
      || r.lowContrast.length;
    const name = `step ${step} "${heading.split('\n')[0].slice(0, 22)}" tiles=${r.tiles} panelRows=${r.panelRows}`;

    // The case the whole layout has to survive: tiles, mic, transcript,
    // understanding panel and bilingual text all present together.
    if (r.tiles >= 4 && r.hasPanel && r.panelRows > 0) worstCaseSeen = true;
    // An error screen has no tiles, no transcript and no panel, and it passes
    // every geometric check there is. A run that sat on one and reported
    // "clean" is the same false assurance this harness exists to remove.
    if (r.tiles > 0 || r.hasPanel) realScreens++;
    if (/^(कुछ गड़बड़|Something went wrong|ఏదో పొరపాటు)/.test(heading)) {
      failures++;
      console.log(`  FAIL  step ${step}: ERROR SCREEN — the app is broken, not the layout.`
        + ' Check the backend (the Gemini free tier is 20 requests/day).');
      break;
    }

    if (bad) {
      failures++;
      console.log(`  FAIL  ${name}`);
      r.overlaps.forEach((o) => console.log(`        OVERLAP: ${o}`));
      r.behindBar.forEach((o) => console.log(`        BEHIND BAR: ${o}`));
      if (r.pageScrolls) console.log('        PAGE SCROLLS');
      if (r.transcriptClipped) console.log('        TRANSCRIPT CLIPPED (it must never be the thing that shrinks)');
      r.lowContrast.forEach((c) => console.log(`        CONTRAST below 4.5:1 — ${c}`));
    } else {
      console.log(`  ok    ${name}`);
    }

    if (await page.locator('.emergency').count()) break;

    const tile = page.locator('.tile').first();
    const key = page.locator('.keypad__key').first();
    if (await tile.count()) { await tile.click(); await page.waitForTimeout(450); }
    else if (await key.count()) {
      for (let n = 0; n < 3; n++) {
        await page.locator('.keypad__key').nth(n).click();
        await page.waitForTimeout(80);
      }
    }
    const primary = page.locator('.btn--primary:not([disabled])').first();
    if (await primary.count()) { await primary.click(); await page.waitForTimeout(1400); }
    else {
      // Never the Listen button: pressing it is a real utterance, not navigation.
      const other = page.locator('.shell__main button:not([disabled]):not(.listen)').last();
      if (await other.count()) { await other.click(); await page.waitForTimeout(1400); }
      else await page.waitForTimeout(1200);
    }
  }

  if (realScreens < 3) {
    failures++;
    console.log(`  FAIL  only ${realScreens} screen(s) with any content were reached; `
      + 'the walk never got into the interview, so this run proves nothing');
  }

  if (!worstCaseSeen) {
    // Not a failure: how many options a question carries is the model's
    // choice, so a run can legitimately miss the heaviest screen. It is not a
    // clean bill of health either, and saying so is the whole point.
    console.log('  WARN  no screen this run had 4+ tiles AND a populated panel; '
      + 'the heaviest layout went untested here');
  }
  await browser.close();
}

const [sizeArg, langArg] = process.argv.slice(2);
const sizes = sizeArg ? [sizeArg] : VIEWPORTS;
const lang = langArg || 'हिन्दी';
for (const size of sizes) await run(size, lang);

console.log(failures ? `\n${failures} layout failure(s)\n` : '\nlayout clean\n');
process.exit(failures ? 1 : 0);
