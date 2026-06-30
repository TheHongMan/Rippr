import os
import sys
import threading
import uuid
import json
import time
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, Response
import yt_dlp
import webview

app = Flask(__name__)
downloads = {}
DOWNLOAD_DIR = str(Path.home() / "Downloads")

HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rippr</title>
<script>
  (function () {
    var saved = null;
    try { saved = localStorage.getItem('rippr-theme'); } catch (e) {}
    document.documentElement.setAttribute('data-theme', saved || '{{ initial_theme }}');
  })();
</script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root, [data-theme="light"] {
    --bg: #f3f4f7;
    --surface: #ffffff;
    --surface-2: #eef0f4;
    --border: rgba(17, 20, 28, 0.08);
    --border-strong: rgba(17, 20, 28, 0.14);
    --text: #16181d;
    --text-secondary: #51555f;
    --text-muted: #898d97;
    --accent: #2f6bff;
    --accent-hover: #1f57e6;
    --accent-contrast: #ffffff;
    --accent-text: #1f57e6;
    --accent-soft: rgba(47, 107, 255, 0.14);
    --logo-bg: #0d0d10;
    --success-bg: #e4f7ec; --success-text: #157a45; --success-dot: #1ea35d;
    --danger-bg: #fdeaea;  --danger-text: #c23232;  --danger-dot: #df4444;
    --warn-bg: #fef3e2;    --warn-text: #b06a12;
    --shadow: 0 1px 2px rgba(16,24,40,.04), 0 10px 30px rgba(16,24,40,.06);
    --radius-card: 16px; --radius: 11px; --radius-pill: 999px;
  }

  [data-theme="dark"] {
    --bg: #0b0c0f;
    --surface: #15171d;
    --surface-2: #1d2027;
    --border: rgba(255, 255, 255, 0.08);
    --border-strong: rgba(255, 255, 255, 0.15);
    --text: #f1f2f5;
    --text-secondary: #a6a9b2;
    --text-muted: #6c6f79;
    --accent: #5b8bff;
    --accent-hover: #719bff;
    --accent-contrast: #0b0c0f;
    --accent-text: #8fb0ff;
    --accent-soft: rgba(91, 139, 255, 0.18);
    --logo-bg: #23262e;
    --success-bg: #15321f; --success-text: #6fe0a0; --success-dot: #34d27f;
    --danger-bg: #381818;  --danger-text: #ff9d9d;  --danger-dot: #ff6b6b;
    --warn-bg: #34260f;    --warn-text: #f3c073;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 12px 32px rgba(0,0,0,.35);
    --radius-card: 16px; --radius: 11px; --radius-pill: 999px;
  }

  html, body { height: 100%; }
  body {
    font-family: "Segoe UI Variable", "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    background: var(--bg); color: var(--text);
    -webkit-font-smoothing: antialiased;
    -webkit-user-select: none; user-select: none;
    padding: 22px 22px 30px;
    display: flex; justify-content: center;
    transition: background-color .3s ease, color .3s ease;
  }
  .app { width: 100%; max-width: 660px; display: flex; flex-direction: column; gap: 16px; }

  /* Header */
  .app-header { display: flex; align-items: center; justify-content: space-between; }
  .brand { display: flex; align-items: center; gap: 11px; }
  .brand-mark { width: 38px; height: 38px; flex-shrink: 0; display: block; }
  .brand-mark .logo-bg { fill: var(--logo-bg); transition: fill .3s ease; }
  .brand-name { font-size: 19px; font-weight: 600; letter-spacing: -0.3px; line-height: 1.1; }
  .brand-tag { font-size: 12.5px; color: var(--text-muted); }
  .brand-text { display: flex; flex-direction: column; }

  .theme-toggle {
    width: 38px; height: 38px; border-radius: var(--radius);
    background: var(--surface); border: 1px solid var(--border);
    color: var(--text-secondary); cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background .15s, border-color .15s, color .15s, transform .1s;
  }
  .theme-toggle:hover { color: var(--text); border-color: var(--border-strong); }
  .theme-toggle:active { transform: scale(0.94); }
  .theme-toggle svg { width: 19px; height: 19px; }
  .theme-toggle .icon-moon { display: none; }
  [data-theme="dark"] .theme-toggle .icon-moon { display: block; }
  [data-theme="dark"] .theme-toggle .icon-sun { display: none; }

  /* Cards */
  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-card); box-shadow: var(--shadow);
    transition: background-color .3s ease, border-color .3s ease;
  }
  .composer { padding: 18px; }

  /* URL row */
  .url-row { display: flex; gap: 9px; }
  .input-wrap { flex: 1; min-width: 0; position: relative; display: flex; align-items: center; }
  .input-wrap .lead-icon {
    position: absolute; left: 13px; width: 17px; height: 17px;
    color: var(--text-muted); pointer-events: none;
  }
  #url {
    width: 100%; height: 46px; padding: 0 14px 0 39px;
    background: var(--surface-2); border: 1px solid transparent;
    border-radius: var(--radius); color: var(--text); font-size: 14.5px;
    outline: none; -webkit-user-select: text; user-select: text;
    transition: border-color .15s, box-shadow .15s, background .15s;
  }
  #url::placeholder { color: var(--text-muted); }
  #url:focus { border-color: var(--accent); background: var(--surface); box-shadow: 0 0 0 3px var(--accent-soft); }

  .btn-primary {
    height: 46px; padding: 0 18px; flex-shrink: 0;
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--accent); color: var(--accent-contrast);
    border: none; border-radius: var(--radius);
    font-size: 14.5px; font-weight: 600; cursor: pointer; white-space: nowrap;
    transition: background .15s, transform .08s, opacity .15s;
  }
  .btn-primary svg { width: 18px; height: 18px; }
  .btn-primary:hover { background: var(--accent-hover); }
  .btn-primary:active { transform: scale(0.97); }
  .btn-primary:disabled { opacity: 0.55; cursor: progress; }

  .hint { font-size: 12.5px; color: var(--danger-text); min-height: 17px; margin-top: 9px; padding-left: 2px; }

  /* Controls */
  .controls { display: flex; gap: 10px; flex-wrap: wrap; }
  .control { display: flex; flex-direction: column; gap: 6px; }
  .control.grow { flex: 1; min-width: 130px; }
  .control label { font-size: 11.5px; font-weight: 500; color: var(--text-muted); letter-spacing: 0.02em; padding-left: 2px; }
  .select-wrap { position: relative; }
  .select-wrap .chev { position: absolute; right: 11px; top: 50%; transform: translateY(-50%); width: 15px; height: 15px; color: var(--text-muted); pointer-events: none; }
  select {
    width: 100%; height: 40px; padding: 0 32px 0 12px;
    -webkit-appearance: none; appearance: none;
    background: var(--surface-2); border: 1px solid transparent;
    border-radius: var(--radius); color: var(--text); font-size: 13.5px;
    cursor: pointer; outline: none;
    transition: border-color .15s, box-shadow .15s, background .15s;
  }
  select:hover { border-color: var(--border-strong); }
  select:focus { border-color: var(--accent); background: var(--surface); box-shadow: 0 0 0 3px var(--accent-soft); }

  /* Toggle switch */
  .switch { position: relative; display: inline-flex; align-items: center; height: 40px; cursor: pointer; }
  .switch input { position: absolute; opacity: 0; width: 0; height: 0; }
  .switch .track {
    width: 42px; height: 24px; border-radius: var(--radius-pill);
    background: var(--surface-2); border: 1px solid var(--border-strong);
    position: relative; transition: background .18s, border-color .18s;
  }
  .switch .track::after {
    content: ""; position: absolute; top: 2px; left: 2px;
    width: 18px; height: 18px; border-radius: 50%; background: #fff;
    box-shadow: 0 1px 2px rgba(0,0,0,.25); transition: transform .18s;
  }
  .switch input:checked + .track { background: var(--accent); border-color: var(--accent); }
  .switch input:checked + .track::after { transform: translateX(18px); }
  .switch input:focus-visible + .track { box-shadow: 0 0 0 3px var(--accent-soft); }

  /* Save-to row */
  .dir-row {
    display: flex; align-items: center; gap: 9px;
    margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border);
  }
  .dir-label { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; color: var(--text-secondary); white-space: nowrap; }
  .dir-label svg { width: 16px; height: 16px; color: var(--text-muted); }
  #outdir {
    flex: 1; min-width: 0; height: 36px; padding: 0 11px;
    background: var(--surface-2); border: 1px solid transparent;
    border-radius: var(--radius); color: var(--text-secondary); font-size: 12px;
    outline: none; -webkit-user-select: text; user-select: text;
    transition: border-color .15s, box-shadow .15s;
  }
  #outdir:focus { border-color: var(--accent); color: var(--text); box-shadow: 0 0 0 3px var(--accent-soft); }
  .btn-icon {
    width: 36px; height: 36px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    background: var(--surface-2); border: 1px solid var(--border);
    border-radius: var(--radius); color: var(--text-secondary); cursor: pointer;
    transition: background .15s, color .15s, border-color .15s, transform .08s;
  }
  .btn-icon:hover { color: var(--text); border-color: var(--border-strong); }
  .btn-icon:active { transform: scale(0.94); }
  .btn-icon svg { width: 17px; height: 17px; }
  .btn-icon svg, .theme-toggle svg, .btn-primary svg, .link-btn svg { display: block; }

  /* Downloads */
  .downloads { padding: 6px 18px; }
  .downloads-head { display: flex; align-items: center; justify-content: space-between; padding: 12px 0 4px; }
  .downloads-head h2 { font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-muted); }
  .clear-btn { background: none; border: none; color: var(--text-muted); font-size: 12px; cursor: pointer; padding: 4px 6px; border-radius: 7px; transition: color .15s, background .15s; }
  .clear-btn:hover { color: var(--text); background: var(--surface-2); }

  .dl { display: flex; gap: 13px; padding: 14px 0; border-top: 1px solid var(--border); animation: rise .32s cubic-bezier(.16,1,.3,1); }
  .dl:first-of-type { border-top: none; }
  .dl-body { flex: 1; min-width: 0; }
  @keyframes rise { from { opacity: 0; transform: translateY(7px); } to { opacity: 1; transform: none; } }

  .thumb { position: relative; width: 78px; height: 48px; flex-shrink: 0; border-radius: 9px; overflow: hidden; background: var(--surface-2); display: flex; align-items: center; justify-content: center; color: var(--text-muted); }
  .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .thumb .ph { width: 22px; height: 22px; }
  .thumb-open { cursor: pointer; }
  .thumb-open .play { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(8,9,12,.46); opacity: 0; transition: opacity .15s; }
  .thumb-open:hover .play { opacity: 1; }
  .thumb-open .play svg { width: 22px; height: 22px; color: #fff; }

  .dl-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .dl-title { font-size: 14px; font-weight: 500; flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  .pill { display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 500; padding: 3px 10px; border-radius: var(--radius-pill); white-space: nowrap; flex-shrink: 0; }
  .pill .dot { width: 6px; height: 6px; border-radius: 50%; }
  .pill-running { background: var(--accent-soft); color: var(--accent-text); }
  .pill-done { background: var(--success-bg); color: var(--success-text); }
  .pill-done .dot { background: var(--success-dot); }
  .pill-error { background: var(--danger-bg); color: var(--danger-text); }
  .pill-error .dot { background: var(--danger-dot); }
  .spinner { width: 11px; height: 11px; border-radius: 50%; border: 2px solid currentColor; border-top-color: transparent; animation: spin .7s linear infinite; opacity: .85; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .bar { position: relative; height: 7px; border-radius: var(--radius-pill); background: var(--surface-2); overflow: hidden; margin-top: 11px; }
  .bar > i { display: block; height: 100%; border-radius: var(--radius-pill); background: var(--accent); transition: width .35s cubic-bezier(.16,1,.3,1); }
  .bar.active > i::after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,.28), transparent); animation: sweep 1.5s linear infinite; }
  @keyframes sweep { from { transform: translateX(-100%); } to { transform: translateX(100%); } }

  .dl-meta { font-size: 12px; color: var(--text-muted); margin-top: 7px; font-variant-numeric: tabular-nums; }
  .dl-actions { display: flex; gap: 14px; margin-top: 9px; }
  .link-btn { display: inline-flex; align-items: center; gap: 5px; background: none; border: none; padding: 0; font-size: 12px; color: var(--accent-text); cursor: pointer; }
  .link-btn:hover { text-decoration: underline; }
  .link-btn.muted { color: var(--text-muted); }
  .link-btn.muted:hover { color: var(--text-secondary); }
  .link-btn svg { width: 13px; height: 13px; }

  .log { margin-top: 10px; background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 11px; font-family: "Cascadia Code", "Consolas", ui-monospace, monospace; font-size: 11px; line-height: 1.55; color: var(--text-secondary); max-height: 170px; overflow-y: auto; white-space: pre-wrap; word-break: break-all; display: none; -webkit-user-select: text; user-select: text; }

  /* Empty state */
  .empty { padding: 40px 24px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 12px; }
  .empty .empty-icon { width: 46px; height: 46px; border-radius: 14px; background: var(--surface-2); display: flex; align-items: center; justify-content: center; color: var(--text-muted); }
  .empty .empty-icon svg { width: 24px; height: 24px; }
  .empty p { font-size: 13.5px; color: var(--text-muted); max-width: 280px; line-height: 1.5; }

  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 99px; border: 3px solid transparent; background-clip: content-box; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); background-clip: content-box; border: 3px solid transparent; }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; animation: none !important; }
  }
