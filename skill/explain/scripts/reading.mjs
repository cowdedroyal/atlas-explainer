#!/usr/bin/env node
// Dump a step-through card as a per-frame text script, for a beginner review.
// Usage: node reading.mjs <packed.html> > reading.md
// Requires Node 22+ (global WebSocket) and a local Chrome/Chromium/Edge.
import { spawn } from 'node:child_process';
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path';

const file = process.argv[2];
const statsOnly = process.argv.includes('--stats');
if (!file) { console.error('usage: node reading.mjs <packed.html> [--stats] > reading.md'); process.exit(2); }
const candidates = [process.env.CHROME_PATH, process.env.CHROME,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'];
const chrome = candidates.find(p => p && fs.existsSync(p));
if (!chrome) { console.error('no Chrome/Chromium found; set CHROME_PATH'); process.exit(2); }
const port = 9800 + Math.floor(Math.random() * 150);
const udd = fs.mkdtempSync(path.join(os.tmpdir(), 'card-read-'));
const proc = spawn(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
  '--disable-extensions', '--remote-debugging-port=' + port, '--user-data-dir=' + udd,
  '--window-size=900,1200', 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
let ws, nextId = 1; const pending = new Map();
function send(method, params = {}) { return new Promise((resolve, reject) => { const id = nextId++; pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params })); }); }
try {
  for (let i = 0; i < 120; i++) { try { const r = await fetch('http://127.0.0.1:' + port + '/json/version'); if (r.ok) break; } catch (e) {} await sleep(100); }
  const target = await (await fetch('http://127.0.0.1:' + port + '/json/new?about:blank', { method: 'PUT' })).json();
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); if (m.error) p.reject(new Error(JSON.stringify(m.error))); else p.resolve(m.result); } };
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 900, height: 1200, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: 'file:///' + file.replace(/\\/g, '/') });
  await sleep(1000);
  const expr = '(' + function () {
    const clean = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    const clen = (s) => [...String(s || '').replace(/\s+/g, '')].length;
    const out = { title: document.title, lead: '', symbols: '', figures: [] };
    const lead = document.querySelector('.ex-lead'); if (lead) out.lead = clean(lead.innerText);
    const sym = document.querySelector('.symbols'); if (sym) out.symbols = clean(sym.innerText);
    document.querySelectorAll('figure.stepper').forEach(fig => {
      const svg = fig.querySelector('svg.dia');
      const inputs = [...fig.querySelectorAll('input.st')];
      const steps = [];
      inputs.forEach((inp, idx) => {
        inp.checked = true; void fig.offsetWidth;
        const cap = fig.querySelectorAll('.cap')[idx];
        const bt = cap ? clean(cap.querySelector('b') ? cap.querySelector('b').innerText : '') : '';
        let dt = '';
        if (cap) {
          const sp = cap.querySelector('span');
          if (sp) dt = clean(sp.innerText);
          else dt = clean(cap.innerText.replace(bt, ''));
        }
        const layer = svg ? svg.querySelector('.fr' + (idx + 1)) : null;
        let rail = '';
        if (layer) {
          const r = layer.querySelector('text.rail') || [...layer.querySelectorAll('text.mono')].pop();
          rail = r ? clean(r.textContent) : '';
        }
        const labels = [];
        if (svg) {
          [...svg.querySelectorAll('text')].forEach(t => {
            let o = 1, n = t;
            while (n && n.getAttribute) { const s = getComputedStyle(n); if (s.display === 'none') return; o *= parseFloat(s.opacity || '1'); n = n.parentNode; }
            if (o < 0.5) return;
            const s = clean(t.textContent);
            if (s && s !== rail && !labels.includes(s)) labels.push(s);
          });
        }
        const sents = dt.split(/[。！？；]/).map(x => x.trim()).filter(Boolean);
        steps.push({ k: idx + 1, title: bt, detail: dt, rail, labels: labels.slice(0, 14),
          chars: clen(dt), sentences: sents.length,
          maxSentence: sents.reduce((m, x) => Math.max(m, clen(x)), 0) });
      });
      out.figures.push({ id: fig.id, aria: svg ? (svg.getAttribute('aria-label') || '') : '', steps });
    });
    return out;
  } + ')()';
  const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
  const d = res.result.value;
  const all = d.figures.flatMap(f => f.steps);
  const totalChars = all.reduce((a, s) => a + s.chars, 0);
  const stats = {
    frames: all.length,
    sentences: all.reduce((a, s) => a + s.sentences, 0),
    maxSentence: Math.max(0, ...all.map(s => s.maxSentence)),
    over24: all.filter(s => s.maxSentence > 24).length,
    over30: all.filter(s => s.maxSentence > 30).length,
    framesOver2Sent: all.filter(s => s.sentences > 2).length,
    avgFrameChars: +(totalChars / (all.length || 1)).toFixed(1),
    maxFrameChars: Math.max(0, ...all.map(s => s.chars)),
    framesOver60Chars: all.filter(s => s.chars > 60).length,
  };
  stats.avgSentence = +(totalChars / (stats.sentences || 1)).toFixed(1);
  console.error('READING_STATS ' + JSON.stringify(stats));
  const lines = ['# 逐帧文字稿', ''];
  if (d.title) lines.push('标题：' + d.title);
  if (d.lead) lines.push('开头：' + d.lead);
  if (d.symbols) lines.push('符号表：' + d.symbols);
  lines.push('');
  d.figures.forEach((f, i) => {
    lines.push('## 图 ' + (i + 1) + '（' + f.steps.length + ' 步）—— ' + (f.aria || f.id));
    f.steps.forEach(s => {
      lines.push('### 第 ' + s.k + ' 步：' + s.title);
      lines.push('- 说明：' + s.detail);
      lines.push('- 图下事实行：' + s.rail);
      if (s.labels.length) lines.push('- 图中标签：' + s.labels.join(' · '));
      lines.push('');
    });
  });
  if (statsOnly) console.log(JSON.stringify(stats));
  else console.log(lines.join('\n'));
} catch (e) { console.error('READING_ERROR', e.message); process.exitCode = 2; }
finally { try { ws && ws.close(); } catch (e) {} proc.kill(); await sleep(150); try { fs.rmSync(udd, { recursive: true, force: true }); } catch (e) {} }

