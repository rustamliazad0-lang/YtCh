// Покадровый рендер 3D-сцены: node motion_render.js page.html out.mp4 seconds
// Кадры JPEG q95 идут потоком в ffmpeg (x264, зерно против блоков, bt709).
const { chromium } = require('playwright');
const { spawn } = require('child_process');
(async () => {
  const [html, out, secs] = process.argv.slice(2);
  const fps = 30, n = Math.round(parseFloat(secs) * fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-vf', 'noise=alls=3:allf=t,scale=out_color_matrix=bt709:flags=lanczos,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-profile:v', 'high', '-level', '4.2', '-g', '60', '-bf', '2',
    '-x264-params', 'aq-mode=3:aq-strength=1.1:deblock=-1,-1', '-maxrate', '18M', '-bufsize', '36M',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await pg.goto('file://' + html);
  await pg.evaluate(() => document.fonts.ready);
  for (let i = 0; i < n; i++) {
    await pg.evaluate(t => window.R(t), i / fps);
    const buf = await pg.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await b.close();
})();
