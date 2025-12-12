# Class Schedule Checker

This script monitors the availability of specific classes at Polytechnique Montréal. It checks for updates every 5 minutes and alerts you with a popup and sound when a class becomes open.

## Features

- **Cross-Platform:** Works on Windows, macOS, and Linux.
- **Audio Alerts:** Uses system text-to-speech to announce open classes.
- **Visual Alerts:** Displays a popup window on top of other applications.

## Prerequisites

- [Python 3.x](https://www.python.org/downloads/) installed on your system.

## Installation

1.  **Download or Clone** this repository.
2.  Open a terminal or command prompt in the project folder.
3.  Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

    _Note for Linux users:_ You may need to install Tkinter separately (e.g., `sudo apt-get install python3-tk`).

## Configuration

Open `schedule-checker.py` and modify the `WANTED_CLASSES` list to include the classes you want to monitor.

```python
# Format: ("Course Code", "Group", "Type")
WANTED_CLASSES = [
    ("SSH3201", "3", "C"),
    ("SSH3201", "7", "L"),
]
```

## Usage

Run the script from your terminal:

```bash
python schedule-checker.py
```

The script will run continuously. To stop it, press `Ctrl+C` in the terminal.

## Developers
Made by [@Nilon123456789](https://github.com/nilon123456789)

Improved by [@XaJason](https://github.com/xajason)
