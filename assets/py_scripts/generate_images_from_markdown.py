"""Generate image assets from Markdown descriptions.

Reads each Markdown file in ``assets/image_desc`` (YAML front matter plus a
plain-text description), renders a simple card image with Pillow using the
front-matter settings, and writes the result to ``assets/images_gen``.

Front matter fields (all optional, per file):
    output:     Output file name written under the output directory
                (defaults to "<markdown-file-stem>.png").
    title:      Heading drawn at the top of the image
                (defaults to the markdown file stem).
    width:      Image width in pixels (default 800).
    height:     Image height in pixels (default 450).
    background: Background color (default "#1c1c1c").
    foreground: Text color (default "#ffffff").

The Markdown body (everything after the closing "---") is wrapped and drawn
as the image's description text.

Usage:
    python generate_images_from_markdown.py
    python generate_images_from_markdown.py --source-dir ../image_desc --output-dir ../images_gen

Prerequisites:
    - Python 3.10+
    - Install dependencies (run from this "py_scripts" directory, or use
      the path from the repository root):
        pip install -r requirements.txt
        pip install -r assets/py_scripts/requirements.txt   (from repo root)

Running the tests for this script:
    pip install -r ../tests/requirements.txt
    pytest ../tests                                            # all asset tests
    pytest ../tests/test_generate_images_from_markdown.py      # this script only
    pytest ../tests -k parse_markdown                          # filter by test name
    pytest ../tests -v                                         # verbose output
"""

from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n?(.*)$", re.DOTALL)

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 450
DEFAULT_BACKGROUND = "#1c1c1c"
DEFAULT_FOREGROUND = "#ffffff"


def parse_markdown(path: Path) -> tuple[dict, str]:
    """Split a markdown file into its YAML front matter and body text."""
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path} is missing YAML front matter (--- ... ---)")
    front_matter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()
    return front_matter, body


def _load_font(size: int) -> ImageFont.ImageFont:
    for candidate in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_image(front_matter: dict, body: str, title_default: str, output_path: Path) -> None:
    width = int(front_matter.get("width", DEFAULT_WIDTH))
    height = int(front_matter.get("height", DEFAULT_HEIGHT))
    background = front_matter.get("background", DEFAULT_BACKGROUND)
    foreground = front_matter.get("foreground", DEFAULT_FOREGROUND)
    title = front_matter.get("title", title_default)

    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)

    title_font = _load_font(size=max(24, height // 12))
    body_font = _load_font(size=max(16, height // 22))

    margin = max(20, width // 20)
    draw.text((margin, margin), title, fill=foreground, font=title_font)

    if body:
        wrapped = textwrap.fill(body, width=max(20, width // 12))
        title_height = title_font.size if hasattr(title_font, "size") else margin
        draw.multiline_text(
            (margin, margin + title_height + margin // 2),
            wrapped,
            fill=foreground,
            font=body_font,
            spacing=6,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def generate_all(source_dir: Path, output_dir: Path) -> list[Path]:
    generated = []
    for md_path in sorted(source_dir.glob("*.md")):
        front_matter, body = parse_markdown(md_path)
        output_name = front_matter.get("output", f"{md_path.stem}.png")
        output_path = output_dir / output_name
        render_image(front_matter, body, md_path.stem, output_path)
        generated.append(output_path)
    return generated


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-dir", type=Path, default=script_dir / ".." / "image_desc")
    parser.add_argument("--output-dir", type=Path, default=script_dir / ".." / "images_gen")
    args = parser.parse_args()

    generated = generate_all(args.source_dir.resolve(), args.output_dir.resolve())
    if not generated:
        print("No markdown descriptions found.")
        return
    for path in generated:
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
