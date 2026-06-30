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

  :root {
    --ease-out: cubic-bezier(.16, 1, .3, 1);
    --ease-quart: cubic-bezier(.25, 1, .5, 1);
    --dur-fast: .14s; --dur: .2s; --dur-slow: .34s;
    --r-stage: 22px; --r-card: 18px; --r: 12px; --r-sm: 9px; --r-pill: 999px;
    --z-base: 1; --z-sticky: 50; --z-overlay: 100; --z-suggest: 200; --z-toast: 400;
    --maxw: 660px;
  }

  :root, [data-theme="light"] {
    --bg: #f4f5f8;
    --bg-2: #e9ebf1;
    --surface: #ffffff;
    --surface-2: #eef0f4;
    --surface-3: #e5e8ef;
    --border: rgba(17, 20, 28, 0.09);
    --border-strong: rgba(17, 20, 28, 0.15);
    --text: #14161b;
    --text-secondary: #4b515b;
    --text-muted: #6b727d;
    --red: #fd1b24;            /* brand: glow, progress, logo */
    --red-strong: #ea0f18;     /* primary fills, AA with white */
    --red-hover: #cf101a;
    --red-text: #c8101b;       /* red text/links on light, AA */
    --red-soft: rgba(253, 27, 36, 0.10);
    --red-line: rgba(253, 27, 36, 0.30);
    --red-glow: rgba(253, 27, 34, 0.28);
    --logo-bg: #0d0d10;
    --success-bg: #e2f6ea; --success-text: #157a45; --success-dot: #1ea35d;
    --danger-bg: #fdeceb;  --danger-text: #c0271f;  --danger-dot: #df4444;
    --warn-bg: #fef3e2;    --warn-text: #b06a12;
    --shadow-sm: 0 1px 2px rgba(16,24,40,.05);
    --shadow: 0 1px 2px rgba(16,24,40,.05), 0 12px 34px rgba(16,24,40,.08);
    --shadow-lg: 0 2px 4px rgba(16,24,40,.06), 0 24px 60px rgba(16,24,40,.12);
    --body-glow: radial-gradient(120% 75% at 50% -12%, rgba(253,27,34,.06), transparent 56%);
    --stage-grad: linear-gradient(180deg, #ffffff, #fbfbfd);
    --track: #fff;
  }

  [data-theme="dark"] {
    --bg: #0b0c10;
    --bg-2: #07080b;
    --surface: #14161c;
    --surface-2: #1b1e26;
    --surface-3: #232732;
    --border: rgba(255, 255, 255, 0.08);
    --border-strong: rgba(255, 255, 255, 0.15);
    --text: #f3f4f7;
    --text-secondary: #aab0bb;
    --text-muted: #8b919c;
    --red: #fd1b24;
    --red-strong: #ea0f18;
    --red-hover: #ff3d44;
    --red-text: #ff7066;       /* red text/links on dark, AA */
    --red-soft: rgba(253, 27, 36, 0.16);
    --red-line: rgba(253, 27, 36, 0.42);
    --red-glow: rgba(253, 27, 34, 0.45);
    --logo-bg: #23262e;
    --success-bg: #11271a; --success-text: #5fd99a; --success-dot: #34d27f;
    --danger-bg: #311316;  --danger-text: #ff9a93;  --danger-dot: #ff6b6b;
    --warn-bg: #332512;    --warn-text: #f3c073;
    --shadow-sm: 0 1px 2px rgba(0,0,0,.4);
    --shadow: 0 1px 2px rgba(0,0,0,.35), 0 14px 36px rgba(0,0,0,.4);
    --shadow-lg: 0 2px 6px rgba(0,0,0,.45), 0 30px 70px rgba(0,0,0,.55);
    --body-glow: radial-gradient(120% 80% at 50% -14%, rgba(253,27,34,.13), transparent 58%);
    --stage-grad: linear-gradient(180deg, #181b22, #121419);
    --track: #f3f4f7;
  }

  html, body { height: 100%; }
  body {
    font-family: "Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    background: var(--body-glow), var(--bg);
    background-attachment: fixed;
    color: var(--text);
    -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
    -webkit-user-select: none; user-select: none;
    padding: 20px 22px 34px;
    display: flex; justify-content: center;
    transition: background-color var(--dur-slow) ease, color var(--dur-slow) ease;
  }
  .app { width: 100%; max-width: var(--maxw); display: flex; flex-direction: column; gap: 16px; }

  /* ---------- Header ---------- */
  .app-header { display: flex; align-items: center; justify-content: space-between; padding: 2px 2px 0; }
  .brand { display: flex; align-items: center; gap: 11px; }
  .brand-mark { width: 36px; height: 36px; flex-shrink: 0; display: block; filter: drop-shadow(0 4px 10px var(--red-glow)); }
  .brand-mark .logo-bg { fill: var(--logo-bg); transition: fill var(--dur-slow) ease; }
  .brand-text { display: flex; flex-direction: column; line-height: 1; }
  .brand-name { font-size: 19px; font-weight: 700; letter-spacing: 0.02em; }
  .brand-name b { color: var(--red-text); font-weight: 700; }
  .brand-tag { font-size: 11.5px; color: var(--text-muted); margin-top: 3px; letter-spacing: .01em; }

  .header-right { display: flex; align-items: center; gap: 10px; }
  .status { display: inline-flex; align-items: center; gap: 7px; font-size: 12px; color: var(--text-muted); padding: 6px 11px 6px 9px; border-radius: var(--r-pill); border: 1px solid var(--border); background: var(--surface); transition: color var(--dur) ease, border-color var(--dur) ease; }
  .status .led { width: 7px; height: 7px; border-radius: 50%; background: var(--text-muted); position: relative; transition: background var(--dur) ease; }
  .status.active { color: var(--red-text); border-color: var(--red-line); }
  .status.active .led { background: var(--red); }
  .status.active .led::after { content: ""; position: absolute; inset: -4px; border-radius: 50%; border: 1px solid var(--red); animation: ping 1.4s var(--ease-out) infinite; }
  @keyframes ping { 0% { transform: scale(.6); opacity: .9; } 100% { transform: scale(1.9); opacity: 0; } }

  .theme-toggle {
    width: 36px; height: 36px; border-radius: var(--r); flex-shrink: 0;
    background: var(--surface); border: 1px solid var(--border);
    color: var(--text-secondary); cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background var(--dur-fast), border-color var(--dur-fast), color var(--dur-fast), transform var(--dur-fast);
  }
  .theme-toggle:hover { color: var(--text); border-color: var(--border-strong); }
  .theme-toggle:active { transform: scale(0.92); }
  .theme-toggle svg { width: 18px; height: 18px; display: block; }
  .theme-toggle .icon-moon { display: none; }
  [data-theme="dark"] .theme-toggle .icon-moon { display: block; }
  [data-theme="dark"] .theme-toggle .icon-sun { display: none; }

  /* ---------- Console (stage + controls) ---------- */
  .console {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--r-card); box-shadow: var(--shadow);
    transition: background-color var(--dur-slow) ease, border-color var(--dur-slow) ease, box-shadow var(--dur) ease;
  }

  .stage {
    position: relative; padding: 22px 22px 20px;
    border-radius: var(--r-card) var(--r-card) 0 0;
    background: var(--stage-grad);
    overflow: hidden;
    transition: box-shadow var(--dur) ease;
  }
  .stage-glow {
    position: absolute; left: 50%; top: -40%; width: 70%; height: 120%;
    transform: translateX(-50%);
    background: radial-gradient(closest-side, var(--red-glow), transparent 72%);
    opacity: 0; filter: blur(14px); pointer-events: none;
    transition: opacity var(--dur-slow) var(--ease-out);
  }
  .stage:focus-within .stage-glow { opacity: .55; }

  .field-row { position: relative; z-index: var(--z-base); display: flex; gap: 11px; align-items: stretch; }
  .field {
    flex: 1; min-width: 0; display: flex; align-items: center; gap: 10px;
    height: 56px; padding: 0 14px 0 16px;
    background: var(--surface-2); border: 1.5px solid transparent; border-radius: var(--r);
    transition: border-color var(--dur), box-shadow var(--dur), background var(--dur);
  }
  .stage:focus-within .field { border-color: var(--red); background: var(--surface); box-shadow: 0 0 0 4px var(--red-soft); }
  .field .lead { width: 20px; height: 20px; flex-shrink: 0; color: var(--text-muted); transition: color var(--dur); }
  .stage:focus-within .field .lead { color: var(--red); }
  #url {
    flex: 1; min-width: 0; height: 100%; border: none; outline: none; background: none;
    color: var(--text); font-size: 16.5px; font-weight: 500; letter-spacing: -0.01em;
    -webkit-user-select: text; user-select: text;
  }
  #url::placeholder { color: var(--text-muted); font-weight: 400; }
  .field .clear {
    width: 26px; height: 26px; flex-shrink: 0; border: none; background: var(--surface-3);
    color: var(--text-muted); border-radius: 50%; cursor: pointer; display: none;
    align-items: center; justify-content: center; transition: color var(--dur-fast), background var(--dur-fast);
  }
  .field .clear:hover { color: var(--text); background: var(--border-strong); }
  .field .clear svg { width: 13px; height: 13px; }
  .field.has-text .clear { display: flex; }

  .rip-btn {
    flex-shrink: 0; height: 56px; padding: 0 22px;
    display: inline-flex; align-items: center; gap: 9px;
    background: var(--red-strong); color: #fff;
    border: none; border-radius: var(--r);
    font-size: 16px; font-weight: 700; letter-spacing: 0.01em; cursor: pointer;
    box-shadow: 0 6px 18px var(--red-glow);
    transition: background var(--dur-fast), transform var(--dur-fast), box-shadow var(--dur), opacity var(--dur);
  }
  .rip-btn svg { width: 19px; height: 19px; display: block; }
  .rip-btn:hover { background: var(--red-hover); box-shadow: 0 8px 26px var(--red-glow); transform: translateY(-1px); }
  .rip-btn:active { transform: translateY(0) scale(0.97); }
  .rip-btn:disabled { opacity: 0.7; cursor: progress; transform: none; box-shadow: none; }
  .rip-btn .btn-spin { width: 17px; height: 17px; border-radius: 50%; border: 2px solid rgba(255,255,255,.45); border-top-color: #fff; animation: spin .7s linear infinite; }

  .stage-foot { position: relative; z-index: var(--z-base); display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 12px; min-height: 20px; padding-left: 2px; }
  .stage-hint { font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .stage-hint.err { color: var(--danger-text); }
  .kbd { font-family: inherit; font-size: 11px; font-weight: 600; color: var(--text-secondary); background: var(--surface-2); border: 1px solid var(--border); border-bottom-width: 2px; border-radius: 6px; padding: 1px 6px; letter-spacing: .02em; }
  .dot-sep { width: 3px; height: 3px; border-radius: 50%; background: var(--text-muted); opacity: .6; }

  /* Clipboard suggestion chip */
  .clip {
    display: none; align-items: center; gap: 9px; max-width: 60%;
    padding: 7px 8px 7px 12px; border-radius: var(--r-pill);
    background: var(--red-soft); border: 1px solid var(--red-line);
    color: var(--red-text); font-size: 12px; font-weight: 600; cursor: pointer;
    transition: background var(--dur-fast);
  }
  .clip.show { display: inline-flex; animation: slideIn var(--dur-slow) var(--ease-out); }
  .clip:hover { background: var(--red-line); }
  .clip .clip-url { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; opacity: .92; -webkit-user-select: none; user-select: none; }
  .clip .clip-go { font-weight: 700; white-space: nowrap; }
  @keyframes slideIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

  /* Drop overlay */
  .drop-veil {
    position: absolute; inset: 0; z-index: var(--z-overlay);
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
    background: color-mix(in srgb, var(--surface) 78%, transparent);
    border: 2px dashed var(--red); border-radius: var(--r-card) var(--r-card) 0 0;
    color: var(--red-text); font-size: 15px; font-weight: 700;
    opacity: 0; pointer-events: none; transform: scale(.99);
    transition: opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-out);
  }
  .drop-veil svg { width: 30px; height: 30px; animation: bobble 1.1s var(--ease-out) infinite; }
  @keyframes bobble { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
  .stage.drag .drop-veil { opacity: 1; transform: scale(1); }
  .stage.drag { box-shadow: inset 0 0 0 1px var(--red), 0 0 0 4px var(--red-soft); }
  .stage.pulse::after {
    content: ""; position: absolute; inset: 0; border-radius: inherit; pointer-events: none;
    box-shadow: inset 0 0 0 2px var(--red); animation: ripPulse .6s var(--ease-out) forwards;
  }
  @keyframes ripPulse { 0% { opacity: .9; } 100% { opacity: 0; } }

  /* ---------- Controls bar ---------- */
  .controls-bar { padding: 16px 22px 18px; border-top: 1px solid var(--border); }
  .controls { display: flex; gap: 11px; flex-wrap: wrap; align-items: flex-end; }
  .control { display: flex; flex-direction: column; gap: 7px; }
  .control.grow { flex: 1; min-width: 124px; }
  .control label { font-size: 11px; font-weight: 600; color: var(--text-muted); letter-spacing: 0.04em; text-transform: uppercase; padding-left: 1px; }
  .select-wrap { position: relative; }
  .select-wrap .chev { position: absolute; right: 11px; top: 50%; transform: translateY(-50%); width: 15px; height: 15px; color: var(--text-muted); pointer-events: none; }
  select {
    width: 100%; height: 42px; padding: 0 34px 0 13px;
    -webkit-appearance: none; appearance: none;
    background: var(--surface-2); border: 1.5px solid transparent; border-radius: var(--r);
    color: var(--text); font-size: 13.5px; font-weight: 500; cursor: pointer; outline: none;
    transition: border-color var(--dur-fast), box-shadow var(--dur-fast), background var(--dur-fast);
  }
  select:hover { border-color: var(--border-strong); }
  select:focus-visible { border-color: var(--red); background: var(--surface); box-shadow: 0 0 0 3px var(--red-soft); }

  /* Subtitles toggle */
  .subs-control label.field-label { margin-bottom: 0; }
  .switch { position: relative; display: inline-flex; align-items: center; height: 42px; cursor: pointer; }
  .switch input { position: absolute; opacity: 0; width: 0; height: 0; }
  .switch .track {
    width: 46px; height: 26px; border-radius: var(--r-pill);
    background: var(--surface-2); border: 1.5px solid var(--border-strong);
    position: relative; transition: background var(--dur), border-color var(--dur);
  }
  .switch .track::after {
    content: ""; position: absolute; top: 2px; left: 2px; width: 18px; height: 18px;
    border-radius: 50%; background: var(--track);
    box-shadow: 0 1px 3px rgba(0,0,0,.3); transition: transform var(--dur) var(--ease-quart), background var(--dur);
  }
  .switch input:checked + .track { background: var(--red-strong); border-color: var(--red-strong); }
  .switch input:checked + .track::after { transform: translateX(20px); background: #fff; }
  .switch input:focus-visible + .track { box-shadow: 0 0 0 3px var(--red-soft); }

  /* Save-to row */
  .dir-row { display: flex; align-items: center; gap: 10px; margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border); }
  .dir-label { display: inline-flex; align-items: center; gap: 7px; font-size: 12.5px; color: var(--text-secondary); white-space: nowrap; }
  .dir-label svg { width: 16px; height: 16px; color: var(--text-muted); }
  #outdir {
    flex: 1; min-width: 0; height: 38px; padding: 0 12px;
    background: var(--surface-2); border: 1.5px solid transparent; border-radius: var(--r);
    color: var(--text-secondary); font-size: 12.5px; outline: none;
    -webkit-user-select: text; user-select: text;
    transition: border-color var(--dur-fast), color var(--dur-fast), box-shadow var(--dur-fast);
  }
  #outdir:focus { border-color: var(--red); color: var(--text); box-shadow: 0 0 0 3px var(--red-soft); }
  .btn-icon {
    width: 38px; height: 38px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
    background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--r);
    color: var(--text-secondary); cursor: pointer;
    transition: background var(--dur-fast), color var(--dur-fast), border-color var(--dur-fast), transform var(--dur-fast);
  }
  .btn-icon:hover { color: var(--text); border-color: var(--border-strong); }
  .btn-icon:active { transform: scale(0.93); }
  .btn-icon svg { width: 17px; height: 17px; display: block; }

  /* ---------- Activity ---------- */
  .activity { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-card); box-shadow: var(--shadow); overflow: hidden; transition: background-color var(--dur-slow) ease, border-color var(--dur-slow) ease; }
  .activity-head { display: flex; align-items: center; justify-content: space-between; padding: 15px 20px 13px; }
  .activity-title { display: flex; align-items: center; gap: 9px; }
  .activity-title h2 { font-size: 13px; font-weight: 700; letter-spacing: 0.02em; }
  .count-badge { font-size: 11px; font-weight: 700; color: var(--text-secondary); background: var(--surface-2); border-radius: var(--r-pill); padding: 2px 9px; min-width: 22px; text-align: center; }
  .clear-btn { background: none; border: none; color: var(--text-muted); font-size: 12px; font-weight: 500; cursor: pointer; padding: 5px 9px; border-radius: 8px; transition: color var(--dur-fast), background var(--dur-fast); }
  .clear-btn:hover { color: var(--text); background: var(--surface-2); }

  .dl-list { padding: 0 8px 8px; }
  .dl {
    display: flex; gap: 14px; padding: 14px 12px; border-radius: var(--r);
    animation: rise var(--dur-slow) var(--ease-out);
  }
  .dl + .dl { border-top: 1px solid var(--border); border-radius: 0; }
  .dl-body { flex: 1; min-width: 0; }
  @keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

  .thumb { position: relative; width: 96px; height: 56px; flex-shrink: 0; border-radius: 10px; overflow: hidden; background: var(--surface-2); display: flex; align-items: center; justify-content: center; color: var(--text-muted); border: 1px solid var(--border); }
  .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .thumb .ph { width: 24px; height: 24px; }
  .thumb-open { cursor: pointer; }
  .thumb-open .play { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(8,9,12,.5); opacity: 0; transition: opacity var(--dur-fast); }
  .thumb-open:hover .play { opacity: 1; }
  .thumb-open .play svg { width: 24px; height: 24px; color: #fff; }

  .dl-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .dl-title { font-size: 14.5px; font-weight: 600; flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: -0.01em; }
  .dl-src { font-size: 12px; color: var(--text-muted); margin-top: 3px; display: flex; align-items: center; gap: 6px; }
  .dl-src .src-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--text-muted); opacity: .6; }

  .pill { display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 600; padding: 4px 11px; border-radius: var(--r-pill); white-space: nowrap; flex-shrink: 0; }
  .pill .dot { width: 6px; height: 6px; border-radius: 50%; }
  .pill-running { background: var(--red-soft); color: var(--red-text); }
  .pill-done { background: var(--success-bg); color: var(--success-text); }
  .pill-done .dot { background: var(--success-dot); }
  .pill-error { background: var(--danger-bg); color: var(--danger-text); }
  .pill-error svg { width: 12px; height: 12px; }
  .spinner { width: 11px; height: 11px; border-radius: 50%; border: 2px solid currentColor; border-top-color: transparent; animation: spin .7s linear infinite; opacity: .9; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .bar { position: relative; height: 8px; border-radius: var(--r-pill); background: var(--surface-2); overflow: hidden; margin-top: 12px; }
  .bar > i { display: block; height: 100%; border-radius: var(--r-pill); background: linear-gradient(90deg, var(--red-strong), var(--red)); transition: width var(--dur-slow) var(--ease-out); box-shadow: 0 0 12px var(--red-glow); }
  .bar.active > i::after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,.35), transparent); animation: sweep 1.4s linear infinite; }
  @keyframes sweep { from { transform: translateX(-100%); } to { transform: translateX(100%); } }

  .dl-meta { font-size: 12px; color: var(--text-muted); margin-top: 8px; font-variant-numeric: tabular-nums; letter-spacing: .01em; }
  .dl-actions { display: flex; gap: 16px; margin-top: 10px; }
  .link-btn { display: inline-flex; align-items: center; gap: 5px; background: none; border: none; padding: 0; font-size: 12.5px; font-weight: 600; color: var(--red-text); cursor: pointer; transition: opacity var(--dur-fast); }
  .link-btn:hover { opacity: .75; }
  .link-btn.muted { color: var(--text-muted); font-weight: 500; }
  .link-btn.muted:hover { color: var(--text-secondary); opacity: 1; }
  .link-btn svg { width: 14px; height: 14px; display: block; }

  .log { margin-top: 11px; background: var(--bg); border: 1px solid var(--border); border-radius: var(--r-sm); padding: 12px; font-family: "Cascadia Code", "Cascadia Mono", "Consolas", ui-monospace, monospace; font-size: 11px; line-height: 1.6; color: var(--text-secondary); max-height: 170px; overflow-y: auto; white-space: pre-wrap; word-break: break-all; display: none; -webkit-user-select: text; user-select: text; }

  /* ---------- Empty / teaching state ---------- */
  .empty { padding: 30px 26px 34px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 6px; }
  .empty .empty-icon { width: 52px; height: 52px; border-radius: 16px; background: var(--red-soft); border: 1px solid var(--red-line); display: flex; align-items: center; justify-content: center; color: var(--red-text); margin-bottom: 8px; }
  .empty .empty-icon svg { width: 26px; height: 26px; }
  .empty h3 { font-size: 16px; font-weight: 700; letter-spacing: -0.01em; }
  .empty p { font-size: 13px; color: var(--text-muted); max-width: 320px; line-height: 1.55; }
  .empty-hints { display: flex; gap: 9px; flex-wrap: wrap; justify-content: center; margin-top: 14px; }
  .hint-chip { display: inline-flex; align-items: center; gap: 7px; font-size: 12px; color: var(--text-secondary); background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--r-pill); padding: 6px 12px; }
  .hint-chip svg { width: 14px; height: 14px; color: var(--text-muted); }
  .sites { margin-top: 20px; padding-top: 18px; border-top: 1px solid var(--border); width: 100%; }
  .sites-label { font-size: 11px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-muted); }
  .sites-row { display: flex; gap: 7px; flex-wrap: wrap; justify-content: center; margin-top: 12px; }
  .site { font-size: 12px; font-weight: 500; color: var(--text-secondary); background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px; padding: 5px 10px; }
  .site.more { color: var(--red-text); background: var(--red-soft); border-color: var(--red-line); }

  ::-webkit-scrollbar { width: 11px; height: 11px; }
  ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 99px; border: 3px solid transparent; background-clip: content-box; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); background-clip: content-box; border: 3px solid transparent; }

  @media (max-width: 520px) {
    .rip-btn { width: 56px; justify-content: center; padding: 0; }
    .rip-btn .rip-label { display: none; }
    .control.grow { min-width: 100%; }
  }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; animation-iteration-count: 1 !important; }
    .bar.active > i::after, .status.active .led::after { display: none; }
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
        <span class="brand-name">Ripp<b>r</b></span>
        <span class="brand-tag">Rip video &amp; audio from anywhere</span>
      </div>
    </div>
    <div class="header-right">
      <span class="status" id="status"><span class="led"></span><span id="statusText">Ready</span></span>
      <button class="theme-toggle" id="themeToggle" onclick="toggleTheme()" aria-label="Toggle theme" title="Toggle theme">
        <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
      </button>
    </div>
  </header>

  <section class="console">
    <div class="stage" id="stage">
      <div class="stage-glow"></div>
      <div class="field-row">
        <div class="field" id="field">
          <svg class="lead" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg>
          <input type="text" id="url" placeholder="Paste or drop a link to rip" autocomplete="off" spellcheck="false" />
          <button class="clear" id="clearUrl" onclick="clearUrl()" tabindex="-1" aria-label="Clear">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
          </button>
        </div>
        <button class="rip-btn" id="ripBtn" onclick="startDownload()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg>
          <span class="rip-label">Rip</span>
        </button>
      </div>
      <div class="stage-foot">
        <span class="stage-hint" id="hint">
          <span class="kbd">Ctrl</span><span class="kbd">V</span> to paste
          <span class="dot-sep"></span>
          drag a link in
        </span>
        <button class="clip" id="clip" onclick="acceptClip()" aria-label="Use clipboard link">
          <span class="clip-url" id="clipUrl"></span>
          <span class="clip-go">Use this</span>
        </button>
      </div>
      <div class="drop-veil">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg>
        Drop to rip
      </div>
    </div>

    <div class="controls-bar">
      <div class="controls">
        <div class="control grow">
          <label for="format">Quality</label>
          <div class="select-wrap">
            <select id="format" onchange="updateContainerOptions(); saveSettings();">
              <option value="bestvideo+bestaudio/best">Best available</option>
              <option value="bestvideo[height&lt;=1080]+bestaudio/best[height&lt;=1080]">1080p</option>
              <option value="bestvideo[height&lt;=720]+bestaudio/best[height&lt;=720]">720p</option>
              <option value="bestvideo[height&lt;=480]+bestaudio/best[height&lt;=480]">480p</option>
              <option value="bestvideo[height&lt;=360]+bestaudio/best[height&lt;=360]">360p</option>
              <option value="bestaudio/best" data-audio="1">Audio only</option>
            </select>
            <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
          </div>
        </div>
        <div class="control grow">
          <label for="container">Format</label>
          <div class="select-wrap">
            <select id="container" onchange="saveSettings()"></select>
            <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
          </div>
        </div>
        <div class="control subs-control">
          <label class="field-label">Subtitles</label>
          <label class="switch">
            <input type="checkbox" id="subs" onchange="saveSettings()" />
            <span class="track"></span>
          </label>
        </div>
      </div>

      <div class="dir-row">
        <span class="dir-label">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
          Save to
        </span>
        <input type="text" id="outdir" value="{{ download_dir }}" spellcheck="false" onchange="saveSettings()" />
        <button class="btn-icon" onclick="pickFolder()" title="Choose folder" aria-label="Choose folder">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M12 11v5M9.5 13.5 12 11l2.5 2.5"/></svg>
        </button>
      </div>
    </div>
  </section>

  <section class="activity" id="activityCard" style="display:none">
    <div class="activity-head">
      <div class="activity-title">
        <h2>Activity</h2>
        <span class="count-badge" id="countBadge">0</span>
      </div>
      <button class="clear-btn" id="clearBtn" onclick="clearFinished()">Clear finished</button>
    </div>
    <div class="dl-list" id="downloadsList"></div>
  </section>

  <section class="activity empty" id="emptyCard">
    <div class="empty-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg>
    </div>
    <h3>Ready when you are</h3>
    <p>Paste or drop a link above, choose your quality and format, and Rippr pulls it down.</p>
    <div class="empty-hints">
      <span class="hint-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="4" rx="1"/><path d="M9 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-3"/></svg>
        Paste with <span class="kbd">Ctrl</span><span class="kbd">V</span>
      </span>
      <span class="hint-chip">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg>
        Drag a link in
      </span>
    </div>
    <div class="sites">
      <span class="sites-label">Works with</span>
      <div class="sites-row">
        <span class="site">YouTube</span>
        <span class="site">TikTok</span>
        <span class="site">Instagram</span>
        <span class="site">X</span>
        <span class="site">Reddit</span>
        <span class="site">Vimeo</span>
        <span class="site">SoundCloud</span>
        <span class="site more">+ thousands more</span>
      </div>
    </div>
  </section>

