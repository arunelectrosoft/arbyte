"""Capture permanent desktop/mobile visual snapshots in tests/reports.

Run this while the Jekyll server is available at ``BASE_URL`` (defaults to
http://127.0.0.1:4000). Existing snapshots are replaced on every run.
"""

import os
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:4000").rstrip("/") + "/"
OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
PAGES = {"visual": "", "courses": "courses/", "contact": "contact/ContactUs.html"}
VIEWPORTS = {"desktop": (1440, 1000), "mobile": (390, 844)}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for viewport_name, (width, height) in VIEWPORTS.items():
                page = browser.new_page(viewport={"width": width, "height": height})
                try:
                    for page_name, page_path in PAGES.items():
                        url = urljoin(BASE_URL, page_path)
                        response = page.goto(url, wait_until="networkidle")
                        if response is None or response.status >= 400:
                            status = "no response" if response is None else response.status
                            raise RuntimeError(f"Could not capture {url}: HTTP {status}")

                        target = OUTPUT_DIR / f"{page_name}-{viewport_name}.png"
                        page.screenshot(path=target, full_page=True)
                        print(f"Saved {target}")
                finally:
                    page.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
