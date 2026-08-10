#!/usr/bin/env python3
# Mp3 GHOST - YouTube to MP3 downloader for Termux (Android)
# Requirements: pip install yt-dlp ffmpeg-python   (pkg install ffmpeg)

import os
import sys
import shutil
import termios
import tty

import yt_dlp

GREEN = "\033[92m"
RED = "\033[31m"
RESET = "\033[0m"

BANNER = GREEN + r"""
    __  _______ _____    ________  ______  ___________
   /  |/  / __ \__  /   / ____/ / / / __ \/ ___/_  __/
  / /|_/ / /_/ //_ <   / / __/ /_/ / / / /\__ \ / /   
 / /  / / ____/__/ /  / /_/ / __  / /_/ /___/ // /    
/_/  /_/_/   /____/   \____/_/ /_/\____//____//_/     
""" + RESET + RED + "by crypt-1sx" + RESET + "\n" + r"""
  [ YouTube -> MP3  |  Termux Edition  ]
"""

OUT_DIR = "/storage/emulated/0/Download/Seal/Audio"


def check_requirements():
    missing = []
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp (pip install yt-dlp)")
    if missing:
        print("[!] Missing dependencies: " + ", ".join(missing))
        print("    Run: pkg install ffmpeg  &&  pip install yt-dlp")
        return False
    return True


def progress_hook(d):
    if d.get("status") == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        done = d.get("downloaded_bytes", 0)
        pct = (done / total * 100) if total else 0
        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r  {bar} {pct:5.1f}%")
        sys.stdout.flush()
    elif d.get("status") == "finished":
        sys.stdout.write("\r" + " " * 44 + "\r")
        sys.stdout.flush()


def choose_format():
    options = [
        ("Best quality (VBR)", 0),
        ("High quality (320 kbps)", 320),
        ("Medium quality (192 kbps)", 192),
        ("Low quality (128 kbps)", 128),
    ]
    print("\n" + RED + "  Available download formats" + RESET)
    for i, (label, _) in enumerate(options, 1):
        print(f"    {i}) {label}")
    while True:
        choice = input("  Choose format (1-4): ").strip()
        if choice in ("1", "2", "3", "4"):
            return options[int(choice) - 1][1]
        print("    Invalid choice. Pick a number from 1 to 4.")


def download_mp3(url, out_dir, quality=0):
    os.makedirs(out_dir, exist_ok=True)
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            },
            {"key": "EmbedThumbnail"},
        ],
        "writethumbnail": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
    }
    print("\n[+] Fetching video info...")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"\n[!] Error: {e}")
        return False


def read_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            if seq == "[A":
                return "up"
            if seq == "[B":
                return "down"
            if seq == "[C":
                return "right"
            if seq == "[D":
                return "left"
            return "esc"
        if ch in ("\r", "\n"):
            return "enter"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def edit_download_dir():
    global OUT_DIR
    print(RED + "  Download Directory" + RESET)
    print("  Current path: " + OUT_DIR)
    new = input("  New path (Enter to keep): ").strip()
    if new:
        OUT_DIR = new
        print(GREEN + "  [i] Updated to: " + OUT_DIR + RESET)
    else:
        print(GREEN + "  [i] Keeping: " + OUT_DIR + RESET)


def run_menu():
    items = ["Paste YouTube URL", "Download Directory", "Quit"]
    sel = 0
    hint = "  Use \u2191/\u2193 to choose, Enter to select"

    def render():
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(BANNER)
        sys.stdout.write("\n")
        for i, item in enumerate(items):
            marker = "> " if i == sel else "  "
            sys.stdout.write(marker + item + "\n")
        sys.stdout.write(hint)
        sys.stdout.flush()

    render()
    try:
        while True:
            key = read_key()
            if key == "up":
                sel = (sel - 1) % len(items)
                render()
            elif key == "down":
                sel = (sel + 1) % len(items)
                render()
            elif key == "enter":
                if sel == 1:
                    sys.stdout.write("\r\033[K\n")
                    sys.stdout.flush()
                    edit_download_dir()
                    render()
                else:
                    break
            elif key in ("q", "Q", "esc"):
                sel = len(items) - 1
                break
    except Exception:
        sys.stdout.write("\n")
        sys.stdout.flush()
        if sys.stdin.isatty():
            while True:
                choice = input("  1) Paste URL   2) Download Directory   3) Quit : ").strip()
                if choice in ("3", "q", "quit", "exit"):
                    return len(items) - 1
                if choice == "2":
                    edit_download_dir()
                else:
                    return 0

    sys.stdout.write("\r\033[K\n")
    sys.stdout.flush()
    return sel


def main():
    if not check_requirements():
        sys.exit(1)

    if len(sys.argv) > 1:
        print(BANNER)
        url = sys.argv[1]
        quality = 0
    else:
        choice = run_menu()
        if choice == 2:
            print("\n[!] Goodbye.")
            sys.exit(0)
        url = input(RED + "Paste YouTube URL: " + RESET).strip()
        if not url:
            print("[!] No URL provided.")
            sys.exit(1)
        if url.lower() in ("q", "quit", "exit"):
            print("\n[!] Exiting. Goodbye!")
            sys.exit(0)
        quality = choose_format()

    if not download_mp3(url, OUT_DIR, quality):
        print("\n[!] Download failed.")
        sys.exit(1)

    print(f"\n[+] Saved to: {OUT_DIR}")
    print("[+] Enjoy your ghost tune!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Cancelled.")
        sys.exit(130)
