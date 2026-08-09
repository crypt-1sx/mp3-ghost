# Mp3 GHOST

> YouTube to MP3 downloader for **Termux (Android)** and Linux.

```
    __  _______ _____    ________  ______  ___________
   /  |/  / __ \__  /   / ____/ / / / __ \/ ___/_  __/
  / /|_/ / /_/ //_ <   / / __/ /_/ / / / /\__ \ / /   
 / /  / / ____/__/ /  / /_/ / __  / /_/ /___/ // /    
/_/  /_/_/   /____/   \____/_/ /_/\____//____//_/     
```
*by islem*

---

## Features

- Clean interactive menu (↑/↓ to navigate, Enter to select)
- Paste a YouTube URL and download it as **high-quality MP3**
- Embedded thumbnail & metadata
- **Changeable download directory** from the menu
- No manual dependency setup — **one command** installs and runs everything

## Requirements

Nothing to install manually. The installer handles Python, `yt-dlp` and `ffmpeg` for you.

## Install & Run

You only need to run **one thing**.

### On Termux (Android)

```bash
pkg install -y git
git clone https://github.com/crypt-1sx/mp3-ghost.git
cd mp3-ghost
bash setup.sh
```

### On Linux

```bash
git clone https://github.com/crypt-1sx/mp3-ghost.git
cd mp3-ghost
bash setup.sh
```

The installer auto-detects your system, installs everything, and launches the script.

## Usage

1. Pick **Paste YouTube URL** and press Enter
2. Type/paste the video URL and press Enter
3. Wait for the download — the MP3 is saved to the download directory

> Default download directory: `/storage/emulated/0/Download/Seal/Audio`
>
> Change it anytime from the menu → **Download Directory**.

### Options

| Option              | What it does                                   |
| ------------------- | ---------------------------------------------- |
| Paste YouTube URL   | Download a video as MP3                        |
| Download Directory  | Show / change where songs are saved            |
| Quit                | Exit the script                                |

## Direct URL (fast)

You can also pass a URL straight from the command line:

```bash
python3 mp3_ghost.py "https://www.youtube.com/watch?v=..."
```

## Notes

- Termux storage access: run `termux-setup-storage` once if the script can't write to your chosen folder.
- MP3 conversion requires `ffmpeg` — installed automatically.
