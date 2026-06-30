# Product

## Register

product

## Users

Everyday Windows users who want to save a video or its audio from the web — a music track, a clip, a talk, a playlist item. They arrive with a link already copied, want the file in a known folder, and want to get back to what they were doing. They are not command-line users; "no browser extensions, no command line" is the whole promise.

## Product Purpose

Rippr is a single-window desktop wrapper around yt-dlp + FFmpeg: paste or drop a link, choose quality and format, and it pulls the file down with live progress. Success is the gap between "I have a link" and "the file is in my folder" being as short, legible, and trustworthy as possible — including when a site fails or a download errors.

## Brand Personality

Fast, punchy, a little rebellious — you *rip* media off the web. Confident and direct, never fussy. Three words: **decisive, tactile, unmistakable.** The interface should feel like a purpose-built tool, not a generic utility. Emotional goal: the quiet satisfaction of a capture landing instantly.

## Anti-references

- The generic blue/neutral "downloader app" with a card and a progress bar — the category reflex. Rippr is the opposite: it wears its red identity.
- Adware-style freeware download managers (cluttered, untrustworthy, banner-laden).
- Over-decorated SaaS dashboards: gratuitous gradients-on-text, glassmorphism, hero-metric templates.

## Design Principles

1. **Own the red.** The brand mark is vivid red; the whole product wears it (primary action, focus, progress, running state). Logo and app are one identity, not two color stories.
2. **The capture is the hero.** A big paste/drop "stage" is the centre of gravity; everything else is secondary. The fastest path from link to file wins.
3. **Earned familiarity, expressive edges.** Standard form controls and affordances users already trust, pushed with confident color, motion, and a command-stage layout — distinctive without being strange.
4. **State you can read at a glance.** Every download shows where it is (running / done / failed) with words + icon + color; the header tells you the app's pulse ("Ready" / "Ripping N").
5. **Native and offline-robust.** System fonts, no web-font dependency, full dark/light parity that follows the OS theme. It should feel at home on Windows and never blank-flash waiting on a network.

## Accessibility & Inclusion

- WCAG AA contrast verified for body and UI text in both themes (brand red tuned per theme: `--red-strong` for white-on-red fills, `--red-text` for red text on each background).
- Full `prefers-reduced-motion` path: looping/sweep animations disabled, transitions reduced to near-instant.
- Keyboard: Enter to rip, Esc to clear, paste-anywhere, visible focus rings on all interactive controls.
- Status conveyed by icon + label + color together, never color alone (color-blind safe).
