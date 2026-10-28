/* Run after: atlas-explainer pack examples -o <packed-dir>
 * Requires Playwright. Set PLAYWRIGHT_MODULE and CHROMIUM_EXECUTABLE_PATH for an existing local installation.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

async function main() {
  const dir = process.argv[2];
  if (!dir) throw new Error('Usage: node scripts/check_media_browser.cjs <packed-dir>');
  const browser = await chromium.launch({headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE_PATH ? {executablePath: process.env.CHROMIUM_EXECUTABLE_PATH} : {})});
  try {
    const page = await browser.newPage({reducedMotion: 'reduce'});
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const load = async (html, animated = true) => {
      await page.setContent('<iframe sandbox="allow-scripts" style="width:950px;height:1200px"></iframe>');
      await page.locator('iframe').evaluate((node, html) => {node.srcdoc = html;}, html);
      const frame = page.frames()[1];
      await frame.waitForSelector(animated ? '.ex-scrub' : '.ex-chart-canvas svg');
      await frame.waitForFunction(() => Array.from(document.querySelectorAll('ex-anim img')).every(i => i.complete));
      return frame;
    };
    const html = fs.readFileSync(path.join(dir, 'media-showcase/index.html'), 'utf8');
    let frame = await load(html);
    const scrub = frame.locator('.ex-scrub');
    assert.equal(await scrub.inputValue(), '0', 'reduced motion disables autoplay');
    await scrub.fill('5');
    assert.equal(await scrub.inputValue(), '5');
    assert.equal(await frame.locator('.ex-count').textContent(), '6 / 12');
    await scrub.press('ArrowRight');
    assert.equal(await scrub.inputValue(), '6', 'keyboard stepping survives redraw');
    await frame.locator('.ex-play').click();
    await frame.waitForFunction(() => Number(document.querySelector('.ex-scrub').value) !== 6);
    await frame.locator('.ex-play').click();
    await frame.waitForFunction(() => document.querySelector('ex-chart[interactive]').__chart.view !== null);
    const chart = frame.locator('ex-chart[interactive]');
    await chart.locator('.role-mark path').first().hover();
    await chart.locator('.ex-tip:not([hidden])').waitFor();
    await chart.locator('.role-legend-label text').first().click();
    await frame.waitForFunction(() => document.querySelector('ex-chart[interactive]').__chart.view.data('pick_store').length > 0);
    const selected = await chart.locator('.role-mark path').evaluateAll(nodes => nodes.map(n => n.getAttribute('opacity')));
    assert(selected.includes('0.35') && selected.includes('1'), 'legend selection changes mark opacity');
    const lightSrc = await frame.locator('ex-chart:not([interactive]) .ex-chart-light img').getAttribute('src');
    await page.locator('iframe').evaluate(node => node.contentWindow.postMessage({type:'atlas:theme',theme:'dark'}, '*'));
    await frame.waitForFunction(() => document.documentElement.dataset.theme === 'dark');
    await frame.locator('ex-chart:not([interactive]) .ex-chart-dark img').waitFor({state:'visible'});
    assert.notEqual(await frame.locator('ex-chart:not([interactive]) .ex-chart-dark img').getAttribute('src'), lightSrc);
    await frame.waitForFunction(() => document.querySelector('ex-chart[interactive]').__chart.view !== null);
    assert.equal(await frame.locator('ex-chart[interactive] .ex-chart-canvas svg').count(), 1);

    // Defense in depth: even if a packed registry is tampered with after validation, static SVG is inert.
    const match = /(<script type="application\/json" id="atlas-media-registry">)([\s\S]*?)(<\/script>)/.exec(html);
    const registry = JSON.parse(match[2]);
    registry.survivors.svg.light = '<svg xmlns="http://www.w3.org/2000/svg" onload="window.__injected=1"><image href="data:image/png,broken" onerror="window.__injected=1"/></svg>';
    frame = await load(html.replace(match[0], match[1] + JSON.stringify(registry).replace(/<\//g, '<\\/') + match[3]));
    await frame.locator('ex-chart:not([interactive]) .ex-chart-light img').evaluate(img => img.decode());
    assert.equal(await frame.evaluate(() => window.__injected), undefined);
    assert.equal(await frame.locator('ex-chart:not([interactive]) svg').count(), 0);

    frame = await load(fs.readFileSync(path.join(dir, 'renderer-imports/index.html'), 'utf8'));
    for (const name of ['motion', 'manim']) {
      const animation = frame.locator(`ex-anim[src="atlas-media:${name}"]`);
      await animation.locator('.ex-scrub').fill('4');
      assert.equal(await animation.locator('.ex-scrub').inputValue(), '4');
      const first = await animation.locator('canvas').evaluate(canvas => canvas.toDataURL());
      await animation.locator('.ex-scrub').fill('8');
      assert.notEqual(await animation.locator('canvas').evaluate(canvas => canvas.toDataURL()), first,
        `${name} renderer frames change the displayed canvas`);
    }
    frame = await load(fs.readFileSync(path.join(dir, 'data-interactions/index.html'), 'utf8'), false);
    await frame.waitForFunction(() => document.querySelector('ex-chart').__chart.view !== null);
    assert.equal(await frame.locator('.role-mark path').count(), 5);
    await frame.locator('input[type="range"]').fill('6');
    await frame.waitForFunction(() => document.querySelector('ex-chart').__chart.view.signal('cutoff') === 6);
    assert.equal(await frame.locator('.role-mark path').count(), 3, 'bound parameter filters the data');
    const domain = await frame.evaluate(() => document.querySelector('ex-chart').__chart.view.scale('x').domain());
    await frame.locator('.ex-chart-canvas svg').hover();
    await page.mouse.wheel(0, -180);
    await frame.waitForFunction(before => {
      const after = document.querySelector('ex-chart').__chart.view.scale('x').domain();
      return after[1] - after[0] < before[1] - before[0];
    }, domain);
    assert.deepEqual(errors, [], 'no uncaught browser errors');
    console.log('PASS: sandbox playback, reduced motion, scrub/keyboard, tooltip, legend selection, themes, inert SVG, real renderer frames, parameter filtering, wheel zoom');
  } finally {await browser.close();}
}
main().catch(error => {console.error(error); process.exitCode = 1;});