</div>

<script>
const jobs = {};

/* ---------- Theme ---------- */
function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem('rippr-theme', next); } catch (e) {}
}

/* ---------- Settings persistence ---------- */
const $ = id => document.getElementById(id);
function saveSettings() {
  try {
    localStorage.setItem('rippr-fmt', $('format').value);
    localStorage.setItem('rippr-container', $('container').value);
    localStorage.setItem('rippr-subs', $('subs').checked ? '1' : '0');
    localStorage.setItem('rippr-outdir', $('outdir').value);
  } catch (e) {}
}
function loadSettings() {
  try {
    const f = localStorage.getItem('rippr-fmt');
    if (f) { for (const o of $('format').options) if (o.value === f) { $('format').value = f; break; } }
  } catch (e) {}
  updateContainerOptions();
  try {
    const c = localStorage.getItem('rippr-container');
    if (c) { for (const o of $('container').options) if (o.value === c) { $('container').value = c; break; } }
    if (localStorage.getItem('rippr-subs') === '1') $('subs').checked = true;
    const o = localStorage.getItem('rippr-outdir');
    if (o) $('outdir').value = o;
  } catch (e) {}
}

/* ---------- Folder picker ---------- */
function pickFolder() {
  fetch('/pick-folder').then(r => r.json()).then(d => {
    if (d.path) { $('outdir').value = d.path; saveSettings(); }
  });
}

