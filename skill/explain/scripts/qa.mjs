#!/usr/bin/env node
// Per-frame QA for a step-through explainer card.
// Usage: node qa.mjs <packed.html> [light|dark] [width] [--max-bytes=N] [--legacy]
// Requires Node 22+ (global WebSocket) and a local Chrome/Chromium/Edge. Set CHROME_PATH if needed.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const file = process.argv[2];
if (!file) { console.error('usage: node qa.mjs <packed.html> [light|dark] [width]'); process.exit(2); }
const theme = process.argv[3] === 'dark' ? 'dark' : 'light';
const width = Number(process.argv[4]) || 900;
const legacy = process.argv.includes('--legacy');
const maxArg = process.argv.find(a => a.startsWith('--max-bytes='));
const MAX_BYTES = maxArg ? (Number(maxArg.split('=')[1]) || 200000) : 200000;

const candidates = [process.env.CHROME_PATH, process.env.CHROME,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'];
const chrome = candidates.find(p => p && fs.existsSync(p));
if (!chrome) { console.error('no Chrome/Chromium found; set CHROME_PATH'); process.exit(2); }

const port = 9200 + Math.floor(Math.random() * 600);
const udd = fs.mkdtempSync(path.join(os.tmpdir(), 'card-qa-'));
const proc = spawn(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
  '--disable-extensions', '--disable-background-networking', '--remote-debugging-port=' + port,
  '--user-data-dir=' + udd, '--window-size=' + width + ',1200', 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
let ws, nextId = 1; const pending = new Map();
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = nextId++; pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
try {
  for (let i = 0; i < 120; i++) {
    try { const r = await fetch('http://127.0.0.1:' + port + '/json/version'); if (r.ok) break; } catch (e) {}
    await sleep(100);
  }
  const target = await (await fetch('http://127.0.0.1:' + port + '/json/new?about:blank', { method: 'PUT' })).json();
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id); pending.delete(m.id);
      if (m.error) p.reject(new Error(JSON.stringify(m.error))); else p.resolve(m.result);
    }
  };
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width, height: 1200, deviceScaleFactor: 1, mobile: false });
  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: theme }] });
  await send('Page.navigate', { url: 'file:///' + file.replace(/\\/g, '/') });
  await sleep(1100);

  const expr = '(' + function (legacy) {
    const eff = (el) => {
      let o = 1, n = el;
      while (n && n.getAttribute) {
        const s = getComputedStyle(n);
        if (s.display === 'none') return 0;
        o *= parseFloat(s.opacity || '1');
        n = n.parentNode;
      }
      return o;
    };
    const out = { figures: [], totalSteps: 0, infinite: [] };
    document.querySelectorAll('figure.stepper').forEach(fig => {
      const id = fig.id || '(no id)';
      const inputs = [...fig.querySelectorAll('input.st')];
      const svg = fig.querySelector('svg.dia');
      if (!svg) { out.figures.push({ id, n: 0, error: 'no svg.dia', steps: [] }); return; }
      const vb = svg.viewBox.baseVal;
      const recs = [];
      const seen = new Set();
      inputs.forEach((inp, idx) => {
        inp.checked = true;
        void fig.offsetWidth;
        const problems = [];
        const wrong = [];
        const shown = (sel) => [...fig.querySelectorAll(sel)].map((el, j) => ({ el, j, on: getComputedStyle(el).display !== 'none' })).filter(x => x.on).map(x => x.j);
        const fr = shown('.fr'), cap = shown('.cap'), ns = shown('.ns');
        if (fr.length !== 1 || fr[0] !== idx) wrong.push('layer ' + JSON.stringify(fr));
        if (cap.length !== 1 || cap[0] !== idx) wrong.push('caption ' + JSON.stringify(cap));
        if (ns.length !== 1 || ns[0] !== idx) wrong.push('nav ' + JSON.stringify(ns));
        if (wrong.length) problems.push({ k: 'state', detail: wrong.join('; ') });
        const capEl = fig.querySelectorAll('.cap')[idx];
        const capText = capEl ? (capEl.innerText || '').trim() : '';
        if (!capText) problems.push({ k: 'empty_caption' });
        if (capEl && capEl.getBoundingClientRect().width > fig.clientWidth - 20) problems.push({ k: 'caption-wide' });
        const capDetailEl = capEl ? capEl.querySelector('span') : null;
        const capDetail = capDetailEl ? (capDetailEl.innerText || '').replace(/\s+/g, ' ').trim() : '';
        const capSents = capDetail.split(/[。！？；]/).map(x => x.trim()).filter(Boolean);
        const capMaxS = capSents.reduce((m, x) => Math.max(m, [...x.replace(/\s+/g, '')].length), 0);
        if (!legacy) {

          if (/^(同样|同理|照旧|以此类推|如上|见前)/.test(capDetail) || /套路|如法炮制/.test(capDetail)) problems.push({ k: 'caption-elliptical' });
          if (capDetailEl) {
            const cs = getComputedStyle(capDetailEl);
            const fs = parseFloat(cs.fontSize) || 0;
            const lh = parseFloat(cs.lineHeight) || fs * 1.5;
            if (fs && fs < 14.5 && !seen.has('small')) { seen.add('small'); problems.push({ k: 'caption-small', px: +fs.toFixed(1) }); }
            if (fs && lh / fs < 1.45 && !seen.has('tight')) { seen.add('tight'); problems.push({ k: 'caption-tight', ratio: +(lh / fs).toFixed(2) }); }
          }
        }
        const layer = svg.querySelector('.fr' + (idx + 1));
        let rail = '';
        if (layer) {
          const railEl = layer.querySelector('text.rail') || [...layer.querySelectorAll('text.mono')].pop();
          rail = railEl ? (railEl.textContent || '').trim() : '';
        }
        if (!rail) problems.push({ k: 'empty_rail' });
        const stripFrame = (el) => {
          if (!el) return '';
          const clone = el.cloneNode(true);
          clone.querySelectorAll('rect.ring, text.rail').forEach((n) => n.remove());
          return clone.innerHTML.replace(/\s+/g, ' ').trim();
        };
        const curSig = stripFrame(layer);
        const prevSig = idx > 0 ? stripFrame(svg.querySelector('.fr' + idx)) : '';
        if (!curSig) problems.push({ k: 'frame-empty' });
        else if (idx > 0 && curSig === prevSig) problems.push({ k: 'frame-static' });
        if (layer) {
          const outside = [];
          [...layer.querySelectorAll('path,rect,circle,ellipse,polygon,use')]
            .filter((el) => !el.closest('defs') && !el.classList.contains('ring'))
            .forEach((el) => {
              let b; try { b = el.getBBox(); } catch (e) { return; }
              if (!b || (b.width <= 0 && b.height <= 0)) return;
              const dx = Math.max(-b.x, (b.x + b.width) - vb.width);
              const dy = Math.max(-b.y, (b.y + b.height) - vb.height);
              if (Math.max(dx, dy) > 2) outside.push(el.tagName.toLowerCase() + '@' + b.x.toFixed(1) + ',' + b.y.toFixed(1) + ' ' + b.width.toFixed(1) + 'x' + b.height.toFixed(1));
            });
          if (outside.length) problems.push({ k: 'shape-outside', n: outside.length, s: outside.slice(0, 3).join(' | ') });
        }
        if (!legacy) {
          const lts = layer ? [...layer.querySelectorAll('text')].filter(t => eff(t) > 0.05 && !t.classList.contains('rail') && (t.textContent || '').trim() !== rail).map(t => (t.textContent || '').trim()).filter(Boolean) : [];
          if (lts.length > 4) problems.push({ k: 'figure-many-labels', n: lts.length, s: lts.join('|') });
          lts.forEach(s => {
            const vlen = [...s].reduce((a, ch) => a + (/[\x00-\x7F]/.test(ch) ? 0.55 : 1), 0);
            if (vlen > 6.5) problems.push({ k: 'figure-long-label', s, w: +vlen.toFixed(1) });
            if (/[。！？]/.test(s)) problems.push({ k: 'figure-sentence', s });
          });
        }
        const texts = [...svg.querySelectorAll('text')].filter(t => eff(t) > 0.05).map(t => {
          const b = t.getBBox();
          return { s: (t.textContent || '').trim(), b, el: t };
        });
        texts.forEach(({ s, b }) => {
          if (b.width <= 0 || b.height <= 0) return;
          if (b.x < -1 || b.y < -1 || b.x + b.width > vb.width + 1 || b.y + b.height > vb.height + 1) {
            problems.push({ k: 'outside', s, b: [b.x, b.y, b.width, b.height].map(v => +v.toFixed(1)) });
          }
        });
        for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
          const a = texts[i].b, c = texts[j].b;
          const ix = Math.min(a.x + a.width, c.x + c.width) - Math.max(a.x, c.x);
          const iy = Math.min(a.y + a.height, c.y + c.height) - Math.max(a.y, c.y);
          const sa = texts[i].el.getAttribute('data-stack'), sb = texts[j].el.getAttribute('data-stack');
          if (sa && sa === sb) continue;
          if (ix > 0.5 && iy > 0.5) problems.push({ k: 'text-overlap', a: texts[i].s, b: texts[j].s, ix: +ix.toFixed(1), iy: +iy.toFixed(1) });
        }
        const rings = [...svg.querySelectorAll('rect')].filter(r => {
          if ((r.getAttribute('class') || '').indexOf('ring') < 0) return false;
          const l = r.closest('.fr');
          return !l || getComputedStyle(l).display !== 'none';
        });
        rings.forEach(r => {
          const rb = r.getBBox();
          texts.forEach(({ s, b }) => {
            const ix = Math.min(b.x + b.width, rb.x + rb.width) - Math.max(b.x, rb.x);
            const iy = Math.min(b.y + b.height, rb.y + rb.height) - Math.max(b.y, rb.y);
            if (ix <= 0 || iy <= 0) return;
            const margin = Math.min(b.x - rb.x, b.y - rb.y, rb.x + rb.width - (b.x + b.width), rb.y + rb.height - (b.y + b.height));
            if (margin < 3) problems.push({ k: 'ring-touch', s, margin: +margin.toFixed(1), bb: [rb.x, rb.y, rb.width, rb.height].map(v => +v.toFixed(1)) });
          });
        });
        const boxes = [...svg.querySelectorAll('rect')].filter(r => {
          const cls = r.getAttribute('class') || '';
          if (cls.indexOf('ring') >= 0 || cls.indexOf('f-bg') >= 0) return false;
          const b = r.getBBox();
          return b.width >= 20 && b.width <= 360 && b.height >= 16 && b.height <= 220;
        });
        texts.forEach(({ s, b }) => {
          boxes.forEach(r => {
            const rb = r.getBBox();
            const ix = Math.min(b.x + b.width, rb.x + rb.width) - Math.max(b.x, rb.x);
            const iy = Math.min(b.y + b.height, rb.y + rb.height) - Math.max(b.y, rb.y);
            if (ix <= 0.5 || iy <= 0.5) return;
            const spill = Math.max(rb.x - b.x, b.x + b.width - (rb.x + rb.width), rb.y - b.y, b.y + b.height - (rb.y + rb.height));
            if (spill > 2) problems.push({ k: 'spill', s, spill: +spill.toFixed(1) });
          });
        });
        recs.push({ k: idx + 1, cap: capText.replace(/\s+/g, ' ').slice(0, 120), rail, chars: capDetail.length, sentences: capSents.length, maxSentence: capMaxS, problems });
      });
      const hs = recs.map(r => Math.round(fig.getBoundingClientRect().height));
      const heightVar = hs.length ? Math.max(...hs) - Math.min(...hs) : 0;
      out.figures.push({ id, n: inputs.length, heightVar, steps: recs });
      out.totalSteps += inputs.length;
    });
    document.querySelectorAll('*').forEach(el => {
      const s = getComputedStyle(el);
      if (s.animationName && s.animationName !== 'none' && s.animationIterationCount.split(',').some(v => v.trim() === 'infinite')) {
        out.infinite.push(el.tagName.toLowerCase() + '.' + (el.getAttribute('class') || ''));
      }
    });
    return out;
  } + ')(' + legacy + ')';
  const res = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
  const data = res.result.value;
  data.file = file;
  data.theme = theme;
  data.width = width;
  data.sizeBytes = fs.statSync(file).size;
  const steps = data.figures.flatMap(f => f.steps || []);
  data.stats = {
    frames: steps.length,
    sentences: steps.reduce((a, s) => a + (s.sentences || 0), 0),
    maxSentence: Math.max(0, ...steps.map(s => s.maxSentence || 0)),
    over30: steps.filter(s => (s.maxSentence || 0) > 30).length,
    framesOver2Sent: steps.filter(s => (s.sentences || 0) > 2).length,
    framesOver120Chars: steps.filter(s => (s.chars || 0) > 120).length,
  };
  let bad = 0;
  data.figures.forEach(f => (f.steps || []).forEach(s => { bad += (s.problems || []).length; }));
  data.problemCount = bad;
  data.sizeOk = data.sizeBytes < MAX_BYTES;
  data.ok = bad === 0 && data.infinite.length === 0 && data.sizeOk;
  console.log(JSON.stringify(data, null, 1));
  process.exitCode = data.ok ? 0 : 1;
} catch (e) {
  console.error('QA_ERROR', e.message);
  process.exitCode = 2;
} finally {
  try { ws && ws.close(); } catch (e) {}
  proc.kill();
  await sleep(150);
  try { fs.rmSync(udd, { recursive: true, force: true }); } catch (e) {}
}