</style>
</head>
<body>
<div class="app">

  <header class="app-header">
    <div class="brand">
      <svg class="brand-mark" viewBox="0 0 1024 1024" aria-hidden="true">
        <path class="logo-bg" d="M326.25,140.76l4.84-.04,263.26-.14,78.68.06c23.26.05,47.5-1.09,70.19,3.96,33.45,7.17,64.12,23.85,88.32,48.02,34.03,33.41,53.16,79.12,53.07,126.81l.24,267.21-.2,77.18c-.01,26.03,1.42,55.23-4.28,80.39-7.65,33.59-24.57,64.37-48.85,88.82-10.41,10.43-23.99,20.35-36.75,27.69-31.98,18.4-60.71,24.07-97.04,24.17l-276.24-.27c-24.34.18-48.69.21-73.03.1-22.25,0-41.79.86-63.7-3.46-68.11-13.42-122.48-65.74-138.94-133.21-5.97-24.48-4.9-46.34-4.91-71.43l-.06-63.28-.12-287.01c-.37-51.53,14.78-95.26,51.4-132.31,28.92-29.26,67.02-47.69,107.91-52.21,9.02-1.03,17.14-1,26.2-1.06Z"/>
        <path fill="#fd1b24" d="M508.86,319.24c14.46-.23,28.17.34,42.54.56,21.1.33,41.52.86,62.6,1.83,26.06,1.2,50.4,1.67,76.44,4.85,24.6,2.32,44.12,12.05,59.44,31.76,14.94,19.2,18.35,38.78,21.59,62.11,5.04,38.33,6.2,77.08,3.46,115.65-1.37,19.18-3.98,37.04-6.36,56.02-9.5-4.6-19.8-8.91-29.48-13.25l-34.77-15.91c-3.84,1.83-11.89,6.99-15.78,9.33l-33.43,20.3c-14.89-9.59-30.35-18.83-44.98-28.72l-46.57,21.59c-14.87-6.01-32.3-11.61-47.67-17.24-6.49-1.07-41.71,13.16-51.47,15.73-13.59-5.5-29.66-13.96-43.58-20.19-7.44,4.57-14.75,9.35-21.92,14.34-6.76,4.67-14.8,10.58-22,14.2-11.35-6.02-24.1-14.98-35.55-21.26-4.84-2.65-9.3-5.88-14.45-8.12-6.38,2.23-19.44,8.9-25.97,12l-43.5,20.53c-8.23-55.43-9.76-113.19-3.46-168.88,3.04-26.93,7.43-53.99,26.99-74.48,9.83-10.27,22.14-17.83,35.75-21.94,19.71-5.83,60.88-6.66,82.05-7.8,36.46-1.96,73.57-2.3,110.09-3.01Z"/>
        <path fill="#ffffff" d="M466.42,419.07c5.45-.25,7.89,1.43,12.47,3.98,5.42,3.02,10.81,6.11,16.22,9.14,16.45,9.13,32.83,18.41,49.12,27.83,11.95,6.82,24.23,13.47,35.93,20.42,7.46,4.35,8.48,15.58.68,20.18-14.02,8.27-28.88,16.32-43.12,24.13-20.67,12.06-42.58,23.4-63.74,34.65-3.9,2.07-6.64,2.72-10.87,1.16-10.69-3.95-8.19-19.39-8.26-28.88l-.16-34.72c-.06-20.81-.23-41.63-.02-62.44.09-9.17,2.96-12.75,11.76-15.45Z"/>
        <path fill="#ffffff" d="M513.49,600.58c10.68,2.54,26.07,7.58,36.99,10.74l-.05,116.2,45.46.56c-26.65,31.71-56.05,63.91-83.45,95.4-9.6-11.67-20.42-22.61-29.88-34.21-17.07-20.93-36-40.65-53.13-61.38l46.27.03c.39-11.31.08-24.04.08-35.49l-.21-79.43c12.76-4.23,25.02-8.56,37.91-12.43Z"/>
        <path fill="#fd1b24" d="M704.47,594.91c4.79.76,50.27,22.92,57.51,26.2-4.37,10.93-9.7,20.6-17.75,29.33-8.7,9.3-19.6,16.25-31.7,20.22-13.37,4.51-32.07,5.69-46.5,6.74-19.8,1.45-39.63,2.45-59.48,3-9.33.24-18.52.65-27.9.83-.71-22.01-.15-46.51-.11-68.68,9.77-5.19,20.93-10.03,30.34-15.61,11.81,8.73,31.94,21.4,44.51,29.27,14.51-7.42,36.07-22.22,51.07-31.29Z"/>
        <path fill="#fd1b24" d="M325.51,595.06c17.25,9.22,33.82,21.23,51.77,31.05,14.05-8.07,30.37-20.07,43.98-29.13,7.73,3.55,20.33,8.96,27.14,13.22l.13,41.49c.02,9.61.26,19.94-.58,29.46-9.45.08-19.76-.53-29.27-.92-27.11-.94-54.1-1.6-81.08-4.63-4.61-.52-9.05-.94-13.62-1.88-6.06-1.21-11.95-3.16-17.54-5.8-18.88-8.69-33.52-24.56-40.66-44.08,19.84-9.72,39.75-19.31,59.72-28.77Z"/>
      </svg>
      <div class="brand-text">
        <span class="brand-name">Rippr</span>
        <span class="brand-tag">Download video and audio</span>
      </div>
    </div>
    <button class="theme-toggle" id="themeToggle" onclick="toggleTheme()" aria-label="Toggle theme" title="Toggle theme">
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    </button>
  </header>

  <section class="card composer">
    <div class="url-row">
      <div class="input-wrap">
        <svg class="lead-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg>
        <input type="text" id="url" placeholder="Paste a link to download" autocomplete="off" spellcheck="false" />
      </div>
      <button class="btn-primary" id="downloadBtn" onclick="startDownload()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg>
        Download
      </button>
    </div>
    <p class="hint" id="hint"></p>

    <div class="controls">
      <div class="control grow">
        <label>Quality</label>
        <div class="select-wrap">
          <select id="format" onchange="updateContainerOptions()">
            <option value="bestvideo+bestaudio/best">Best available</option>
            <option value="bestvideo[height<=1080]+bestaudio/best[height<=1080]">1080p</option>
            <option value="bestvideo[height<=720]+bestaudio/best[height<=720]">720p</option>
            <option value="bestvideo[height<=480]+bestaudio/best[height<=480]">480p</option>
            <option value="bestvideo[height<=360]+bestaudio/best[height<=360]">360p</option>
            <option value="bestaudio/best" data-audio="1">Audio only</option>
          </select>
          <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </div>
      </div>
      <div class="control grow">
        <label>Format</label>
        <div class="select-wrap">
          <select id="container"></select>
          <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </div>
      </div>
      <div class="control">
        <label>Subtitles</label>
        <label class="switch">
          <input type="checkbox" id="subs" />
          <span class="track"></span>
        </label>
      </div>
    </div>

    <div class="dir-row">
      <span class="dir-label">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
        Save to
      </span>
      <input type="text" id="outdir" value="{{ download_dir }}" spellcheck="false" />
      <button class="btn-icon" onclick="pickFolder()" title="Choose folder" aria-label="Choose folder">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M12 11v5M9.5 13.5 12 11l2.5 2.5"/></svg>
      </button>
    </div>
  </section>

  <section class="card downloads" id="downloadsCard" style="display:none">
    <div class="downloads-head">
      <h2>Downloads</h2>
      <button class="clear-btn" id="clearBtn" onclick="clearFinished()">Clear finished</button>
    </div>
    <div id="downloadsList"></div>
  </section>

  <section class="card empty" id="emptyCard">
    <div class="empty-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14l1.8 4.5A2 2 0 0 0 7.6 20h8.8a2 2 0 0 0 1.8-1.5L20 14"/><path d="M4 14V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8"/><path d="M9 13a3 3 0 0 0 6 0"/></svg>
    </div>
    <p>No downloads yet. Paste a link above to get started.</p>
  </section>

