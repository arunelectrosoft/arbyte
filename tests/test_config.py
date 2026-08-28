"""Site-specific configuration for the Playwright test suite.

This is the ONLY file that needs to change to reuse the test suite
(``test_site_pages.py``) against a different web site: point ``BASE_URL``
at the new site, list its pages in ``PAGE_PATHS``, and set authentication
details if the site requires them.

Every value can also be overridden at run time via environment variables,
so CI/CD pipelines or the ``run_playwright_tests`` scripts can target a
different environment without editing this file.
"""

import os

# Base URL of the site under test (local dev server, staging, production, ...).
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:4000").rstrip("/")

# Map of short page names -> the path appended to BASE_URL.
# Add, remove, or rename entries here to adapt the suite to another site.
PAGE_PATHS = {
    "home": "/index.html",
    "courses": "/courses/",
    "demos": "/demos/",
    "blog": "/blog/",
    "about": "/about/",
    "contact": "/contact/",
}

# Pages exercised when the caller asks for "all" pages. Defaults to every
# entry in PAGE_PATHS (in declaration order); override to change the
# default subset/order without removing pages from PAGE_PATHS.
DEFAULT_PAGES = tuple(PAGE_PATHS.keys())

# --- Authentication ---------------------------------------------------
# Set AUTH_ENABLED=true (env var) if the site sits behind HTTP basic auth.
# Credentials are read from environment variables so secrets never need
# to be committed to the repository.
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").strip().lower() in {"1", "true", "yes"}
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")


def get_http_credentials() -> dict | None:
    """Return Playwright ``http_credentials`` for the browser context, or
    ``None`` when the site under test does not require authentication."""
    if not AUTH_ENABLED:
        return None
    return {"username": AUTH_USERNAME, "password": AUTH_PASSWORD}
