// 用 Playwright + 本机 Chrome 截图（无需 WebGL）
const path = require('path');
const { chromium } = require('playwright-core');
const OUT = path.resolve(__dirname, '..', 'out');
const NAME = process.env.SHOT_NAME || 'map';
const URL = process.env.PAGE_URL || 'http://127.0.0.1:8793/render/map.html';

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    args: ['--force-color-profile=srgb', '--hide-scrollbars'],
  });
  const page = await browser.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2 });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForFunction('window.__ready === true', { timeout: 60000 });
  await page.waitForTimeout(300);
  const p = path.join(OUT, NAME + '_2x.png');
  await page.screenshot({ path: p });
  console.log('shot ->', p);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
