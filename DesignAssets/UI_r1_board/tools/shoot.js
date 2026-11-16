// 用 Playwright + 本机 Chrome 截图（SwiftShader 软件 WebGL）
const path = require('path');
const { chromium } = require('playwright-core');

const OUT = path.resolve(__dirname, '..', 'out');
const URL = process.env.PAGE_URL || 'http://127.0.0.1:8791/page.html';

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    args: [
      '--use-gl=angle', '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader', '--disable-gpu-sandbox',
      '--force-color-profile=srgb', '--hide-scrollbars',
    ],
  });
  const page = await browser.newPage({
    viewport: { width: 1080, height: 1920 },
    deviceScaleFactor: 2,
  });
  page.on('console', m => console.log('[page]', m.type(), m.text()));
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForFunction('window.__ready === true', { timeout: 180000 });
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(OUT, 'game_2x.png') });
  console.log('shot ->', path.join(OUT, 'game_2x.png'));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