</div>

<script>
const jobs = {};

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem('rippr-theme', next); } catch (e) {}
}

function pickFolder() {
  fetch('/pick-folder').then(r => r.json()).then(d => {
    if (d.path) document.getElementById('outdir').value = d.path;
  });
}

function startDownload() {
  const url = document.getElementById('url').value.trim();
  if (!url) { flash('Paste a link first'); return; }
  const format    = document.getElementById('format').value;
  const container = document.getElementById('container').value;
  const subs      = document.getElementById('subs').checked;
  const outdir    = document.getElementById('outdir').value.trim();
  const btn = document.getElementById('downloadBtn');
  btn.disabled = true;
  document.getElementById('hint').textContent = '';
  fetch('/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, format, container, subs, outdir })
  }).then(r => r.json()).then(data => {
    btn.disabled = false;
    document.getElementById('url').value = '';
    addJob(data.id, url, outdir);
    pollJob(data.id);
  }).catch(() => {
    btn.disabled = false;
    flash('Could not start the download');
  });
}

function addJob(id, url, outdir) {
  jobs[id] = { url, outdir, progress: 0, status: 'running', log: '', title: url };
  renderJobs();
}

function pollJob(id) {
  const es = new EventSource('/progress/' + id);
  es.onmessage = (e) => {
    const d = JSON.parse(e.data);
    jobs[id] = { ...jobs[id], ...d };
    renderJob(id);
    if (d.status === 'done' || d.status === 'error') es.close();
  };
  es.onerror = () => { es.close(); if (jobs[id] && jobs[id].status === 'running') { jobs[id].status = 'error'; renderJob(id); } };
}

