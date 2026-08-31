"""Generic browser checks for a site's public pages and internal links.

This suite contains no site-specific data. Page names/paths, the base
URL, and authentication are all read from ``test_config.py`` so the same
suite can be reused for other web sites by editing that config file only.
"""

import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

import test_config as config

REQUESTED_PAGES = tuple(
    page.strip().lower()
    for page in os.getenv("PAGE_SELECTION", "all").split(",")
    if page.strip()
)

# Markdown descriptions live here; if a live page has a missing/broken image,
# the failure message points here so it can be (re)generated with
# assets/py_scripts/generate_images_from_markdown.py.
IMAGE_DESC_DIR = Path(__file__).resolve().parents[1] / "assets" / "image_desc"


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


@pytest.mark.parametrize("topic", selected_pages())
def test_public_page_has_no_missing_images(page: Page, topic: str) -> None:
    """Every <img> on a requested page must resolve over HTTP and decode to
    a non-empty image (catches both 404s and images that fail to render/
    generate during loading). If one is missing, the assertion message
    points at the Markdown description folder used to (re)generate it.
    """
    page_url = f"{config.BASE_URL}{config.PAGE_PATHS[topic]}"
    response = page.goto(page_url, wait_until="networkidle")
    assert response is not None and response.status < 400, f"Could not load {topic}."

    images = page.locator("img[src]").evaluate_all(
        """imgs => imgs.map(img => ({
            src: img.currentSrc || img.src,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
        }))"""
    )

    missing: list[str] = []
    for image in images:
        src = image["src"]
        if not src:
            continue

        image_response = page.request.get(src, max_redirects=10)
        broken = (
            image_response.status >= 400
            or image["naturalWidth"] == 0
            or image["naturalHeight"] == 0
        )
        if not broken:
            continue

        stem = Path(urlparse(src).path).stem
        desc_path = IMAGE_DESC_DIR / f"{stem}.md"
        hint = (
            f"a description exists at {desc_path}; run "
            "'python assets/py_scripts/generate_images_from_markdown.py' to generate it"
            if desc_path.exists()
            else f"add a description at {desc_path} so it can be generated"
        )
        missing.append(f"{src} (HTTP {image_response.status}) - {hint}")

    assert not missing, f"Missing/broken image(s) on {topic}: " + "; ".join(missing)


@pytest.mark.parametrize("topic", selected_pages())
def test_mermaid_diagrams_render_in_bounded_frames(page: Page, topic: str) -> None:
    """Mermaid sources must render to SVG and stay within their frame width."""
    page_url = f"{config.BASE_URL}{config.PAGE_PATHS[topic]}"
    response = page.goto(page_url, wait_until="networkidle")
    assert response is not None and response.status < 400, f"Could not load {topic}."

    diagrams = page.locator(".mermaid")
    for index in range(diagrams.count()):
        diagram = diagrams.nth(index)
        diagram.locator("svg").wait_for(state="visible")
        source = diagram.get_attribute("data-mermaid-source") or ""
        if source.lstrip().lower().startswith(("graph ", "flowchart ")):
            directive = source.lstrip().splitlines()[0].upper()
            assert directive.endswith((" TD", " TB")), (
                f"Non-top-down Mermaid source on {topic}: {directive}"
            )

        dimensions = diagram.evaluate(
            """element => ({
                diagramWidth: element.getBoundingClientRect().width,
                parentWidth: element.parentElement.getBoundingClientRect().width,
            })"""
        )
        assert dimensions["diagramWidth"] <= dimensions["parentWidth"] + 1, (
            f"Mermaid diagram overflows its container on {topic}."
        )


@pytest.mark.parametrize("topic", ("courses", "demos", "contact"))
def test_missing_diagrams_use_white_card_placeholders(page: Page, topic: str) -> None:
    """Collection items without an image diagram retain a clean white frame."""
    page_url = f"{config.BASE_URL}{config.PAGE_PATHS[topic]}"
    response = page.goto(page_url, wait_until="networkidle")
    assert response is not None and response.status < 400, f"Could not load {topic}."

    placeholders = page.locator(".listing-card .diagram-placeholder")
    assert placeholders.count() > 0, f"Expected at least one placeholder on {topic}."
    for index in range(placeholders.count()):
        background = placeholders.nth(index).evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
        assert background in {"rgb(255, 255, 255)", "rgba(0, 0, 0, 0)"}


def test_contact_page_has_locations_socials_and_training_preview(page: Page) -> None:
    """The Contact detail page exposes all requested location and channel cards."""
    response = page.goto(
        f"{config.BASE_URL}/contact/ContactUs.html", wait_until="networkidle"
    )
    assert response is not None and response.status < 400

    content = page.locator("main").inner_text()
    for expected in (
        "India",
        "Tamil Nadu",
        "Coimbatore",
        "GitHub",
        "LinkedIn",
        "Instagram",
        "YouTube",
        "Discord",
        "Facebook",
        "X",
    ):
        assert expected in content

    preview_url = "https://github.com/arunelectrosoft/arbyte-training-preview"
    assert page.locator(f'a[href="{preview_url}"]').count() == 1


def test_courses_link_to_training_preview(page: Page) -> None:
    """Every course listing card offers the shared GitHub course preview."""
    response = page.goto(f"{config.BASE_URL}/courses/", wait_until="networkidle")
    assert response is not None and response.status < 400

    course_cards = page.locator(".listing-card")
    preview_links = course_cards.locator(
        'a[href="https://github.com/arunelectrosoft/arbyte-training-preview"]'
    )
    assert preview_links.count() == course_cards.count()


def test_footer_is_semantic_and_has_clear_navigation(page: Page) -> None:
    """The redesigned footer has useful navigation and one focused CTA."""
    response = page.goto(f"{config.BASE_URL}/index.html", wait_until="networkidle")
    assert response is not None and response.status < 400

    footer = page.locator("footer.site-footer")
    assert footer.count() == 1
    footer_text = footer.inner_text()
    for expected in ("Arbyte", "Learn", "Courses", "Coimbatore", "Start a conversation"):
        assert expected in footer_text


def test_external_blank_links_are_isolated(page: Page) -> None:
    """New-tab links must prevent opener access and referrer leakage."""
    response = page.goto(f"{config.BASE_URL}/index.html", wait_until="networkidle")
    assert response is not None and response.status < 400

    links = page.locator('a[target="_blank"]')
    for index in range(links.count()):
        rel_tokens = set((links.nth(index).get_attribute("rel") or "").split())
        assert {"noopener", "noreferrer"}.issubset(rel_tokens)


def test_page_uses_strict_mermaid_without_third_party_trackers(page: Page) -> None:
    """Diagrams are hardened and obsolete analytics/advertising is not loaded."""
    response = page.goto(f"{config.BASE_URL}/index.html", wait_until="networkidle")
    assert response is not None and response.status < 400

    script_sources = page.locator("script[src]").evaluate_all(
        "scripts => scripts.map(script => script.src)"
    )
    assert not any("googletagmanager" in src or "googlesyndication" in src for src in script_sources)

    runtime_response = page.request.get(
        f"{config.BASE_URL}/assets/javascripts/mermaid-runtime.js"
    )
    assert runtime_response.status < 400
    runtime_source = runtime_response.text()
    assert 'securityLevel: "strict"' in runtime_source
    assert "htmlLabels: false" in runtime_source
