// Owner: Nikki
//
// Every answer the patient gave must reach the Confirm screen.
//
//   node e2e/confirm.mjs                # all seven languages
//   node e2e/confirm.mjs हिन्दी          # one
//
// Exits non-zero if any field in the clinical record is not accounted for.
//
// WHY THIS EXISTS: this is the fourth time something was dropped silently
// between a store and a render. The Confirm screen showed two rows for a
// ten-question interview, because the session store deduplicated answers by
// node_id and every history follow-up shares the node id "hpi". Nothing failed
// — there was no error, no empty state, just a shorter list than the truth.
// A unit test on the store would not have caught it either; the invariant is
// between what the SERVER recorded and what the SCREEN shows, so it has to be
// checked end to end.
//
// THE ASSERTION is coverage, not a row count. Rows are legitimately FEWER than
// fields: a field reconcile.py derives (symptom_onset, from symptom_duration)
// is shown with the answer it came from rather than as a row for a question
// nobody was asked. So every field must be claimed by exactly one row —
// none missing, none counted twice.

import { chromium } from '@playwright/test';

const BASE = process.env.KIOSK_URL || 'http://localhost:5173';

const LANGS = {
  'हिन्दी': '^एक क्षण|^One moment',
  'తెలుగు': '^ఒక్క? క్షణం|^One moment',
  'ಕನ್ನಡ': '^ಒಂದು ಕ್ಷಣ|^One moment',
  'தமிழ்': '^ஒரு நிமிடம்|^One moment',
  'मराठी': '^एक क्षण|^One moment',
  'বাংলা': '^এক মুহূর্ত|^One moment',
  'English': '^One moment',
};

// Danger-symptom tiles end the interview in the emergency screen, which is
// correct behaviour and the wrong path for this check.
const NONE_OF_THESE = /ఏదీ లేదు|कोई नहीं|ಯಾವುದೂ ಇಲ್ಲ|எதுவும் இல்லை|কোনোটিই নয়|None of these/i;

let failures = 0;

async function run(lang) {
  const loading = LANGS[lang];
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.addInitScript(() => {
    window.__extracted = null;
    const of = window.fetch;
    window.fetch = async (...a) => {
      const r = await of(...a);
      try {
        const j = await r.clone().json();
        if (j && Array.isArray(j.extracted) && j.extracted.length) window.__extracted = j.extracted;
      } catch { /* not JSON */ }
      return r;
    };
  });

  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.locator('button').first().click();
  await page.waitForTimeout(1200);
  await page.locator('button', { hasText: lang }).first().click();
  await page.waitForTimeout(2000);

  const settle = async () => {
    for (let i = 0; i < 140; i++) {
      const h = await page.locator('h1').first().innerText({ timeout: 2000 }).catch(() => '');
      if (h && !new RegExp(loading).test(h)) return h;
      await page.waitForTimeout(500);
    }
    return '';
  };

  for (let step = 0; step < 26; step++) {
    const heading = await settle();
    if (!heading) break;
    if (await page.locator('.readback').count()) break;
    if (await page.locator('.emergency').count()) break;

    const none = page.locator('.tile').filter({ hasText: NONE_OF_THESE });
    const tile = (await none.count()) ? none.first() : page.locator('.tile').first();
    const key = page.locator('.keypad__key').first();
    const box = page.locator('.transcript__input');
    if (await page.locator('.tile').count()) {
      await tile.click({ timeout: 3000 }).catch(() => {});
      await page.waitForTimeout(300);
    } else if (await key.count()) {
      for (let n = 0; n < 3; n++) {
        await page.locator('.keypad__key').nth(n).click({ timeout: 3000 }).catch(() => {});
      }
    } else if (await box.count()) {
      await box.fill('2 days', { timeout: 3000 }).catch(() => {});
    }
    const primary = page.locator('.btn--primary:not([disabled])').first();
    if (await primary.count()) await primary.click({ timeout: 3000 }).catch(() => {});
    else {
      const other = page.locator('.shell__main button:not([disabled]):not(.listen)').last();
      if (await other.count()) await other.click({ timeout: 3000 }).catch(() => {});
    }
    await page.waitForTimeout(900);
  }

  if (!(await page.locator('.readback').count())) {
    failures++;
    console.log(`  FAIL  ${lang}: never reached the Confirm screen`);
    await browser.close();
    return;
  }

  const rows = await page.locator('.readback__item').count();
  const fields = await page.evaluate(() => (window.__extracted || []).map((f) => f.name));
  const claimed = await page.evaluate(() => window.__rowFields || []);
  // English sessions render one line, not two: there is no second language to
  // show underneath. Only the other six owe an English counterpart.
  const noEnglish = lang === 'English' ? 0 : await page.evaluate(() =>
    [...document.querySelectorAll('.readback__q')].filter(
      (q) => !q.querySelector('.bilingual__english'),
    ).length,
  );
  const geom = await page.evaluate(() => {
    const bar = document.querySelector('.shell__bar')?.getBoundingClientRect();
    const btn = document.querySelector('.btn--primary')?.getBoundingClientRect();
    return {
      pageScrolls: document.documentElement.scrollHeight > window.innerHeight,
      nextBehindBar: !!(bar && btn && btn.bottom > bar.top + 1),
    };
  });

  const counts = {};
  for (const row of claimed) for (const f of row.fields) counts[f] = (counts[f] || 0) + 1;
  const missing = fields.filter((n) => !counts[n]);
  const twice = Object.entries(counts).filter(([, c]) => c > 1).map(([n]) => n);
  const bad =
    missing.length || twice.length || geom.pageScrolls || geom.nextBehindBar || noEnglish;

  if (bad) failures++;
  console.log(
    `  ${bad ? 'FAIL' : 'ok  '}  ${lang.padEnd(8)} rows=${rows} fields=${fields.length} ` +
      `covered=${fields.length - missing.length}/${fields.length}`,
  );
  if (missing.length) console.log(`        DROPPED between store and screen: ${missing.join(', ')}`);
  if (twice.length) console.log(`        claimed by more than one row: ${twice.join(', ')}`);
  if (noEnglish) console.log(`        ${noEnglish} question(s) with no English line`);
  if (geom.pageScrolls) console.log('        PAGE SCROLLS');
  if (geom.nextBehindBar) console.log('        Next is behind the bottom bar');
  await browser.close();
}

const only = process.argv[2];
for (const lang of only ? [only] : Object.keys(LANGS)) await run(lang);
console.log(failures ? `\n${failures} language(s) failed\n` : '\nevery answer reaches Confirm\n');
process.exit(failures ? 1 : 0);