/* ---------- URL field helpers ---------- */
function looksLikeUrl(s) {
  if (!s) return false;
  return /^https?:\/\/\S+\.\S+/i.test(s.trim());
}
function syncField() {
  const has = $('url').value.trim().length > 0;
  $('field').classList.toggle('has-text', has);
}
function clearUrl() {
  $('url').value = '';
  syncField();
  $('url').focus();
}
function flashStage() {
  const s = $('stage');
  s.classList.remove('pulse'); void s.offsetWidth; s.classList.add('pulse');
  setTimeout(() => s.classList.remove('pulse'), 640);
}

/* ---------- Start a rip ---------- */
function startDownload() {
  const url = $('url').value.trim();
  if (!url) { flash('Paste a link first'); $('url').focus(); return; }
  const format    = $('format').value;
  const container = $('container').value;
  const subs      = $('subs').checked;
  const outdir    = $('outdir').value.trim();
  const btn = $('ripBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="btn-spin"></span><span class="rip-label">Ripping</span>';
  clearHint();
  saveSettings();
  fetch('/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, format, container, subs, outdir })
  }).then(r => r.json()).then(data => {
    resetBtn();
    $('url').value = ''; syncField();
    flashStage();
    addJob(data.id, url, outdir);
    pollJob(data.id);
  }).catch(() => {
    resetBtn();
    flash('Could not start the download');
  });
}
function resetBtn() {
  const btn = $('ripBtn');
  btn.disabled = false;
  btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 11l5 5 5-5M5 21h14"/></svg><span class="rip-label">Rip</span>';
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
    updateStatus();
    if (d.status === 'done' || d.status === 'error') es.close();
  };
  es.onerror = () => { es.close(); if (jobs[id] && jobs[id].status === 'running') { jobs[id].status = 'error'; renderJob(id); updateStatus(); } };
}

