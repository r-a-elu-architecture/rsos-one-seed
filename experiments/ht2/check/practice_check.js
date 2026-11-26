// Headless check of practice mode: 3 simulated sessions, gate, HT2 lock, learning curve. N1-N4 are never started.
// Usage: node practice_check.js <page> <cases.json> <screenshot-dir>
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [page, casesPath, shots] = process.argv.slice(2);
  const cases = JSON.parse(fs.readFileSync(casesPath, 'utf8'));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.setContent('<!doctype html><html><head><meta charset="utf-8"></head><body>' + fs.readFileSync(page, 'utf8') + '</body></html>');
  const out = { checks: {} };
  out.checks.test_locked_before = await p.evaluate(() => { document.getElementById('m-test').click(); const r = document.getElementById('start').disabled; document.getElementById('m-practice').click(); return r; });
  const delays = [60, 62, 64]; // ms per key in sessions 1-3: spread 6.7% < 10%
  for (let s = 0; s < 3; s++) {
    for (let t = 0; t < 6; t++) {
      const id = (await p.$eval('#task', el => el.options[el.selectedIndex].text)).split(' ')[0];
      await p.click('#start');
      for (const k of cases[id].keys.match(/TRIG:.*$|\S+/g)) {
        if (k.startsWith('TRIG:')) { await p.keyboard.press('Shift+K'); const inp = p.locator('.frame.cur input'); await inp.fill(k.slice(5)); await inp.press('Enter'); }
        else await p.keyboard.press(/^[A-Z]$/.test(k) ? 'Shift+' + k : k);
        await p.waitForTimeout(delays[s]);
      }
      out[`s${s + 1}_${id}_rsos_ok`] = (await p.evaluate(() => __rsosKB.compile())) === cases[id].rsos;
      await p.click('#done');
    }
  }
  out.sessions = await p.evaluate(() => __rsosKB.sessions());
  out.gate = await p.evaluate(() => { const g = __rsosKB.gate(); return { met: g.met, ratio: g.ratio }; });
  out.checks.test_unlocked_after = await p.evaluate(() => { document.getElementById('m-test').click(); return !document.getElementById('start').disabled; });
  out.checks.test_first_task = await p.$eval('#task', el => el.options[el.selectedIndex].text);
  out.checks.sealed_not_decoded = await p.evaluate(() => !document.body.innerText.includes('N1 ·  '));
  await p.evaluate(() => document.getElementById('m-practice').click());
  out.checks.export_has_gate = JSON.parse(await p.inputValue('#export')).gate;
  out.errors = errs;
  await p.screenshot({ path: shots + '/practice_desktop.png', fullPage: true });
  await p.setViewportSize({ width: 400, height: 900 }); await p.screenshot({ path: shots + '/practice_phone.png', fullPage: true });
  console.log(JSON.stringify(out, null, 1)); await b.close();
})();