function renderJobs() {
  const ids = Object.keys(jobs);
  document.getElementById('downloadsCard').style.display = ids.length ? '' : 'none';
  document.getElementById('emptyCard').style.display = ids.length ? 'none' : '';
  const list = document.getElementById('downloadsList');
  list.innerHTML = '';
  ids.slice().reverse().forEach(id => {
    const el = document.createElement('div');
    el.id = 'job-' + id;
    el.className = 'dl';
    list.appendChild(el);
    renderJob(id);
  });
  updateClearBtn();
}

function renderJob(id) {
  const j = jobs[id];
  const el = document.getElementById('job-' + id);
  if (!el) return;
  const running = j.status === 'running';
  const pct = Math.round(j.progress || 0);
  const title = (j.title || j.url).length > 64 ? (j.title || j.url).slice(0, 64) + '…' : (j.title || j.url);
  const logId = 'log-' + id;
  const wasOpen = document.getElementById(logId)?.style.display === 'block';

  let pill;
  if (j.status === 'done')  pill = '<span class="pill pill-done"><span class="dot"></span>Done</span>';
  else if (j.status === 'error') pill = '<span class="pill pill-error"><span class="dot"></span>Failed</span>';
  else pill = '<span class="pill pill-running"><span class="spinner"></span>Downloading</span>';

  let progressHtml = '';
  if (running) {
    progressHtml = `
      <div class="bar active"><i style="width:${pct}%"></i></div>
      <div class="dl-meta">${escHtml(j.progressText || pct + '%')}</div>`;
  }

  let actions = `<button class="link-btn muted" onclick="toggleLog('${id}')">${wasOpen ? 'Hide log' : 'Show log'}</button>`;
  if (j.status === 'done') {
    actions = `<button class="link-btn" onclick="openFolder('${id}')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
        Show in folder
      </button>` + actions;
  }

  const canPlay = j.status === 'done' && j.filepath;
  const filmIcon = '<svg class="ph" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18M8 5v14M16 5v14"/></svg>';
  const thumbImg = j.thumbnail
    ? `<img src="${escHtml(j.thumbnail)}" alt="" onerror="this.remove()">`
    : filmIcon;
  const playOverlay = '<span class="play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span>';
  const thumb = `<div class="thumb ${canPlay ? 'thumb-open' : ''}" ${canPlay ? `onclick="openFile('${id}')" title="Play video"` : ''}>${thumbImg}${canPlay ? playOverlay : ''}</div>`;

  el.innerHTML = `
    ${thumb}
    <div class="dl-body">
      <div class="dl-top">
        <span class="dl-title" title="${escHtml(j.url)}">${escHtml(title)}</span>
        ${pill}
      </div>
      ${progressHtml}
      <div class="dl-actions">${actions}</div>
      <pre class="log" id="${logId}" style="display:${wasOpen ? 'block' : 'none'}">${escHtml(j.log || '')}</pre>
    </div>
  `;
  if (wasOpen) { const lb = document.getElementById(logId); lb.scrollTop = lb.scrollHeight; }
  updateClearBtn();
}