/* ---------- Rendering ---------- */
function renderJobs() {
  const ids = Object.keys(jobs);
  $('activityCard').style.display = ids.length ? '' : 'none';
  $('emptyCard').style.display = ids.length ? 'none' : '';
  const list = $('downloadsList');
  list.innerHTML = '';
  ids.slice().reverse().forEach(id => {
    const el = document.createElement('div');
    el.id = 'job-' + id;
    el.className = 'dl';
    list.appendChild(el);
    renderJob(id);
  });
  $('countBadge').textContent = ids.length;
  updateClearBtn();
  updateStatus();
}

function domainOf(u) {
  try { return new URL(u).hostname.replace(/^www\./, ''); } catch (e) { return ''; }
}

function escHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function renderJob(id) {
  const j = jobs[id];
  const el = $('job-' + id);
  if (!el) return;
  const running = j.status === 'running';
  const pct = Math.round(j.progress || 0);
  const fullTitle = j.title || j.url;
  const title = fullTitle.length > 70 ? fullTitle.slice(0, 70) + '…' : fullTitle;
  const src = domainOf(j.url);
  const logId = 'log-' + id;
  const wasOpen = $(logId) && $(logId).style.display === 'block';

  let pill;
  if (j.status === 'done') pill = '<span class="pill pill-done"><span class="dot"></span>Done</span>';
  else if (j.status === 'error') pill = '<span class="pill pill-error"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8v5M12 16h.01"/><circle cx="12" cy="12" r="9"/></svg>Failed</span>';
  else pill = '<span class="pill pill-running"><span class="spinner"></span>Ripping</span>';

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
  } else if (j.status === 'error') {
    actions = `<button class="link-btn" onclick="retryJob('${id}')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.6-6.4M21 4v5h-5"/></svg>
        Retry
      </button>` + actions;
  }

  const canPlay = j.status === 'done' && j.filepath;
  const filmIcon = '<svg class="ph" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18M8 5v14M16 5v14"/></svg>';
  const thumbImg = j.thumbnail
    ? `<img src="${escHtml(j.thumbnail)}" alt="" onerror="this.remove()">`
    : filmIcon;
  const playOverlay = '<span class="play"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span>';
  const thumb = `<div class="thumb ${canPlay ? 'thumb-open' : ''}" ${canPlay ? `onclick="openFile('${id}')" title="Play video"` : ''}>${thumbImg}${canPlay ? playOverlay : ''}</div>`;

  const srcLine = src ? `<div class="dl-src"><span class="src-dot"></span>${escHtml(src)}</div>` : '';

  el.innerHTML = `
    ${thumb}
    <div class="dl-body">
      <div class="dl-top">
        <div style="flex:1;min-width:0">
          <div class="dl-title" title="${escHtml(fullTitle)}">${escHtml(title)}</div>
          ${srcLine}
        </div>
        ${pill}
      </div>
      ${progressHtml}
      <div class="dl-actions">${actions}</div>
      <pre class="log" id="${logId}" style="display:${wasOpen ? 'block' : 'none'}">${escHtml(j.log || '')}</pre>
    </div>
  `;
  if (wasOpen) { const lb = $(logId); lb.scrollTop = lb.scrollHeight; }
  updateClearBtn();
}

