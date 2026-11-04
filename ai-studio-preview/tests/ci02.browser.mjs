import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';

const base = 'http://127.0.0.1:4173/';
const out = 'ci02-evidence';
await mkdir(out, { recursive: true });
const evidence = { revision: process.env.GITHUB_SHA || 'unknown', checks: [], blockedExternal: [], pageErrors: [], consoleErrors: [], noCredentials: true, noSignIn: true };
const record = (name, passed, detail) => {
  evidence.checks.push({ name, result: passed ? 'PASS' : 'FAIL', detail });
  console.log((passed ? 'PASS ' : 'FAIL ') + name + ': ' + detail);
};
const browser = await chromium.launch({ headless: true, args: ['--disable-background-networking', '--no-first-run'] });
try {
  for (const device of [{ name: 'desktop', width: 1440, height: 900 }, { name: 'mobile', width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport: { width: device.width, height: device.height }, serviceWorkers: 'block', permissions: [] });
    await context.route('**/*', async route => {
      const url = route.request().url();
      const host = new URL(url).hostname;
      if (host === 'localhost' || host === '127.0.0.1') await route.continue();
      else {
        evidence.blockedExternal.push({ device: device.name, origin: new URL(url).origin, method: route.request().method() });
        await route.abort('blockedbyclient');
      }
    });
    const page = await context.newPage();
    page.on('pageerror', e => evidence.pageErrors.push({ device: device.name, message: e.message }));
    page.on('console', m => { if (m.type() === 'error' && evidence.consoleErrors.length < 25) evidence.consoleErrors.push({ device: device.name, text: m.text().slice(0, 350) }); });
    let loaded = false;
    let loadDetail = 'HTTP 200 and visible application shell';
    try {
      const response = await page.goto(base, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.getByText('RESEARCH_REPO', { exact: true }).first().waitFor({ state: 'visible', timeout: 15000 });
      loaded = response?.status() === 200 && (await page.locator('main').isVisible());
    } catch (e) { loadDetail = String(e).slice(0, 300); }
    record('load-' + device.name, loaded, loadDetail);
    if (!loaded) { await page.screenshot({ path: out + '/' + device.name + '-load-failed.png' }).catch(() => null); await context.close(); continue; }
    await page.screenshot({ path: out + '/' + device.name + '-terminal.png', fullPage: true });
    const nav = ['Academic Terminal', 'Repo Scoring Agent', 'Knowledge Graph', 'TypeSafe Evidence', 'Reports & Whitepaper', 'Pipeline Guardrails'];
    const results = [];
    for (const name of nav) {
      try {
        await page.getByRole('button', { name, exact: true }).click({ timeout: 8000 });
        const text = (await page.locator('main').innerText()).trim();
        results.push({ tab: name, rendered: text.length > 150, chars: text.length });
      } catch (e) { results.push({ tab: name, rendered: false, error: String(e).slice(0, 180) }); }
    }
    record('navigation-' + device.name, results.every(x => x.rendered), JSON.stringify(results));
    const disclosure = /\b(?:simulated (?:data|papers?|results?|research|pipeline)|synthetic (?:data|papers?|results?|research)|demo (?:mode|only|data)|mock data|no live retrieval|not verified|not connected to (?:arxiv|github|typesafe|firebase))\b/i;
    try {
      await page.getByRole('button', { name: 'Repo Scoring Agent', exact: true }).click();
      const text = await page.locator('main').innerText();
      const hasClaim = /LLM relevance scoring|Querying GitHub Search API/i.test(text);
      record('scoring-disclosure-' + device.name, !hasClaim || disclosure.test(text), 'Claims real scoring=' + hasClaim + ', visible simulation disclosure=' + disclosure.test(text));
      await page.screenshot({ path: out + '/' + device.name + '-scoring.png', fullPage: true });
      await page.getByRole('button', { name: 'Academic Terminal', exact: true }).click();
      const paperText = await page.locator('main').innerText();
      const liveClaim = /Live retrieval/i.test(paperText);
      record('academic-disclosure-' + device.name, !liveClaim || disclosure.test(paperText), 'Claims live retrieval=' + liveClaim + ', visible simulation disclosure=' + disclosure.test(paperText));
    } catch (e) { record('research-disclosure-' + device.name, false, String(e).slice(0, 220)); }
    try {
      await page.getByRole('button', { name: 'TypeSafe Evidence', exact: true }).click();
      await page.getByRole('button', { name: 'Assess Evidence', exact: true }).click({ timeout: 7000 });
      await page.waitForTimeout(1100);
      const typeText = await page.locator('main').innerText();
      const receiptVisible = /SHA-256 Input Hash/i.test(typeText) && /NOT_PROMOTED/i.test(typeText);
      const isMarkedAsLocal = /local heuristics?|simulated classification|mock classifier|not (?:a|the) (?:real )?provider|not connected to typesafe/i.test(typeText);
      record('typesafe-receipt-' + device.name, receiptVisible, 'Evaluation receipt displayed=' + receiptVisible);
      record('typesafe-provider-disclosure-' + device.name, isMarkedAsLocal, 'Local-rule simulator clearly disclosed=' + isMarkedAsLocal);
      await page.screenshot({ path: out + '/' + device.name + '-typesafe.png', fullPage: true });
    } catch (e) { record('typesafe-inspection-' + device.name, false, String(e).slice(0, 260)); }
    await context.close();
  }
} finally { await browser.close(); }
const firebase = evidence.blockedExternal.filter(r => /firestore|firebase|googleapis|identitytoolkit|securetoken/i.test(r.origin));
record('external-connection-isolation', true, 'Every non-local request aborted, count=' + evidence.blockedExternal.length);
record('firebase-startup-zero-attempts', firebase.length === 0, 'Firebase-like network attempts=' + firebase.length);
record('uncaught-browser-errors', evidence.pageErrors.length === 0, 'Count=' + evidence.pageErrors.length);
evidence.overall = evidence.checks.every(c => c.result === 'PASS') ? 'PASS' : 'FAIL';
await writeFile(out + '/ci02-report.json', JSON.stringify(evidence, null, 2));
console.log('CI02_OVERALL=' + evidence.overall);
process.exitCode = evidence.overall === 'PASS' ? 0 : 1;
