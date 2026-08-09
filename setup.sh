#!/usr/bin/env bash
# Mp3 GHOST - one-command installer & launcher
# Works on Termux (Android) and Linux desktops.
# Usage:  bash setup.sh

set -e

RED="\033[31m"
GREEN="\033[92m"
RESET="\033[0m"

echo -e "${GREEN}"
echo "  Mp3 GHOST installer"
echo -e "${RESET}"

DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$DIR/mp3_ghost.py"

if [ ! -f "$SCRIPT" ]; then
    echo -e "${RED}[!] mp3_ghost.py not found next to setup.sh${RESET}"
    exit 1
fi

detect() {
    if [ -n "$PREFIX" ] && [ -d "$PREFIX" ] && echo "$PREFIX" | grep -qi "termux"; then
        echo "termux"
    else
        echo "linux"
    fi
}

install_termux() {
    echo "[+] Updating packages..."
    pkg update -y
    echo "[+] Installing python, ffmpeg..."
    pkg install -y python ffmpeg
    echo "[+] Installing yt-dlp..."
    pip install -U yt-dlp
}

install_linux() {
    echo "[+] Installing python3, ffmpeg..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip ffmpeg
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip ffmpeg
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Syu --noconfirm python python-pip ffmpeg
    else
        echo -e "${RED}[!] Unsupported package manager. Install python3, pip and ffmpeg manually.${RESET}"
        exit 1
    fi
    echo "[+] Installing yt-dlp..."
    pip install -U --break-system-packages yt-dlp || pip install -U yt-dlp
}

case "$(detect)" in
    termux)
        echo "[*] Detected: Termux (Android)"
        install_termux
        ;;
    *)
        echo "[*] Detected: Linux"
        install_linux
        ;;
esac

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    echo -e "${RED}[!] Python not found after install.${RESET}"
    exit 1
fi

echo
echo -e "${GREEN}[+] Everything is ready! Starting Mp3 GHOST...${RESET}"
echo

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT"
else
    exec python "$SCRIPT"
fi