function openFile(id) {
  const j = jobs[id];
  if (!j || !j.filepath) return;
  fetch('/open-file?path=' + encodeURIComponent(j.filepath));
}

function openFolder(id) {
  const j = jobs[id];
  if (!j || !j.outdir) return;
  fetch('/open-folder?path=' + encodeURIComponent(j.outdir));
}

function toggleLog(id) {
  const lb = document.getElementById('log-' + id);
  if (!lb) return;
  const open = lb.style.display !== 'block';
  lb.style.display = open ? 'block' : 'none';
  const btn = lb.parentElement.querySelector('.link-btn.muted');
  if (btn) btn.textContent = open ? 'Hide log' : 'Show log';
  if (open) lb.scrollTop = lb.scrollHeight;
}

function clearFinished() {
  Object.keys(jobs).forEach(id => {
    if (jobs[id].status === 'done' || jobs[id].status === 'error') delete jobs[id];
  });
  renderJobs();
}

function updateClearBtn() {
  const anyFinished = Object.values(jobs).some(j => j.status === 'done' || j.status === 'error');
  const btn = document.getElementById('clearBtn');
  if (btn) btn.style.visibility = anyFinished ? 'visible' : 'hidden';
}

function escHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function flash(msg) { document.getElementById('hint').textContent = msg; }

