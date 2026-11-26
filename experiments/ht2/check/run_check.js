// Headless functional check of docs/keyboard.html (HT2 amendment 1). Usage: node run_check.js <page> <cases.json> <out.json>
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [page, casesPath, outPath] = process.argv.slice(2);
  const cases = JSON.parse(fs.readFileSync(casesPath, 'utf8'));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.setContent('<!doctype html><html><head><meta charset="utf-8"></head><body>' + fs.readFileSync(page, 'utf8') + '</body></html>');
  await p.waitForTimeout(300);
  const out = {};
  for (const [id, c] of Object.entries(cases)) {
    await p.evaluate(() => __rsosKB.reset());
    const toks = c.keys.match(/TRIG:.*$|\S+/g);
    for (const k of toks) {
      if (k.startsWith('TRIG:')) {
        await p.keyboard.press('Shift+K');
        const inp = p.locator('.frame.cur input');
        await inp.fill(k.slice(5)); await inp.press('Enter');
      } else await p.keyboard.press(/^[A-Z]$/.test(k) ? 'Shift+' + k : k);
    }
    const rsos = await p.evaluate(() => __rsosKB.compile());
    const plain = await p.evaluate(() => __rsosKB.plain());
    const status = await p.textContent('#slotstatus');
    const missing = c.plain.filter(w => !plain.toLowerCase().includes(w.toLowerCase()));
    out[id] = { keys: c.keys, rsos, expected: c.rsos, rsos_match: rsos === c.rsos, plain, plain_missing: missing, slot_status: status };
  }
  fs.writeFileSync(outPath, JSON.stringify({ page, errors: errs, results: out }, null, 1));
  await b.close();
})();