function retryJob(id) {
  const j = jobs[id];
  if (!j) return;
  $('url').value = j.url; syncField(); $('url').focus();
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
  const lb = $('log-' + id);
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
  const btn = $('clearBtn');
  if (btn) btn.style.visibility = anyFinished ? 'visible' : 'hidden';
}

/* ---------- Header status ---------- */
function updateStatus() {
  const running = Object.values(jobs).filter(j => j.status === 'running').length;
  const st = $('status'); const txt = $('statusText');
  if (running > 0) { st.classList.add('active'); txt.textContent = running === 1 ? 'Ripping 1' : 'Ripping ' + running; }
  else { st.classList.remove('active'); txt.textContent = 'Ready'; }
}

/* ---------- Hints ---------- */
function flash(msg) {
  const h = $('hint');
  h.classList.add('err');
  h.textContent = msg;
}
function clearHint() {
  const h = $('hint');
  h.classList.remove('err');
  h.innerHTML = '<span class="kbd">Ctrl</span><span class="kbd">V</span> to paste <span class="dot-sep"></span> drag a link in';
}

/* ---------- Clipboard suggestion ---------- */
let dismissedClip = '';
function showClip(url) {
  $('clipUrl').textContent = domainOf(url) || url;
  $('clip').dataset.url = url;
  $('clip').classList.add('show');
}
function hideClip() { $('clip').classList.remove('show'); }
function acceptClip() {
  const url = $('clip').dataset.url;
  if (url) { $('url').value = url; syncField(); $('url').focus(); flashStage(); dismissedClip = url; }
  hideClip();
}
async function checkClipboard() {
  if ($('url').value.trim()) { hideClip(); return; }
  if (!navigator.clipboard || !navigator.clipboard.readText) return;
  try {
    const t = (await navigator.clipboard.readText() || '').trim();
    if (t && t !== dismissedClip && looksLikeUrl(t)) showClip(t);
  } catch (e) { /* permission denied — paste still works */ }
}

