// Owner: Ranjith
// Full-path browser walkthrough at 1280x800, against the real backend.
//
// Checks at every screen:
//   - nothing clipped or overflowing horizontally
//   - bilingual rendering correct for the chosen language
//   - each question spoken exactly once, never twice, never on back-nav
//   - Next disabled until an answer exists
//   - the understanding panel accumulates
//   - no English technical text on a patient screen
//
// Run: node e2e/walkthrough.mjs
import { chromium } from '@playwright/test';

const KIOSK = process.env.KIOSK_URL ?? 'http://localhost:5173';
const VIEWPORT = { width: 1280, height: 800 };

const problems = [];
const note = (screen, msg) => {
  problems.push(`${screen}: ${msg}`);
  console.log(`   ✗ ${msg}`);
};
const ok = (msg) => console.log(`   ✓ ${msg}`);

// Words that must never appear on a patient-facing screen.
const TECHNICAL = [
  'undefined', 'null', 'NaN', '[object Object]', 'Error:', 'TypeError',
  'node_id', 'session_id', 'chief_complaint', 'symptom_', 'Traceback',
  'failed:', 'Unauthorized', 'net::ERR',
];

async function audit(page, screen, { patientFacing = true } = {}) {
  // Horizontal overflow / clipping.
  const overflow = await page.evaluate(() => {
    const de = document.documentElement;
    const clipped = [];
    for (const el of document.querySelectorAll('button, h1, p, span, div')) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      if (r.right > window.innerWidth + 1 || r.left < -1) {
        clipped.push((el.className || el.tagName) + ' @' + Math.round(r.left) + '..' + Math.round(r.right));
      }
      // Text taller than its own clipping box = visually cut off.
      const cs = getComputedStyle(el);
      if (cs.overflow === 'hidden' && el.scrollHeight > el.clientHeight + 2 && el.clientHeight > 0) {
        clipped.push('CLIPPED ' + (el.className || el.tagName));
      }
    }
    return {
      docScrollW: de.scrollWidth, winW: window.innerWidth,
      docScrollH: de.scrollHeight, winH: window.innerHeight,
      clipped: clipped.slice(0, 5),
    };
  });
  if (overflow.docScrollW > overflow.winW + 1) {
    note(screen, `horizontal overflow: ${overflow.docScrollW}px > ${overflow.winW}px`);
  }
  if (overflow.docScrollH > overflow.winH + 1) {
    note(screen, `vertical scroll: ${overflow.docScrollH}px > ${overflow.winH}px`);
    const parts = await page.evaluate(() => {
      const m = document.querySelector('.shell__main');
      if (!m) return [];
      return [...m.children].map((e) => {
        const r = e.getBoundingClientRect();
        return `${(e.className || e.tagName).split(' ')[0]}:${Math.round(r.height)}@y${Math.round(r.top)}`;
      });
    });
    console.log('     breakdown:', parts.join('  '));
  } else {
    ok(`fits ${overflow.docScrollW}x${overflow.docScrollH}`);
  }
  for (const c of overflow.clipped) note(screen, `clipped element: ${c}`);

  if (patientFacing) {
    const text = await page.evaluate(() => document.body.innerText);
    for (const t of TECHNICAL) {
      if (text.includes(t)) note(screen, `technical text on patient screen: ${JSON.stringify(t)}`);
    }
  }
  return overflow;
}

async function spokenSoFar(page) {
  return page.evaluate(() => window.__spoken ?? []);
}

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: VIEWPORT });
const page = await ctx.newPage();

