"""Small, fast browser smoke tests for the public Arbyte site.

The detailed regression suite remains in test_site_pages.py. This module keeps
routine local checks intentionally compact: one browser, one pass over the
public pages, and focused checks for layout, links, Mermaid, and security.
"""

from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

import test_config as config


def test_public_site_smoke_checks() -> None:
    """Public pages load, remain within the viewport, and have valid local links."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        try:
            checked_links: set[str] = set()
            for name, path in config.PAGE_PATHS.items():
                page_url = f"{config.BASE_URL}{path}"
                response = page.goto(page_url, wait_until="networkidle")
                assert response is not None, f"No response received for {name}."
                assert response.status < 400, f"{name} returned HTTP {response.status}."
                assert page.title().strip(), f"{name} has no document title."

                overflow = page.evaluate(
                    "document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
                )
                assert not overflow, f"{name} has horizontal page overflow."

                for href in page.locator("a[href]").evaluate_all(
                    "anchors => anchors.map(anchor => anchor.href)"
                ):
                    parsed = urlparse(urljoin(page_url, href))
                    if (
                        parsed.scheme not in {"http", "https"}
                        or parsed.netloc != urlparse(config.BASE_URL).netloc
                    ):
                        continue
                    target = parsed._replace(fragment="").geturl()
                    if target in checked_links:
                        continue
                    checked_links.add(target)
                    link_response = page.request.get(target, max_redirects=10)
                    assert link_response.status < 400, (
                        f"Broken internal link on {name}: {target} "
                        f"(HTTP {link_response.status})"
                    )
        finally:
            page.close()
            browser.close()


def test_homepage_components_and_security() -> None:
    """Core UI renders and common client-side security rules remain enabled."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        try:
            response = page.goto(f"{config.BASE_URL}/index.html", wait_until="networkidle")
            assert response is not None and response.status < 400

            assert page.locator("footer.site-footer").count() == 1
            assert page.locator(".course-card").count() > 0

            diagrams = page.locator(".mermaid")
            assert diagrams.count() > 0
            for index in range(diagrams.count()):
                diagrams.nth(index).locator("svg").wait_for(state="visible")

            for index in range(page.locator('a[target="_blank"]').count()):
                link = page.locator('a[target="_blank"]').nth(index)
                rel = set((link.get_attribute("rel") or "").split())
                assert {"noopener", "noreferrer"}.issubset(rel)

            script_sources = page.locator("script[src]").evaluate_all(
                "scripts => scripts.map(script => script.src)"
            )
            assert not any(
                "googletagmanager" in source or "googlesyndication" in source
                for source in script_sources
            )
        finally:
            page.close()
            browser.close()
