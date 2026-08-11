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
  [ YouTube -> MP3 MP4  |  Termux Edition  ]
"""

OUT_DIR = "/storage/emulated/0/Download/MP3 GHOST"


def check_requirements():
    missing = []
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp (pip install yt-dlp)")
    try:
        import mutagen
    except ImportError:
        missing.append("mutagen (pip install mutagen)")
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


def human_size(n):
    if not n or n <= 0:
        return "?"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
        n /= 1024


def estimate_size(fmt, info):
    if not info:
        return 0
    dur = info.get("duration") or 0
    fmts = info.get("formats") or []

    def fsz(f):
        return f.get("filesize") or f.get("filesize_approx") or 0

    def best_audio():
        best = None
        for f in fmts:
            if f.get("acodec") not in (None, "none"):
                if best is None or (f.get("abr") or 0) > (best.get("abr") or 0):
                    best = f
        return best

    def kbps_bytes(kbps):
        return int(dur * kbps * 1000 / 8) if dur else 0

    codec, q = fmt["codec"], fmt["quality"]

    if codec == "mp3":
        kbps = q if q else 192
        a = best_audio()
        if q == 0 and a:
            kbps = a.get("abr") or a.get("tbr") or 192
        return kbps_bytes(kbps)

    if codec == "mp4":
        cands = [f for f in fmts if f.get("height")]
        if q == "best":
            v = max(cands, key=lambda f: f["height"]) if cands else None
        else:
            h = int(q.replace("p", ""))
            sub = [f for f in cands if f["height"] <= h]
            v = max(sub, key=lambda f: f["height"]) if sub else None
        a = best_audio()
        v_sz, a_sz = fsz(v), fsz(a)
        if v_sz or a_sz:
            return (v_sz or 0) + (a_sz or 0)
        vbr = (v.get("tbr") or 0) - (v.get("abr") or 0) if v else 0
        return kbps_bytes(vbr + (a.get("tbr") or 0))

    if codec in ("m4a", "opus"):
        a = best_audio()
        if fsz(a):
            return fsz(a)
        return kbps_bytes(a.get("tbr") or 0)

    if codec == "flac":
        a = best_audio()
        abr = a.get("abr") or a.get("tbr") or 0
        kbps = max(abr * 4, 900) if abr else 900
        return kbps_bytes(kbps)

    return 0


def fetch_info(url):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and info.get("entries"):
                info = info["entries"][0]
            return info
    except Exception:
        return None


def choose_format(info=None):
    formats = [
        ("MP3 - Best quality (VBR)", {"codec": "mp3", "quality": 0}),
        ("MP3 - 320 kbps", {"codec": "mp3", "quality": 320}),
        ("MP3 - 192 kbps", {"codec": "mp3", "quality": 192}),
        ("MP3 - 128 kbps", {"codec": "mp3", "quality": 128}),
        ("MP4 - Best quality", {"codec": "mp4", "quality": "best"}),
        ("MP4 - 720p", {"codec": "mp4", "quality": "720p"}),
        ("MP4 - 480p", {"codec": "mp4", "quality": "480p"}),
        ("M4A - Audio", {"codec": "m4a", "quality": 0}),
        ("OPUS - Audio", {"codec": "opus", "quality": 0}),
        ("FLAC - Lossless", {"codec": "flac", "quality": 0}),
    ]
    total = len(formats)
    print("\n" + RED + "  Available download formats" + RESET)
    for i, (label, f) in enumerate(formats, 1):
        print(f"    {i}) {label}   [~{human_size(estimate_size(f, info))}]")
    print(f"    {total + 1}) Return to URL input")
    while True:
        choice = input(f"  Choose format (1-{total + 1}): ").strip().lower()
        if choice in ("m", "menu", "main"):
            return "menu"
        if choice in ("q", "quit", "exit"):
            print("\n[!] Goodbye.")
            sys.exit(0)
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= total:
                return formats[n - 1][1]
            if n == total + 1:
                return None
        print("    Invalid choice. Try again.")


def download_media(url, out_dir, fmt):
    os.makedirs(out_dir, exist_ok=True)
    codec = fmt["codec"]
    quality = fmt["quality"]

    opts = {
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
    }

    if codec == "mp4":
        if quality == "best":
            opts["format"] = "bestvideo+bestaudio/best"
        else:
            h = quality.replace("p", "")
            opts["format"] = f"bv*[height<={h}]+ba/b[height<={h}]"
        opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = "bestaudio/best"
        opts["writethumbnail"] = True
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
                "preferredquality": quality,
            },
            {"key": "EmbedThumbnail"},
        ]

    print("\n[+] Downloading...")
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
        fmt = {"codec": "mp3", "quality": 0}
        if not download_media(url, OUT_DIR, fmt):
            print("\n[!] Download failed.")
            sys.exit(1)
        print(f"\n[+] Saved to: {OUT_DIR}")
        print("[+] Enjoy your ghost tune!")
        return

    while True:
        choice = run_menu()
        if choice == 2:
            print("\n[!] Goodbye.")
            sys.exit(0)

        while True:
            url = input(RED + "Paste YouTube URL" + RESET + " (type : 'menu' to go back): ").strip()
            if not url:
                continue
            if url.lower() in ("menu", "main", "back"):
                break
            if url.lower() in ("q", "quit", "exit"):
                print("\n[!] Exiting. Goodbye!")
                sys.exit(0)
            print("\n[+] Fetching video info...")
            info = fetch_info(url)
            if info is None:
                print(RED + "  [!] Error: not a valid URL. Try again." + RESET)
                continue
            nav = choose_format(info)
            if nav == "menu":
                break
            if nav is None:
                continue
            if not download_media(url, OUT_DIR, nav):
                print("\n[!] Download failed.")
            else:
                print(f"\n[+] Saved to: {OUT_DIR}")
                print("[+] Enjoy your ghost tune!")
                input("\n  Press Enter to return to the menu...")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Cancelled.")
        sys.exit(130)
