const { chromium } = require('playwright-core');
const MODE = process.env.PIX_MODE || 'text';
const BASE = 'E:/UnityProject/MutiplayGame/outputs/ui_replica_v7/';
const CFG = {
  text : ['render_px/',    'pixel.html#'],
  raw  : ['render_raw/',   'pixel.html?text=0#'],
  final: ['render_final/', 'ui_final.html#'],
};
const OUT = BASE + CFG[MODE][0];
const URL = 'file:///' + BASE + CFG[MODE][1];
const S = [['s1',325,478],['s2',325,478],['s3',325,478],['s4',325,478],
           ['s5',325,478],['s6',325,478],['s7',325,478],['s8',325,478],['s9',470,836]];
(async () => {
  require('fs').mkdirSync(OUT,{recursive:true});
  const browser = await chromium.launch({
    executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless:true, args:['--no-sandbox','--disable-gpu','--allow-file-access-from-files']
  });
  for (const [id,w,h] of S) {
    const page = await browser.newPage({viewport:{width:w,height:h},deviceScaleFactor:2});
    const errs=[]; page.on('pageerror',e=>errs.push(e.message));
    await page.goto(URL+id,{waitUntil:'load'});
    await page.waitForTimeout(220);
    const cnt = await page.locator('#'+id+' .t').count();
    await page.screenshot({path:OUT+id+'.png'});
    console.log(id, w+'x'+h, 'texts='+cnt, errs.length?errs.join('|'):'OK');
    await page.close();
  }
  await browser.close();
})().catch(e=>{console.error('FATAL',e);process.exit(1)});
