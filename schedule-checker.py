import requests
import pandas as pd
import time
import os
import subprocess
import platform
import threading
from tkinter import messagebox
import tkinter as tk

# URL to download the CSV file
CSV_URL = "https://cours.polymtl.ca/Horaire/public/fermes.csv"
CSV_FILE = "fermes.csv"
SOUND_FILE = "vine-boom.wav"  # Custom sound file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_PATH = os.path.join(SCRIPT_DIR, SOUND_FILE)
CHECK_INTERVAL = 300 / 2  # Check every 5 minutes (300 seconds)

# Classes to look for
WANTED_CLASSES = [
    ("SSH3201", "3", "C"),
    ("SSH3201", "7", "L"),
    ("SSH3201", "8", "L"),
    ("SSH3501", "4", "C"),
    ("SSH3501", "7", "C"),
    # Added from user request
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def download_csv():
    try:
        response = requests.get(CSV_URL, headers=HEADERS)
        response.raise_for_status()
        with open(CSV_FILE, "wb") as file:
            file.write(response.content)
        return True
    except requests.RequestException as e:
        print(f"Error downloading CSV: {e}")
        return False


def check_classes():
    try:
        df = pd.read_csv(CSV_FILE, sep=";")
        df.columns = df.columns.str.strip()
        df["Grccod"] = df["Grccod"].astype(str)

        missing_classes = []

        for cousig, grccod, grccodtypgrpcou in WANTED_CLASSES:
            filtered = df[
                (df["Cousig"] == cousig)
                & (df["Grccod"] == grccod)
                & (df["Grccodtypgrpcou"] == grccodtypgrpcou)
            ]
            if filtered.empty:
                missing_classes.append((cousig, grccod, grccodtypgrpcou))

        return missing_classes
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []


def alert_user(missing_classes):
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
                            print(
                                "No suitable audio player found (install aplay or paplay)"
                            )
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
    # alert_user([("TEST", "TEST", "TEST")])  # Uncomment to test alerts on startup

    while True:
        print("Checking for updates...")
        if not download_csv():
            print("Skipping check due to download error.")
        else:
            missing_classes = check_classes()
            if missing_classes:
                alert_user(missing_classes)
            else:
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(
                    f"\033[91m[{current_time}] None of the classes are open yet.\033[0m"
                )

        print(f"Waiting for {CHECK_INTERVAL // 60} minutes before next check...\n")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
