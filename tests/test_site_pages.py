"""Generic browser checks for a site's public pages and internal links.

This suite contains no site-specific data. Page names/paths, the base
URL, and authentication are all read from ``test_config.py`` so the same
suite can be reused for other web sites by editing that config file only.
"""

import os
from urllib.parse import urljoin, urlparse

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

import test_config as config

REQUESTED_PAGES = tuple(
    page.strip().lower()
    for page in os.getenv("PAGE_SELECTION", "all").split(",")
    if page.strip()
)


def selected_pages() -> tuple[str, ...]:
    """Return the requested, valid page names from the runner environment."""
    if not REQUESTED_PAGES or "all" in REQUESTED_PAGES:
        return config.DEFAULT_PAGES

    unknown_pages = set(REQUESTED_PAGES) - set(config.PAGE_PATHS)
    if unknown_pages:
        pytest.fail(f"Unknown page selection: {', '.join(sorted(unknown_pages))}")

    return REQUESTED_PAGES


@pytest.fixture(scope="session")
def browser() -> Browser:
    headless = os.getenv("HEADLESS", "true").strip().lower() not in {"0", "false", "no"}
    # Optional: set PLAYWRIGHT_CHANNEL=chrome/msedge to drive a system-installed
    # browser instead of Playwright's bundled Chromium (useful when the
    # bundled browser download is unavailable, e.g. offline/sandboxed hosts).
    channel = os.getenv("PLAYWRIGHT_CHANNEL", "").strip() or None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless, channel=channel)
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser) -> Page:
    context: BrowserContext = browser.new_context(
        http_credentials=config.get_http_credentials()
    )
    browser_page = context.new_page()
    yield browser_page
    browser_page.close()
    context.close()


@pytest.mark.parametrize("topic", selected_pages())
def test_public_page_loads(page: Page, topic: str) -> None:
    """Each requested page must return a successful HTML page."""
    response = page.goto(
        f"{config.BASE_URL}{config.PAGE_PATHS[topic]}", wait_until="networkidle"
    )

    assert response is not None, f"No response received for {topic}."
    assert response.status < 400, f"{topic} returned HTTP {response.status}."
    assert page.title().strip(), f"{topic} does not have a page title."


@pytest.mark.parametrize("topic", selected_pages())
def test_public_page_has_no_broken_internal_links(page: Page, topic: str) -> None:
    """Every same-site HTTP link on a requested page must resolve successfully."""
    page_url = f"{config.BASE_URL}{config.PAGE_PATHS[topic]}"
    response = page.goto(page_url, wait_until="networkidle")
    assert response is not None and response.status < 400, f"Could not load {topic}."

    internal_links = page.locator("a[href]").evaluate_all(
        """anchors => anchors.map(anchor => anchor.href)"""
    )
    base_host = urlparse(config.BASE_URL).netloc
    broken_links: list[str] = []

    for href in sorted(set(internal_links)):
        parsed = urlparse(urljoin(page_url, href))
        if parsed.scheme not in {"http", "https"} or parsed.netloc != base_host:
            continue

        link_response = page.request.get(href, max_redirects=10)
        if link_response.status >= 400:
            broken_links.append(f"{href} (HTTP {link_response.status})")

    assert not broken_links, (
        f"Broken internal link(s) found on {topic}: " + "; ".join(broken_links)
    )
