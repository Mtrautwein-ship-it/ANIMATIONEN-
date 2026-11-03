// Rendert das Video Bild für Bild nach MP4 (1920x1080, 30 fps).
// Aufruf: node render.js [eingabe.html] [ausgabe.mp4] [fps]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const input = path.resolve(process.argv[2] || 'step1-fluessigkeitskategorien.html');
  const output = path.resolve(process.argv[3] || 'step1-fluessigkeitskategorien.mp4');
  const fps = +(process.argv[4] || 30);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + input + '?render');
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.DURATION);
  const lines = await page.evaluate(() => window.LINES.map(l => ({ text: l.text, start: l.start, end: l.end })));
  require('fs').writeFileSync(path.join(path.dirname(input), path.basename(input).split('-')[0] + '-zeiten.json'), JSON.stringify({ duration, lines }, null, 1));
  const frames = Math.round(duration * fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < frames; f++) {
    await page.evaluate(t => window.render(t), f / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (fps * 10) === 0) console.log(`${(f / fps).toFixed(0)} / ${duration} s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('fertig:', output);
})();
