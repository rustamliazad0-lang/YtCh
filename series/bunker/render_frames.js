// Рендер кадров SVG в видео. Режимы:
//   node render_frames.js out.mp4 24   — читает из stdin строки JSON {i, svg}, пишет mp4 (кадры по порядку)
//   node render_frames.js --png a.svg b.svg — сохраняет png рядом
const { chromium } = require('playwright'); const { spawn } = require('child_process'); const fs = require('fs'); const readline = require('readline');
// ждём, пока браузер полностью дорисует кадр (иначе в снимок попадают куски прошлого кадра — мерцание)
const settle = p => p.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0)))));
const HTML = s => `<html><body style="margin:0;overflow:hidden;background:#000">${s}</body></html>`;
(async () => {
  const b = await chromium.launch();
  if (process.argv[2] === '--png') {
    const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    for (const f of process.argv.slice(3)) { await p.setContent(HTML(fs.readFileSync(f, 'utf8'))); await settle(p); await p.screenshot({ path: f.replace(/\.svg$/, '.png') }); }
    await b.close(); return;
  }
  const [out, fps, scale] = process.argv.slice(2), N = 4, SC = +(scale || 1);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', fps, '-c:v', 'png', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const pages = await Promise.all([...Array(N)].map(() => b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: SC })));
  const free = [...pages], waiters = [], done = new Map(); let next = 0;
  const getPage = () => free.length ? Promise.resolve(free.pop()) : new Promise(r => waiters.push(r));
  const release = p => waiters.length ? waiters.shift()(p) : free.push(p);
  const flush = async () => { while (done.has(next)) { const buf = done.get(next); done.delete(next); next++; if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); } };
  let chain = Promise.resolve(); const jobs = [];
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of rl) {
    if (!line.trim()) continue;
    const { i, svg } = JSON.parse(line); const p = await getPage();
    jobs.push((async () => { await p.setContent(HTML(svg)); await settle(p); const buf = await p.screenshot({ type: 'png' }); release(p); done.set(i, buf); chain = chain.then(flush); })());
    if (done.size > 40) await chain;
  }
  await Promise.all(jobs); await chain; await flush(); ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
})();
