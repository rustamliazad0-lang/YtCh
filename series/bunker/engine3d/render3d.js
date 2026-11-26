// node render3d.js spec.json out.mp4 [audio.mp3]: поднимает локальный сервер, снимает кадры, кодирует (зерно, x264, bt709)
const { chromium } = require('playwright'); const { spawn } = require('child_process'); const path = require('path');
(async () => {
  const [specPath, out, audio] = process.argv.slice(2);
  const spec = require(path.resolve(specPath)), fps = 30, n = Math.round(spec.duration * fps);
  const srv = spawn('python3', ['-m', 'http.server', '8765', '--bind', '127.0.0.1'], { cwd: __dirname, stdio: 'ignore' });
  await new Promise(r => setTimeout(r, 800));
  const args = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-'];
  if (audio) args.push('-i', audio);
  args.push('-vf', 'noise=alls=3:allf=t,scale=out_color_matrix=bt709:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
    '-x264-params', 'aq-mode=3:aq-strength=1.1', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709');
  if (audio) args.push('-af', 'loudnorm=I=-14:TP=-1.5:LRA=11,apad', '-c:a', 'aac', '-b:a', '192k', '-shortest');
  args.push('-movflags', '+faststart', out);
  const ff = spawn('ffmpeg', args, { stdio: ['pipe', 'inherit', 'inherit'] });
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('console', m => { if (m.type() === 'error') console.error('PAGE:', m.text()); });
  pg.on('pageerror', e => console.error('PAGEERR:', e.message));
  await pg.goto(`http://127.0.0.1:8765/proto.html?spec=${encodeURIComponent(path.relative(__dirname, path.resolve(specPath)))}`);
  await pg.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await pg.evaluate(t => window.R(t), i / fps);
    const buf = await pg.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i === 9) console.log('≈', ((Date.now() - t0) / 10).toFixed(0), 'мс на кадр');
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close(); srv.kill();
})();
