/* Development-only browser acceptance harness. Requires Playwright and Chromium. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const base = process.env.EXPLORER_URL || 'http://127.0.0.1:8769/research/explorer/';
const output = process.env.EXPLORER_REVIEW_DIR || '.tmp/explorer-review';
let browser;
(async () => {
  await fs.mkdir(output, { recursive: true });
  browser = await chromium.launch({ headless: true });
  const results = [];
  const record = (scenario, evidence) => results.push({ scenario, result: 'passed', evidence });
  const desktop = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await desktop.newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto(base); await page.locator('#application').waitFor({ state: 'visible' });
  assert.match(await page.locator('#mode-note').innerText(), /fixture views|Source fixture mode/);
  assert.equal(await page.locator('#records tr').count(), 12);
  assert.match(await page.locator('#inspection').innerText(), /person:a/);
  record('Verified source loading and explicit mode', '12 organisational records; no accepted canonical revision; default source identity person:a.');

  await page.getByRole('tab', { name: /Conceptual/ }).click();
  assert.equal(await page.locator('#records tr').count(), 19);
  assert.match(await page.locator('#selection-state').innerText(), /retained outside/);
  assert.match(await page.locator('#inspection').innerText(), /person:a/);
  await page.getByRole('tab', { name: /OWL/ }).click();
  assert.equal(await page.locator('#records tr').count(), 22);
  assert.match(await page.locator('#selection-state').innerText(), /in the current results/);
  assert.equal(new URL(page.url()).searchParams.get('id'), 'identity:person:a');
  record('Cross-view selection and absent representation', 'Conceptual absence retains person:a; OWL/gUFO shows same identity; no nearby-record substitution.');

  await page.getByRole('tab', { name: /OWL/ }).focus();
  await page.keyboard.press('Home'); assert.equal(await page.locator('#tab-conceptual').getAttribute('aria-selected'), 'true');
  await page.keyboard.press('ArrowRight'); assert.equal(await page.locator('#tab-organisational').getAttribute('aria-selected'), 'true');
  await page.locator('button[data-identity="identity:appointment:two"]').focus(); await page.keyboard.press('Enter');
  assert.equal(new URL(page.url()).searchParams.get('id'), 'identity:appointment:two');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'inspector');
  record('Keyboard tabs and table selection', 'Home/ArrowRight switches tabs; Enter selects exact appointment:two; inspector receives focus.');

  await page.locator('#search').fill('NOT-A-RECORD-9182');
  assert.equal(await page.locator('#empty').isVisible(), true);
  assert.match(await page.locator('#selection-state').innerText(), /retained outside/);
  assert.equal(new URL(page.url()).searchParams.get('id'), 'identity:appointment:two');
  await page.getByRole('button', { name: 'Clear filters' }).click();
  assert.equal(await page.locator('#records tr').count(), 12);
  await page.locator('#domain').selectOption('source-model');
  assert.equal(await page.locator('#empty').isVisible(), true);
  await page.getByRole('button', { name: 'Clear filters' }).click();
  record('No-match and domain filters', 'No-match state is explicit; selected identity survives; clear restores 12 records.');

  await page.locator('button[data-identity="identity:person:b"]').click();
  await page.getByRole('tab', { name: /OWL/ }).click();
  await page.goBack(); assert.equal(await page.locator('#tab-organisational').getAttribute('aria-selected'), 'true');
  assert.equal(new URL(page.url()).searchParams.get('id'), 'identity:person:b');
  await page.goForward(); assert.equal(await page.locator('#tab-owl-gufo').getAttribute('aria-selected'), 'true');
  assert.match(await page.locator('#inspection').innerText(), /person:b/);
  record('Browser back/forward', 'View and exact selected source ID restore both directions.');

  await page.goto(base + '?view=organisational&id=identity%3Aunknown'); await page.locator('#application').waitFor({ state: 'visible' });
  assert.match(await page.locator('#selection-state').innerText(), /not present/);
  assert.equal(await page.locator('#inspection .identity-label').count(), 0);
  record('Unknown identity deep link', 'Unknown stays unresolved; no default identity is substituted.');

  await page.goto(base); await page.locator('#application').waitFor({ state: 'visible' });
  await page.locator('button[data-identity="identity:appointment:one"]').click(); await page.evaluate(() => scrollTo(0, 380));
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await page.screenshot({ path: path.join(output, 'desktop.png') });
  assert.deepEqual(errors, []);
  record('Desktop layout and runtime errors', '1440×1000; no document overflow or uncaught page errors.');

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
  const phone = await mobile.newPage(); const phoneErrors = []; phone.on('pageerror', e => phoneErrors.push(e.message));
  await phone.goto(base); await phone.locator('#application').waitFor({ state: 'visible' });
  assert.equal(await phone.evaluate(() => innerWidth), 390);
  assert.equal(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await phone.locator('button[data-identity="identity:person:a"]').click();
  assert.equal(await phone.evaluate(() => document.activeElement.id), 'inspector');
  await phone.screenshot({ path: path.join(output, 'mobile-inspector.png') });
  await phone.getByRole('tab', { name: /Conceptual/ }).click();
  await phone.locator('#view-panel').scrollIntoViewIfNeeded();
  await phone.screenshot({ path: path.join(output, 'mobile-view.png') });
  assert.equal(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  assert.deepEqual(phoneErrors, []);
  record('Mobile selection and responsive table alternative', '390×844; inspector focus/scroll; conceptual view; no document overflow or page errors.');

  const broken = await desktop.newPage();
  await broken.route('**/data/case/mappings.json', route => route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }));
  await broken.goto(base); await broken.locator('#load-error').waitFor({ state: 'visible' });
  assert.equal(await broken.locator('#application').isVisible(), false);
  assert.match(await broken.locator('#error-detail').innerText(), /mismatch/);
  await broken.screenshot({ path: path.join(output, 'integrity-error.png') });
  await broken.unroute('**/data/case/mappings.json'); await broken.getByRole('button', { name: 'Retry data loading' }).click();
  await broken.locator('#application').waitFor({ state: 'visible' });
  record('Artifact-integrity failure and retry', 'Altered mapping bytes fail closed before rendering; retry recovers from actual correct artifacts.');

  const missing = await desktop.newPage();
  await missing.route('**/data/manifest.json', route => route.fulfill({ status: 404, body: 'missing' }));
  await missing.goto(base); await missing.locator('#load-error').waitFor({ state: 'visible' });
  assert.equal(await missing.locator('#application').isVisible(), false);
  record('Missing manifest', 'HTTP 404 produces explicit failure and no partial view.');

  await fs.writeFile(path.join(output, 'checks.json'), JSON.stringify({ schemaVersion: 'ontograph.research.explorer-local-checks.v1', browser: 'Playwright Chromium', independent: false, results, limitations: ['Author verification, not independent acceptance or full accessibility certification.', 'Local preview assembles read-only research home PR8 with this exclusive explorer. No publication.'] }, null, 2) + '\n');
  await browser.close(); console.log(`Passed ${results.length} explorer scenarios.`);
})().catch(async error => { console.error(error); if (browser) await browser.close(); process.exitCode = 1; });
