# Rippr

A clean, minimal desktop app for downloading video and audio from YouTube and thousands of other sites. Paste a link, pick your quality and format, and download. No browser extensions, no command line.

Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [pywebview](https://pywebview.flowrl.com/).

---



## Features

- Download video in **MP4, MKV, WebM, MOV, AVI** at up to best available quality (up to 1080p selectable)
- Extract **audio-only** in MP3, M4A, Opus, FLAC, or WAV
- **Subtitle download** toggle (auto-fetches English subs where available)
- Custom **save folder** with folder-picker dialog
- Real-time **progress bar** with speed, ETA, and log output
- Click a completed download to **open the file or reveal it in Explorer**
- **Dark and light mode**: auto-detects your Windows theme, toggle anytime
- Single `.exe`: no Python or dependencies required

## Download

Grab the latest `Rippr.exe` from the [Releases](https://github.com/TheHongMan/Rippr/releases) page. Double-click to run, no installation needed.

## Supported Sites

Anywhere yt-dlp works: YouTube, Twitter/X, Instagram, TikTok, Reddit, Vimeo, SoundCloud, and [thousands more](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

## Building from Source

**Requirements:** Python 3.11+, [FFmpeg](https://ffmpeg.org/download.html) on PATH

```bash
pip install flask yt-dlp pywebview pyinstaller
pyinstaller Rippr.spec
```

The executable will be output to `dist/Rippr.exe`.

## License

MIT