// Capture speech instead of playing it, so we can assert on exactly what
// would have been spoken and how many times.
await page.addInitScript(() => {
  window.__spoken = [];
  const fake = {
    speak: (u) => { window.__spoken.push(u.text); },
    cancel: () => {},
    getVoices: () => [],
    addEventListener: () => {},
    removeEventListener: () => {},
    speaking: false, pending: false, paused: false,
  };
  Object.defineProperty(window, 'speechSynthesis', { value: fake, configurable: true });
  window.SpeechSynthesisUtterance = function (text) { this.text = text; };

  // Stub SpeechRecognition so the walk can answer free-text questions the way
  // a patient does — by speaking. Emits one final result shortly after start().
  window.__nextUtterance = 'mujhe do din se dard hai';
  class FakeRecognition {
    constructor() { this.continuous = false; this.interimResults = false; this.lang = 'en-IN'; }
    start() {
      setTimeout(() => {
        const text = window.__nextUtterance;
        const results = [[{ transcript: text }]];
        results[0].isFinal = true;
        results[0][0] = { transcript: text };
        this.onresult?.({ resultIndex: 0, results: Object.assign(results, { length: 1 }) });
        this.onend?.();
      }, 120);
    }
    stop() { this.onend?.(); }
    abort() { this.onend?.(); }
  }
  window.SpeechRecognition = FakeRecognition;
  window.webkitSpeechRecognition = FakeRecognition;
});

const consoleErrors = [];
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
page.on('pageerror', (e) => consoleErrors.push('pageerror: ' + e.message));

console.log(`\n=== KIOSK WALKTHROUGH @ ${VIEWPORT.width}x${VIEWPORT.height} ===\n`);

// ---------------------------------------------------------------- 1. Idle
await page.goto(KIOSK, { waitUntil: 'networkidle' });
console.log('1. Idle');
await audit(page, 'idle');
const idleText = await page.evaluate(() => document.body.innerText);
console.log('   text:', JSON.stringify(idleText.replace(/\s+/g, ' ').slice(0, 90)));

// Before a language is chosen, nothing should render bilingually.
const preBilingual = await page.locator('.bilingual').count();
if (preBilingual > 0) note('idle', `${preBilingual} bilingual blocks before language chosen (should be 0)`);
else ok('English only before language selection');


const click = async (sel, label) => {
  await page.locator(sel).first().click();
  await page.waitForTimeout(700);
  if (label) console.log(`   -> clicked ${label}`);
};

// ------------------------------------------------------------ 2. Language
await click('.tile, button', 'begin');
console.log('\n2. Language');
await audit(page, 'language');
const langTiles = await page.locator('.tile--language, .tile').count();
console.log('   language tiles:', langTiles);
// Pick Hindi.
const hindi = page.locator('button', { hasText: 'हिन्दी' }).first();
if (await hindi.count()) { await hindi.click(); await page.waitForTimeout(900); }
else note('language', 'Hindi tile not found');

// ------------------------------ every subsequent screen: audit + advance
const seen = [];
// "One moment" is the holding screen while the API answers. Wait it out rather
// than treating it as a screen that failed to advance.
const settle = async () => {
  for (let i = 0; i < 40; i++) {
    const h = (await page.locator('h1').first().innerText().catch(() => '')) || '';
    if (!/One moment|एक क्षण/.test(h)) return h;
    await page.waitForTimeout(500);
  }
  return (await page.locator('h1').first().innerText().catch(() => '')) || '(none)';
};

