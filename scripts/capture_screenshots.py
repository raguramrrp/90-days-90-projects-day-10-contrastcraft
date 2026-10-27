"""
ContrastCraft — Screenshot Capture Utility
Uses headless Chrome with direct file:// URLs and client-side data engine
to capture high-resolution screenshots for documentation and portfolio showcasing.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"


def main():
    if not os.path.exists(CHROME_PATH):
        print(f"Chrome not found at {CHROME_PATH}")
        return

    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    temp_profile = Path(tempfile.mkdtemp(prefix="cc_chrome_"))

    index_html = PROJECT_ROOT / "frontend" / "index.html"
    base_file_url = f"file:///{str(index_html.resolve()).replace('\\', '/')}"

    screens = [
        ("dashboard.png", f"{base_file_url}#workspace"),
        ("playground.png", f"{base_file_url}#playground"),
        ("findings.png", f"{base_file_url}#findings"),
        ("fix_studio.png", f"{base_file_url}#fix-studio"),
        ("tokens.png", f"{base_file_url}#tokens"),
        ("html_a11y.png", f"{base_file_url}#html-a11y"),
    ]

    for filename, url in screens:
        out_file = SCREENSHOTS_DIR / filename
        print(f"Capturing {filename} from {url}...")
        cmd = [
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--window-size=1400,900",
            f"--user-data-dir={temp_profile}",
            "--virtual-time-budget=2500",
            f"--screenshot={str(out_file.resolve())}",
            url
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if out_file.exists() and out_file.stat().st_size > 0:
                print(f"  [OK] Saved {filename} ({out_file.stat().st_size} bytes)")
            else:
                print(f"  [WARN] File not created. Exit code: {res.returncode}, Stderr: {res.stderr[:200]}")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")

    # Clean up temp profile
    shutil.rmtree(temp_profile, ignore_errors=True)
    print("\nScreenshot capture process completed.")


if __name__ == "__main__":
    main()