/* ---------- Container options ---------- */
const VIDEO_CONTAINERS = [
  { value: 'mp4',  label: 'MP4' }, { value: 'mkv',  label: 'MKV' },
  { value: 'webm', label: 'WebM' }, { value: 'mov',  label: 'MOV' }, { value: 'avi',  label: 'AVI' },
];
const AUDIO_CONTAINERS = [
  { value: 'mp3',  label: 'MP3' }, { value: 'm4a',  label: 'M4A' },
  { value: 'opus', label: 'Opus' }, { value: 'flac', label: 'FLAC' }, { value: 'wav',  label: 'WAV' },
];
function updateContainerOptions() {
  const sel = $('format');
  const isAudio = sel.options[sel.selectedIndex].dataset.audio === '1';
  const list = isAudio ? AUDIO_CONTAINERS : VIDEO_CONTAINERS;
  $('container').innerHTML = list.map(o => `<option value="${o.value}">${o.label}</option>`).join('');
}

/* ---------- Drag & drop (whole window) ---------- */
let dragDepth = 0;
function extractUrl(dt) {
  if (!dt) return '';
  let t = dt.getData('text/uri-list') || dt.getData('text/plain') || '';
  const line = t.split('\n').map(s => s.trim()).filter(s => s && !s.startsWith('#')).find(s => /^https?:\/\//i.test(s));
  return line || t.trim();
}
window.addEventListener('dragenter', e => { e.preventDefault(); dragDepth++; $('stage').classList.add('drag'); });
window.addEventListener('dragover',  e => { e.preventDefault(); if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'; });
window.addEventListener('dragleave', e => { dragDepth--; if (dragDepth <= 0) { dragDepth = 0; $('stage').classList.remove('drag'); } });
window.addEventListener('drop', e => {
  e.preventDefault(); dragDepth = 0; $('stage').classList.remove('drag');
  const t = extractUrl(e.dataTransfer);
  if (t) { $('url').value = t; syncField(); $('url').focus(); flashStage(); hideClip(); }
});

/* ---------- Paste anywhere ---------- */
document.addEventListener('paste', e => {
  if (document.activeElement === $('url')) return; // native paste handles the field
  const t = ((e.clipboardData && e.clipboardData.getData('text')) || '').trim();
  if (t) { $('url').value = t; syncField(); $('url').focus(); flashStage(); hideClip(); e.preventDefault(); }
});

/* ---------- Init ---------- */
$('url').addEventListener('input', syncField);
$('url').addEventListener('keydown', e => {
  if (e.key === 'Enter') startDownload();
  if (e.key === 'Escape') clearUrl();
});
window.addEventListener('focus', checkClipboard);
loadSettings();
syncField();
updateClearBtn();
updateStatus();
$('url').focus();
checkClipboard();
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

    bg = "#0b0c10" if current_theme() == "dark" else "#f4f5f8"
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
