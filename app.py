"""
ContrastCraft — Automated Web Accessibility Contrast Auditor
Application Entry Point.
"""

from __future__ import annotations
import os
import sys
import webbrowser
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app

__version__ = "1.0.0"


def main():
    if "--version" in sys.argv:
        print(f"ContrastCraft v{__version__}")
        sys.exit(0)

    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    url = f"http://{host}:{port}"
    print("=" * 70)
    print("  ContrastCraft — Automated Web Accessibility Contrast Auditor")
    print(f"  Version: {__version__} • WCAG 2.1 / 2.2 Level AA & AAA")
    print("=" * 70)
    print(f"\n  Web Application:  {url}")
    print(f"  API Documentation: {url}/docs")
    print(f"  Health Check:      {url}/api/health")
    print("\n  Press CTRL+C in this terminal to stop the application.\n")

    # Optionally open browser if --open flag passed
    if "--open" in sys.argv:
        webbrowser.open(url)

    uvicorn.run("backend.app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
