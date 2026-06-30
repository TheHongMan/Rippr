# Design

Visual system for Rippr. Single embedded surface in `app.py` (`HTML` string), rendered in pywebview (Edge WebView2 / Chromium). Theme follows the Windows app theme on launch and is overridable via the in-app toggle (persisted to `localStorage` as `rippr-theme`).

## Theme

Cinematic, dark-first product tool that **owns its brand red**. Deep near-black surfaces with a faint red ambient glow at the top of the viewport; the Rippr red carries every primary action, focus, progress, and running state. Light theme is a full-parity neutral near-white (not cream), with the same red as the accent. Strategy: **Committed** — one saturated color carries identity across the surface, on a restrained neutral base.

## Color

Tokens are CSS custom properties scoped to `:root, [data-theme="light"]` and `[data-theme="dark"]`. Brand hex is preserved from the logo (`#fd1b24`); a tuned darker red (`#ea0f18`) is used for white-text fills to pass AA.

### Dark (default)
- `--bg` `#0b0c10` · `--surface` `#14161c` · `--surface-2` `#1b1e26` · `--surface-3` `#232732`
- `--text` `#f3f4f7` · `--text-secondary` `#aab0bb` · `--text-muted` `#8b919c`
- `--red` `#fd1b24` (glow / progress / logo) · `--red-strong` `#ea0f18` (button fills) · `--red-hover` `#ff3d44`
- `--red-text` `#ff7066` (red text/links, AA on dark) · `--red-soft` `rgba(253,27,36,.16)` · `--red-line` `rgba(253,27,36,.42)`
- Status: success `#5fd99a`/`#11271a` · danger `#ff9a93`/`#311316`

### Light
- `--bg` `#f4f5f8` · `--surface` `#ffffff` · `--surface-2` `#eef0f4`
- `--text` `#14161b` · `--text-secondary` `#4b515b` · `--text-muted` `#6b727d`
- `--red` `#fd1b24` · `--red-strong` `#ea0f18` · `--red-text` `#c8101b` (AA on white) · `--red-soft` `rgba(253,27,36,.10)`

### Contrast (verified WCAG)
- Body/secondary/muted text ≥ 4.5:1 on their surfaces in both themes.
- White on `--red-strong` = 4.59:1 (passes normal-text AA); `--red-text` ≥ 4.7:1 on every background it appears on.

## Typography

One family — the native Windows UI stack: `"Segoe UI Variable Display", "Segoe UI Variable", "Segoe UI", system-ui, sans-serif`. Monospace (`Cascadia Code`/`Consolas`) only for the per-download log and progress stats (tabular numerals). Fixed px/rem scale, not fluid.

- Wordmark "Rippr" 19px/700, last letter in `--red-text`.
- Capture input 16.5px/500. Rip button 16px/700. Section headings 13–16px/700.
- Labels 11px/600 uppercase, tracking `.04em`. Body/meta 12–13px. Download title 14.5px/600.

## Components

- **Capture stage** — large rounded `.console` card; top `.stage` holds the link `.field` (56px, leading link icon, clear button) + the red `.rip-btn`; red focus-within ring + ambient `.stage-glow`; whole window is a drop target with a dashed `.drop-veil` ("Drop to rip"); clipboard chip suggests a detected link.
- **Controls bar** — connected below the stage by a hairline: Quality / Format custom-styled `select`s, Subtitles pill `switch` (red when on), Save-to row with folder picker. Choices persist to `localStorage`.
- **Status pill** (header) — `Ready` / `Ripping N` with a red pulsing LED when active.
- **Activity feed** — `.dl` rows: 16:9 thumbnail (play overlay when done), title + source domain, state pill (`Ripping` spinner / `Done` green / `Failed` alert-icon), red gradient progress bar with sheen, contextual actions (Show in folder / Retry / Show log).
- **Empty state** — teaching: red download glyph, "Ready when you are", paste/drag hint chips, and a "Works with" site row.

States covered per control: default, hover, focus-visible, active, disabled, loading. Semantic z-index scale (`--z-base → --z-toast`).

## Layout

Single centered column, `max-width: 660px`, body padding `20px 22px 34px`. Responsive is structural, not fluid type: controls `flex-wrap`, `repeat`-free; below 520px the Rip button collapses to icon-only and `.control.grow` stacks full-width. Verified down to the 540px minimum window with no overflow (long titles ellipsis-truncate).

## Motion

150–340ms, ease-out (`cubic-bezier(.16,1,.3,1)`). State-conveying only: focus glow, drag-over scale + glow, `flashStage` rip pulse on start, staggered row `rise`, progress sweep, running LED ping. Full `prefers-reduced-motion: reduce` alternative disables loops/sweeps and collapses transitions.
