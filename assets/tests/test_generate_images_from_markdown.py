"""Tests for the image-generation pipeline in ``assets/py_scripts``.

Covers the Markdown front-matter parser and image renderer directly
(``generate_images_from_markdown.py``), plus an end-to-end check that every
description in ``assets/image_desc`` produces a valid, correctly sized image
in ``assets/images_gen``.

Run with:
    pip install -r assets/tests/requirements.txt
    pytest assets/tests
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

ASSETS_DIR = Path(__file__).resolve().parents[1]
PY_SCRIPTS_DIR = ASSETS_DIR / "py_scripts"
IMAGE_DESC_DIR = ASSETS_DIR / "image_desc"
IMAGES_GEN_DIR = ASSETS_DIR / "images_gen"

sys.path.insert(0, str(PY_SCRIPTS_DIR))
import generate_images_from_markdown as gen  # noqa: E402  (import after sys.path tweak)


# --- parse_markdown -----------------------------------------------------


def test_parse_markdown_reads_front_matter_and_body(tmp_path):
    md_file = tmp_path / "sample.md"
    md_file.write_text(
        '---\ntitle: "Sample"\noutput: sample.png\nwidth: 100\nheight: 50\n---\n'
        "Sample description text.\n",
        encoding="utf-8",
    )

    front_matter, body = gen.parse_markdown(md_file)

    assert front_matter == {"title": "Sample", "output": "sample.png", "width": 100, "height": 50}
    assert body == "Sample description text."


def test_parse_markdown_requires_front_matter(tmp_path):
    md_file = tmp_path / "no_front_matter.md"
    md_file.write_text("Just a description, no front matter.", encoding="utf-8")

    with pytest.raises(ValueError):
        gen.parse_markdown(md_file)


# --- render_image ---------------------------------------------------------


def test_render_image_writes_file_with_requested_dimensions(tmp_path):
    output_path = tmp_path / "rendered.png"

    gen.render_image(
        front_matter={"width": 320, "height": 180, "background": "#123456", "foreground": "#ffffff"},
        body="Some description text that should be wrapped across lines.",
        title_default="rendered",
        output_path=output_path,
    )

    assert output_path.exists()
    with Image.open(output_path) as image:
        assert image.size == (320, 180)


def test_render_image_uses_defaults_when_front_matter_is_sparse(tmp_path):
    output_path = tmp_path / "defaults.png"

    gen.render_image(front_matter={}, body="", title_default="defaults", output_path=output_path)

    assert output_path.exists()
    with Image.open(output_path) as image:
        assert image.size == (gen.DEFAULT_WIDTH, gen.DEFAULT_HEIGHT)


# --- generate_all ---------------------------------------------------------


def test_generate_all_honors_output_field_and_stem_fallback(tmp_path):
    source_dir = tmp_path / "image_desc"
    output_dir = tmp_path / "images_gen"
    source_dir.mkdir()

    (source_dir / "with_output.md").write_text(
        '---\ntitle: "Has explicit output"\noutput: custom_name.jpg\nwidth: 64\nheight: 64\n---\nBody text.',
        encoding="utf-8",
    )
    (source_dir / "without_output.md").write_text(
        '---\ntitle: "Falls back to stem"\nwidth: 64\nheight: 64\n---\nBody text.',
        encoding="utf-8",
    )

    generated = gen.generate_all(source_dir, output_dir)

    generated_names = {path.name for path in generated}
    assert generated_names == {"custom_name.jpg", "without_output.png"}
    for path in generated:
        assert path.exists()


# --- end-to-end: real image_desc descriptions -----------------------------


def _image_desc_files() -> list[Path]:
    return sorted(IMAGE_DESC_DIR.glob("*.md"))


@pytest.mark.parametrize("md_path", _image_desc_files(), ids=lambda p: p.stem)
def test_each_image_description_has_valid_front_matter(md_path):
    front_matter, body = gen.parse_markdown(md_path)

    assert front_matter.get("title"), f"{md_path.name} is missing a 'title' in its front matter"
    assert body, f"{md_path.name} has no description body"


def test_generate_all_produces_one_image_per_description(tmp_path):
    output_dir = tmp_path / "images_gen"

    generated = gen.generate_all(IMAGE_DESC_DIR, output_dir)

    assert len(generated) == len(_image_desc_files())
    for path in generated:
        assert path.exists() and path.stat().st_size > 0
        with Image.open(path) as image:
            # Any successfully decoded image has non-zero dimensions.
            assert all(dimension > 0 for dimension in image.size)


@pytest.mark.parametrize("md_path", _image_desc_files(), ids=lambda p: p.stem)
def test_committed_generated_image_matches_description(md_path):
    """Guards against ``assets/images_gen`` drifting out of sync with
    ``assets/image_desc`` (i.e. someone edited a description but forgot to
    re-run ``generate_images_from_markdown.py``)."""
    front_matter, _ = gen.parse_markdown(md_path)
    output_name = front_matter.get("output", f"{md_path.stem}.png")
    committed_path = IMAGES_GEN_DIR / output_name

    assert committed_path.exists(), (
        f"{committed_path} does not exist; run "
        "'python assets/py_scripts/generate_images_from_markdown.py' to generate it"
    )
    expected_width = int(front_matter.get("width", gen.DEFAULT_WIDTH))
    expected_height = int(front_matter.get("height", gen.DEFAULT_HEIGHT))
    with Image.open(committed_path) as image:
        assert image.size == (expected_width, expected_height)
