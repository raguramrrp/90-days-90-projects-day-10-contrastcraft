"""
ContrastCraft — Screenshot Capture Utility
Starts local server in a daemon thread and uses headless Chrome to capture UI screenshots.
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from backend.app.main import app

PORT = 8035
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"


def start_server():
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


def main():
    if not os.path.exists(CHROME_PATH):
        print(f"Chrome not found at {CHROME_PATH}")
        return

    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    print("Starting background server on port", PORT)
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(3)

    url = f"http://127.0.0.1:{PORT}/"
    output_png = SCREENSHOTS_DIR / "dashboard.png"

    print(f"Capturing dashboard to {output_png}...")
    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1280,850",
        f"--screenshot={output_png}",
        url
    ]
    subprocess.run(cmd, check=True)

    if output_png.exists():
        print(f"[OK] Dashboard screenshot captured ({output_png.stat().st_size} bytes)")
    else:
        print("[FAIL] Dashboard screenshot was not generated.")


if __name__ == "__main__":
    main()