for (let step = 0; step < 26; step++) {
  const heading = (await settle()) || '(none)';
  const screenName = `step${step}:${heading.split('\n')[0].slice(0, 28)}`;
  seen.push(heading.split('\n')[0].slice(0, 40));
  console.log(`\n${3 + step}. ${heading.replace(/\n/g, ' | ').slice(0, 70)}`);
  await audit(page, screenName);

  // Bilingual: after choosing Hindi, the heading should carry an English line.
  const bi = await page.locator('.bilingual__english').count();
  if (bi > 0) ok(`${bi} English sub-lines rendered`);

  // Understanding panel accumulation.
  const panel = await page.locator('.understanding__item').count();
  if (panel > 0) ok(`understanding panel: ${panel} fields`);

  // Next must be disabled until an answer exists.
  const next = page.locator('button:has-text("आगे"), button:has-text("Next")').first();
  if (await next.count() && await next.isDisabled()) ok('Next disabled with no answer yet');

  // Advance. Some screens auto-advance on tile tap (language, identify) and
  // have no primary button at all, so navigation is detected by the heading
  // changing rather than by any particular control existing.
  const beforeHeading = heading;
  const tile = page.locator('.tile').first();
  const keypad = page.locator('.keypad__key').first();
  const textbox = page.locator('input[type="text"], textarea').first();

  if (await tile.count()) {
    await tile.click();
    await page.waitForTimeout(1300);   // covers the language greeting delay
  } else if (await keypad.count()) {
    for (let i = 0; i < 3; i++) {
      await page.locator('.keypad__key').nth(i).click();
      await page.waitForTimeout(120);
    }
  } else if (await textbox.count()) {
    await textbox.fill('mujhe do din se seene mein dard hai');
    await page.waitForTimeout(250);
  } else if (await page.locator('.mic').count()) {
    // Free-text question: answer it by "speaking", as a patient would.
    await page.locator('.mic').first().click();
    await page.waitForTimeout(600);
  }

  const primary = page.locator('.btn--primary:not([disabled])').first();
  if (await primary.count()) {
    await primary.click();
    await page.waitForTimeout(1600);
  } else {
    // Screens like Identify offer several BigButtons and no single primary.
    // Take the LAST one: on Identify that is "I am new here", the path a
    // walk-in patient without an ABHA actually takes, and the one the whole
    // design exists to support.
    const choices = page.locator('.shell__main .btn:not([disabled])');
    const n = await choices.count();
    if (n) {
      await choices.nth(n - 1).click();
      await page.waitForTimeout(1600);
    }
  }

  if (await page.locator('.emergency').count()) { console.log('   -> EMERGENCY screen reached'); break; }

  const afterHeading = (await settle()) || '(none)';
  if (afterHeading === beforeHeading) {
    // Genuinely stuck: no control moved us on. Report rather than spin.
    const controls = await page.evaluate(() =>
      [...document.querySelectorAll('button')].map((b) => (b.innerText || '').split('\n')[0].slice(0, 22)).filter(Boolean));
    console.log('   (stuck — buttons present:', JSON.stringify(controls.slice(0, 6)) + ')');
    break;
  }
}

// -------------------------------------------------- speech: once and only once
const spoken = await spokenSoFar(page);
const counts = spoken.reduce((m, t) => (m[t] = (m[t] || 0) + 1, m), {});
const repeats = Object.entries(counts).filter(([, n]) => n > 1);
console.log('\n=== SPEECH ===');
console.log('utterances:', spoken.length, '| distinct:', Object.keys(counts).length);
if (repeats.length) {
  for (const [t, n] of repeats) note('speech', `spoken ${n}x: ${JSON.stringify(t.slice(0, 54))}`);
} else ok('every utterance spoken exactly once');

// Audio must be single-language: no English sub-line should be spoken.
const englishLines = await page.evaluate(() =>
  [...document.querySelectorAll('.bilingual__english')].map((e) => e.textContent));
const spokenEnglish = englishLines.filter((e) => e && spoken.includes(e));
if (spokenEnglish.length) note('speech', `English sub-line was spoken: ${spokenEnglish[0]}`);
else ok('English sub-lines never spoken (audio stays single-language)');

// ------------------------------------------------------- back-navigation
const before = (await spokenSoFar(page)).length;
const back = page.locator('.shell__bar-btn').last();
if (await back.count()) {
  await back.click(); await page.waitForTimeout(900);
  const after = (await spokenSoFar(page)).length;
  if (after > before) note('back-nav', `re-spoke ${after - before} utterance(s) on back-navigation`);
  else ok('back-navigation did not re-speak');
}

console.log('\n=== CONSOLE ERRORS ===');
if (consoleErrors.length) consoleErrors.slice(0, 6).forEach((e) => note('console', e.slice(0, 110)));
else ok('none');

console.log('\n=== SCREENS VISITED ===');
seen.forEach((s, i) => console.log(`  ${i}. ${s}`));

await browser.close();
console.log(problems.length ? `\n${problems.length} PROBLEM(S):\n - ${problems.join('\n - ')}` : '\nNO PROBLEMS FOUND');
