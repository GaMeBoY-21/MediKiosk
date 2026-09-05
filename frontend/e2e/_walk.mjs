import { chromium } from '@playwright/test';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1280, height: 800 } });
const errs=[]; p.on('pageerror',e=>errs.push(String(e).slice(0,70)));
const seen=[];
await p.goto('http://localhost:5173', { waitUntil: 'networkidle' });
const card = p.locator('.role-card').first();
if (await card.count()) { await card.click(); await p.waitForTimeout(700); }
await p.locator('button').first().click(); await p.waitForTimeout(900);
await p.locator('button', { hasText: 'हिन्दी' }).first().click(); await p.waitForTimeout(1800);
const settle=async()=>{for(let i=0;i<170;i++){const h=await p.locator('h1').first().innerText({timeout:2000}).catch(()=>'');if(h&&!/^एक क्षण|^One moment/.test(h))return h;await p.waitForTimeout(500);}return'';};
let questions=0, described=false, token=null;
for (let i=0;i<32;i++){
  const h=await settle(); if(!h) break;
  const label=h.split('\n')[0].slice(0,30);
  const geom=await p.evaluate(()=>{const bar=document.querySelector('.shell__bar')?.getBoundingClientRect();
    const btns=[...document.querySelectorAll('.btn--primary,.btn--outline')].map(x=>x.getBoundingClientRect());
    const low=btns.length?Math.max(...btns.map(x=>x.bottom)):null;
    return {scroll:document.documentElement.scrollHeight>innerHeight, behind:!!(bar&&low&&low>bar.top+1)};});
  if (!seen.length || seen[seen.length-1].label!==label) seen.push({label, ...geom});
  if (await p.locator('.emergency').count()) { seen.push({label:'-> EMERGENCY'}); break; }
  if (await p.locator('.readback').count()) {
    const rows=await p.locator('.readback__item').count();
    seen.push({label:`-> Confirm (${rows} rows)`});
    await p.locator('.btn--primary:not([disabled])').first().click({timeout:5000}).catch(()=>{});
    await p.waitForTimeout(3500);
    token=await p.evaluate(()=>{const m=document.body.innerText.match(/\bA-\d+\b/);return m?m[0]:null;});
    break;
  }
  // The new opening description: type a rich narration once.
  if (await p.locator('.describe__or').count() && !described) {
    await p.locator('.transcript__input').fill('मुझे तीन दिन से सिर में तेज़ धड़कने जैसा दर्द है, सुबह शुरू हुआ, तेज़ रोशनी से बढ़ता है। मुझे शुगर है, मैं मेटफॉर्मिन लेता हूँ, एलर्जी नहीं है, माँ को माइग्रेन है, धूम्रपान नहीं करता, शराब नहीं पीता, शाकाहारी हूँ।');
    described=true;
    await p.waitForTimeout(300);
    await p.locator('.btn--primary:not([disabled])').first().click({timeout:5000}).catch(()=>{});
    await p.waitForTimeout(1200);
    continue;
  }
  if (await p.locator('.interview__row').count()) questions++;
  const none=p.locator('.tile').filter({hasText:/कोई नहीं|None of these/i});
  const t=(await none.count())?none.first():p.locator('.tile').first();
  const k=p.locator('.keypad__key').first(), box=p.locator('.transcript__input');
  if (await p.locator('.tile').count()) { await t.click({timeout:4000}).catch(()=>{}); await p.waitForTimeout(400); }
  else if (await k.count()) { for(let n=0;n<3;n++) await p.locator('.keypad__key').nth(n).click({timeout:4000}).catch(()=>{}); }
  else if (await box.count()) { await box.fill('2 days',{timeout:4000}).catch(()=>{}); }
  const pr=p.locator('.btn--primary:not([disabled])').first();
  if (await pr.count()) await pr.click({timeout:4000}).catch(()=>{});
  else { const c=p.locator('.shell__main button:not([disabled]):not(.listen)').last();
         if (await c.count()) await c.click({timeout:4000}).catch(()=>{}); }
  await p.waitForTimeout(900);
}
console.log('screens:');
seen.forEach(s=>console.log(`  ${s.behind?'BEHIND-BAR':'ok        '} ${s.scroll?'SCROLLS':'       '} ${s.label}`));
console.log(`interview questions after the description: ${questions}`);
console.log(`token: ${token || '(none)'}   page errors: ${errs.length?errs:'none'}`);
await b.close();
