// 地図ページを headless Chrome で撮る（CDP、node 25 の組み込み WebSocket / fetch）。
// ページ側に window.__ready と window.__frame(t)（時刻 t の絵を出して描画完了で resolve）がある前提。
//
//   node capture.mjs png    <url> <out.png>  [W H] [t]          1 枚
//   node capture.mjs frames <url> <outDir>   [W H] [fps] [loop]  ループを fps でコマ送り（frame_0000.png …）
//   node capture.mjs eval   <url> <js>       [W H]               ページで式を評価して表示（検証用）
//
// 撮るサーバは別に立てておく（例：preview の mapchallenge、http://127.0.0.1:8793/）。
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [mode, url, arg, W = '1600', H = '900', a5, a6] = process.argv.slice(2);
if (!mode || !url || !arg) { console.error('usage: see header'); process.exit(2); }
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9300 + Math.floor(Math.random() * 500);
const prof = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'cap-chrome-'));
// swiftshader で WebGL を CPU 描画する。GPU の無い headless でも地図が黒くならない
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`,
  `--window-size=${W},${H}`, '--hide-scrollbars', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  '--no-first-run', '--no-default-browser-check', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const done = code => { try { chrome.kill(); } catch {} setTimeout(() => { rmSync(prof, { recursive: true, force: true }); process.exit(code); }, 300); };

let targets;
for (let i = 0; i < 60 && !targets; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); } catch { await sleep(200); } }
const ws = new WebSocket(targets.find(t => t.type === 'page').webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const pending = new Map(); const logs = [];
ws.onmessage = ev => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.consoleAPICalled' && ['error', 'warning', 'warn'].includes(m.params.type))
    logs.push(`${m.params.type}: ${m.params.args.map(a => a.value ?? a.description).join(' ')}`);
  if (m.method === 'Runtime.exceptionThrown') logs.push('exception: ' + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
};
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description || 'eval failed');
  return r.result?.result?.value;
};
const shoot = async file => writeFileSync(file, Buffer.from((await send('Page.captureScreenshot', { format: 'png' })).result.data, 'base64'));

await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', { width: +W, height: +H, deviceScaleFactor: 1, mobile: +W < 600 });
// REDUCED_MOTION=1 で prefers-reduced-motion: reduce を再現する（止まって始まるかの確認用）
if (process.env.REDUCED_MOTION) await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
await send('Page.navigate', { url });
let ready = false;
for (let i = 0; i < 180 && !ready; i++) {
  await sleep(500);
  // map.loaded() は再生中（毎コマ塗りを変える）だと false が続くので見ない
  ready = await ev(`!!(window.__ready && typeof map !== 'undefined' && map.areTilesLoaded())`).catch(() => false);
}
if (!ready) { console.error('page not ready'); done(1); await new Promise(() => {}); }
await sleep(1500); // 文字のフォントとラベルの配置が落ち着くのを待つ

try {
  if (mode === 'png') {
    await ev(`__frame(${+(a5 ?? 0)})`);
    await shoot(arg);
    console.log('wrote', arg);
  } else if (mode === 'frames') {
    const fps = +(a5 ?? 30), loop = +(a6 ?? (await ev('LOOP')));
    const n = Math.round(fps * loop);
    mkdirSync(arg, { recursive: true });
    for (let k = +(process.env.START ?? 0); k < n; k++) {  // START=k で途中から撮り直せる
      await ev(`__frame(${k / fps})`);  // k = n は k = 0 と同じ絵になるので撮らない
      await shoot(join(arg, `frame_${String(k).padStart(4, '0')}.png`));
      if (k % 30 === 0) console.log(`frame ${k}/${n}`);
    }
    console.log(`wrote ${n} frames (${fps} fps, ${loop} s) to ${arg}`);
  } else if (mode === 'eval') {
    console.log(JSON.stringify(await ev(arg), null, 1));
  }
} catch (e) { console.error(e.message); logs.push('capture: ' + e.message); }
console.log(logs.length ? 'console:\n' + logs.join('\n') : 'console: no errors or warnings');
done(logs.length ? 1 : 0);
