"""Static site-wide check that every image referenced by source files
(config, data, includes/layouts, and page front matter) actually exists in
``assets/images``. If a referenced image is missing, this test also requires
a matching Markdown description in ``assets/image_desc`` so it can be
regenerated with ``assets/py_scripts/generate_images_from_markdown.py``.

This complements the live-browser check in
``tests/test_site_pages.py::test_public_page_has_no_missing_images`` --
this one runs without starting a Jekyll server or browser.

Run with:
    pytest assets/tests/test_site_images_present.py
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGES_DIR = REPO_ROOT / "assets" / "images"
IMAGE_DESC_DIR = REPO_ROOT / "assets" / "image_desc"

LOGO_RE = re.compile(r"^logo:\s*/assets/images/(\S+)", re.MULTILINE)
DATA_URL_RE = re.compile(r"url:\s*/assets/images/(\S+)")
STATIC_SRC_RE = re.compile(r'/assets/images/([\w.\-]+\.(?:png|jpe?g|svg|gif|webp))')
FRONT_MATTER_IMGSRC_RE = re.compile(r'^imgsrc:\s*"([^"]+)"', re.MULTILINE)


def _referenced_images() -> dict[str, list[str]]:
    """Map each referenced image file name to the source file(s) mentioning it."""
    references: dict[str, list[str]] = {}

    def add(name: str, source: Path) -> None:
        references.setdefault(name, []).append(str(source.relative_to(REPO_ROOT)))

    config_path = REPO_ROOT / "_config.yml"
    for match in LOGO_RE.finditer(config_path.read_text(encoding="utf-8")):
        add(match.group(1), config_path)

    for data_path in (REPO_ROOT / "_data").glob("*.yml"):
        for match in DATA_URL_RE.finditer(data_path.read_text(encoding="utf-8")):
            add(match.group(1), data_path)

    for html_dir in (REPO_ROOT / "_includes", REPO_ROOT / "_layouts"):
        for html_path in html_dir.glob("*.html"):
            for match in STATIC_SRC_RE.finditer(html_path.read_text(encoding="utf-8")):
                add(match.group(1), html_path)

    for md_path in (REPO_ROOT / "siteContents").rglob("*.md"):
        for match in FRONT_MATTER_IMGSRC_RE.finditer(md_path.read_text(encoding="utf-8")):
            add(match.group(1), md_path)

    return references


def test_every_referenced_image_exists_or_has_a_description():
    references = _referenced_images()
    assert references, "No image references were found -- the scan patterns may be out of date."

    missing = []
    for image_name, sources in sorted(references.items()):
        if (IMAGES_DIR / image_name).exists():
            continue

        desc_path = IMAGE_DESC_DIR / f"{Path(image_name).stem}.md"
        if desc_path.exists():
            missing.append(
                f"{image_name} (referenced in {', '.join(sources)}) is missing from {IMAGES_DIR}, "
                f"but a description exists at {desc_path} -- run "
                "'python assets/py_scripts/generate_images_from_markdown.py' to generate it"
            )
        else:
            missing.append(
                f"{image_name} (referenced in {', '.join(sources)}) is missing from {IMAGES_DIR} "
                f"and has no description at {desc_path} -- add one so it can be generated"
            )

    assert not missing, "Missing image(s):\n" + "\n".join(missing)