const VIDEO_CONTAINERS = [
  { value: 'mp4',  label: 'MP4' },
  { value: 'mkv',  label: 'MKV' },
  { value: 'webm', label: 'WebM' },
  { value: 'mov',  label: 'MOV' },
  { value: 'avi',  label: 'AVI' },
];
const AUDIO_CONTAINERS = [
  { value: 'mp3',  label: 'MP3' },
  { value: 'm4a',  label: 'M4A' },
  { value: 'opus', label: 'Opus' },
  { value: 'flac', label: 'FLAC' },
  { value: 'wav',  label: 'WAV' },
];

function updateContainerOptions() {
  const sel = document.getElementById('format');
  const isAudio = sel.options[sel.selectedIndex].dataset.audio === '1';
  const list = isAudio ? AUDIO_CONTAINERS : VIDEO_CONTAINERS;
  const c = document.getElementById('container');
  c.innerHTML = list.map(o => `<option value="${o.value}">${o.label}</option>`).join('');
}

document.getElementById('url').addEventListener('keydown', e => { if (e.key === 'Enter') startDownload(); });
updateContainerOptions();
updateClearBtn();
document.getElementById('url').focus();
</script>
</body>
</html>"""


def current_theme():
    try:
        import winreg
        k = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        val, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
        return "light" if val == 1 else "dark"
    except Exception:
        return "dark"


@app.route("/")
def index():
    return render_template_string(HTML, download_dir=DOWNLOAD_DIR, initial_theme=current_theme())


@app.route("/pick-folder")
def pick_folder():
    result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
    if result and len(result) > 0:
        return jsonify({"path": result[0]})
    return jsonify({"path": None})


@app.route("/open-folder")
def open_folder():
    path = request.args.get("path", "")
    if path and os.path.isdir(path):
        try:
            os.startfile(path)
            return jsonify({"ok": True})
        except Exception:
            pass
    return jsonify({"ok": False})


@app.route("/open-file")
def open_file():
    path = request.args.get("path", "")
    if path and os.path.isfile(path):
        try:
            os.startfile(path)
            return jsonify({"ok": True})
        except Exception:
            pass
    return jsonify({"ok": False})


@app.route("/start", methods=["POST"])
def start():
    data = request.json
    url       = data.get("url", "").strip()
    fmt       = data.get("format", "bestvideo+bestaudio/best")
    container = data.get("container", "mp4")
    subs      = data.get("subs", False)
    outdir    = data.get("outdir", DOWNLOAD_DIR).strip() or DOWNLOAD_DIR

    AUDIO_FMTS = {"mp3", "m4a", "opus", "flac", "wav"}
    is_audio   = container in AUDIO_FMTS

    job_id = str(uuid.uuid4())[:8]
    downloads[job_id] = {
        "status": "running", "progress": 0, "progressText": "",
        "log": "", "title": url, "url": url, "thumbnail": "", "filepath": "",
    }

    def run():
        def progress_hook(d):
            if d["status"] == "downloading":
                pct_str = d.get("_percent_str", "").strip()
                speed   = d.get("_speed_str", "").strip()
                eta     = d.get("_eta_str", "").strip()
                total   = d.get("_total_bytes_str", d.get("_total_bytes_estimate_str", "")).strip()
                try:
                    pct_val = float(pct_str.replace("%", ""))
                except Exception:
                    pct_val = downloads[job_id]["progress"]
                downloads[job_id]["progress"] = pct_val
                downloads[job_id]["progressText"] = f"{pct_str} of {total} at {speed} ETA {eta}"
                downloads[job_id]["log"] += f"{pct_str} of {total} at {speed} ETA {eta}\n"
            elif d["status"] == "finished":
                downloads[job_id]["log"] += f"Finished: {os.path.basename(d.get('filename',''))}\n"
                downloads[job_id]["progress"] = 100

        ydl_opts = {
            "format": fmt,
            "outtmpl": os.path.join(outdir, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": False,
            "writesubtitles": subs,
            "writeautomaticsub": subs,
            "subtitleslangs": ["en"] if subs else [],
        }
        if is_audio:
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": container,
                "preferredquality": "0",
            }]
        else:
            ydl_opts["merge_output_format"] = container
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    downloads[job_id]["title"] = info.get("title", url)
                    downloads[job_id]["thumbnail"] = info.get("thumbnail") or ""
                    downloads[job_id]["log"] += f"Title: {info.get('title', url)}\nURL: {url}\n\n"
                dl_info = ydl.extract_info(url, download=True)
                fp = ""
                try:
                    reqs = (dl_info or {}).get("requested_downloads") or []
                    if reqs:
                        fp = reqs[0].get("filepath") or reqs[0].get("_filename") or ""
                except Exception:
                    fp = ""
                downloads[job_id]["filepath"] = fp
            downloads[job_id]["status"] = "done"
            downloads[job_id]["progress"] = 100
        except Exception as ex:
            downloads[job_id]["status"] = "error"
            downloads[job_id]["log"] += f"\nError: {ex}"

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"id": job_id})


@app.route("/progress/<job_id>")
def progress_stream(job_id):
    def stream():
        while True:
            job = downloads.get(job_id, {})
            payload = {
                "status":       job.get("status", "running"),
                "progress":     job.get("progress", 0),
                "progressText": job.get("progressText", ""),
                "title":        job.get("title", ""),
                "log":          job.get("log", ""),
                "url":          job.get("url", ""),
                "thumbnail":    job.get("thumbnail", ""),
                "filepath":     job.get("filepath", ""),
            }
            yield f"data: {json.dumps(payload)}\n\n"
            if payload["status"] in ("done", "error"):
                break
            time.sleep(0.5)
    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def start_flask():
    app.run(debug=False, port=5000, threaded=True, use_reloader=False)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    time.sleep(0.8)

    bg = "#0b0c0f" if current_theme() == "dark" else "#f3f4f7"
    webview.create_window(
        title="Rippr",
        url="http://localhost:5000",
        width=720,
        height=680,
        min_size=(540, 540),
        resizable=True,
        background_color=bg,
    )
    webview.start()
