// Снимает каждую HTML-сцену в PNG 2160x3840 (вектор, чёткость x2). Запуск: node shot_frames.js <папка с html>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const dir = process.argv[2];
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 2 });
  for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.html')).sort()) {
    await pg.goto('file://' + path.join(dir, f));
    await pg.screenshot({ path: path.join(dir, f.replace('.html', '.png')) });
  }
  await b.close();
})();
