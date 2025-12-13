import os
import platform
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import requests
import tkinter as tk
import webbrowser
from tkinter import messagebox
from discord_webhook import DiscordWebhook

# Classes to look for
WANTED_CLASSES = [
    ("SSH3201", "3", "C"),
    ("SSH3201", "7", "L"),
    ("SSH3201", "8", "L"),
    ("SSH3501", "4", "C"),
    ("SSH3501", "7", "C"),
    # Added from user request
    #("SIGLE", "NUM_GROUPE", "TYPE (e.g., C for course, L for lab)"),
]

# Options
CHECK_INTERVAL = 300  # Check every 5 minutes (300 seconds)
OPEN_DOSSIER_ETUDIANT = True  # Set to True to open Dossier Etudiant in browser if classes open
DISCORD_WEBHOOK_URL = "" # Discord webhook URL [e.g., https://discord.com/api/webhooks/...](set to empty string "" to disable)
DISCORD_USER_MENTION = ""  # User ID to mention in Discord [e.g., 1234567890] (set to empty string "" to disable)
SOUND_FILE = "vine-boom.wav"  # Custom sound file
TEST_ALERT_ON_START = True  # Set to True to test alert on script startup

# Constants
# URL to download the CSV file
CSV_URL = "https://cours.polymtl.ca/Horaire/public/fermes.csv"
CSV_FILE = "fermes.csv"
URL_DOSSIER_ETUDIANT = "https://dossieretudiant.polymtl.ca/WebEtudiant7/poly.html"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_PATH = os.path.join(SCRIPT_DIR, SOUND_FILE)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
}


def download_csv():
    try:
        response = requests.get(CSV_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        # Save CSV next to the script to avoid CWD issues
        csv_path = Path(SCRIPT_DIR) / CSV_FILE
        with csv_path.open("wb") as file:
            file.write(response.content)
        return True
    except requests.RequestException as e:
        print(f"Error downloading CSV: {e}")
        return False


def check_classes():
    try:
        csv_path = Path(SCRIPT_DIR) / CSV_FILE
        df = pd.read_csv(csv_path, sep=";")
        df.columns = df.columns.str.strip()
        df["Grccod"] = df["Grccod"].astype(str)
        # If a wanted class is NOT listed in "fermes.csv", then it is open.
        open_classes: List[Tuple[str, str, str]] = []
        for cousig, grccod, grccodtypgrpcou in WANTED_CLASSES:
            filtered = df[
                (df["Cousig"] == cousig)
                & (df["Grccod"] == grccod)
                & (df["Grccodtypgrpcou"] == grccodtypgrpcou)
            ]
            if filtered.empty:
                open_classes.append((cousig, grccod, grccodtypgrpcou))

        return open_classes
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def play_sound():
    current_os = platform.system()

    # Check for custom sound file using absolute path (avoids CWD issues)
    if os.path.exists(SOUND_PATH):
        try:
            if current_os == "Windows":
                import winsound

                # Play asynchronously so popup shows while sound plays
                winsound.PlaySound(
                    SOUND_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC
                )
            elif current_os == "Darwin":
                subprocess.run(["afplay", SOUND_PATH])
            else:
                # Linux/Unix support (try aplay first, then paplay)
                try:
                    subprocess.run(["aplay", SOUND_PATH])
                except FileNotFoundError:
                    try:
                        subprocess.run(["paplay", SOUND_PATH])
                    except FileNotFoundError:
                        print("No suitable audio player found (install aplay or paplay)")
            return
        except Exception as e:
            print(f"Error playing custom sound: {e}")

    if current_os == "Windows":
        try:
            import winsound

            # Play a sequence of beeps to ensure it's heard
            for _ in range(3):
                winsound.Beep(1000, 400)
                time.sleep(0.1)
        except Exception as e:
            print(f"Sound error: {e}")
    elif current_os == "Darwin":  # macOS
        try:
            # Play a standard system sound
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"])
        except Exception as e:
            print(f"Sound error: {e}")
    else:
        print("Audio alert not configured for this OS.")

def send_discord_notification(message: str):
    try:
        content = message + "\n\n" + URL_DOSSIER_ETUDIANT
        allowed_mentions = {}
        if DISCORD_USER_MENTION:
            content = f"<@{DISCORD_USER_MENTION}>\n" + message
            allowed_mentions = {
                "users": [DISCORD_USER_MENTION],
            }
        webhook = DiscordWebhook(
            url=DISCORD_WEBHOOK_URL,
            content=content,
            username="Class Notifier",
            allowed_mentions=allowed_mentions,
        )
        webhook.execute()
    except Exception as e:
        print(f"Discord webhook error: {e}")

def open_dossier_etudiant():
    try:
        webbrowser.open(URL_DOSSIER_ETUDIANT)
    except Exception as e:
        print(f"Error opening Dossier Etudiant: {e}")

def alert_user(missing_classes):

    # Build the list of open classes
    open_classes_list = []
    for cousig, grccod, grccodtypgrpcou in missing_classes:
        class_name = f"{cousig} - {grccod} ({grccodtypgrpcou})"
        open_classes_list.append(class_name)
        print(f"\033[92mClass {class_name} is now open!\033[0m")

    # Create the summary message
    message = "The following classes are now open:\n\n" + "\n".join(open_classes_list)

    # Play sound in a separate thread so it plays immediately (once)
    threading.Thread(target=play_sound, daemon=True).start()
    # Send Discord notification if webhook URL is set
    if DISCORD_WEBHOOK_URL:
        send_discord_notification(message)

    # Open the default web browser to Dossier Etudiant if enabled
    if OPEN_DOSSIER_ETUDIANT:
        open_dossier_etudiant()

    # 1. Show a single message box (Cross-platform via Tkinter)
    try:
        # Create a hidden root window so the messagebox appears correctly
        root = tk.Tk()
        root.withdraw()
        # Make sure the window stays on top
        root.attributes("-topmost", True)

        # On Mac, the window might need to be updated to take focus
        if platform.system() == "Darwin":
            root.update()

        messagebox.showinfo("Classes Open!", message, icon="info")
        root.destroy()
    except Exception as e:
        print(f"Popup error: {e}")


def main():
    print("Starting schedule checker (Ctrl+C to stop).")

    if TEST_ALERT_ON_START:
        print("Testing alert on startup...")
        alert_user([("TEST", "0", "X")])

    try:
        while True:
            print("Checking for updates...")
            if not download_csv():
                print("Skipping check due to download error.")
            else:
                open_classes = check_classes()
                if open_classes:
                    alert_user(open_classes)
                else:
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    print(f"\033[91m[{current_time}] None of the classes are open yet.\033[0m")

            print(f"Waiting for {CHECK_INTERVAL} seconds before next check...\n")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Schedule checker stopped by user.")


if __name__ == "__main__":
    main()
