"""Tests for the fully offline PlantUML diagram pipeline in
``assets/py_scripts/generate_plantuml_images.py``.

These tests shell out to the local Java runtime and the bundled
``plantuml.jar``, so they are skipped automatically if either is missing
(e.g. on a machine without a JRE installed).

Run with:
    pip install -r assets/tests/requirements.txt
    pytest assets/tests
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ASSETS_DIR = Path(__file__).resolve().parents[1]
PY_SCRIPTS_DIR = ASSETS_DIR / "py_scripts"
IMAGE_DESC_DIR = ASSETS_DIR / "image_desc"

sys.path.insert(0, str(PY_SCRIPTS_DIR))
import generate_plantuml_images as gen  # noqa: E402  (import after sys.path tweak)


def _java_available() -> bool:
    if shutil.which("java") is None:
        return False
    try:
        subprocess.run(["java", "-version"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


requires_plantuml = pytest.mark.skipif(
    not (gen.PLANTUML_JAR.exists() and _java_available()),
    reason="requires a local Java runtime and assets/py_scripts/plantuml.jar",
)


# --- mermaid_chain_to_plantuml ---------------------------------------------


def test_mermaid_chain_to_plantuml_converts_labeled_chain():
    mermaid_source = (
        "graph LR\n"
        "    A[Visitor] --> B[Navbar]\n"
        "    B --> C[Arbyte Logo]\n"
        "    C --> D[Homepage]\n"
    )

    plantuml_source = gen.mermaid_chain_to_plantuml(mermaid_source)

    assert plantuml_source.startswith("@startuml\nstart\n")
    assert plantuml_source.rstrip().endswith("stop\n@enduml".rstrip())
    assert ":Visitor;" in plantuml_source
    assert ":Navbar;" in plantuml_source
    assert ":Arbyte Logo;" in plantuml_source
    assert ":Homepage;" in plantuml_source


def test_mermaid_chain_to_plantuml_requires_at_least_one_edge():
    with pytest.raises(ValueError):
        gen.mermaid_chain_to_plantuml("graph LR\n    just some text, no edges\n")


# --- render_plantuml / generate_all (require local Java + plantuml.jar) ---


@requires_plantuml
def test_render_plantuml_produces_svg_bytes():
    diagram = "@startuml\nstart\n:Step One;\n:Step Two;\nstop\n@enduml\n"

    image_bytes = gen.render_plantuml(diagram, "svg")

    assert image_bytes.strip().startswith(b"<?xml") or b"<svg" in image_bytes[:200]


@requires_plantuml
def test_generate_all_renders_one_diagram_per_description_with_mermaid_field(tmp_path):
    output_dir = tmp_path / "images_gen"

    generated = gen.generate_all(IMAGE_DESC_DIR, output_dir)

    md_files_with_mermaid = [
        md for md in IMAGE_DESC_DIR.glob("*.md") if gen.parse_markdown(md)[0].get("mermaid")
    ]
    assert len(generated) == len(md_files_with_mermaid)
    for path in generated:
        assert path.exists() and path.stat().st_size > 0
        assert b"<svg" in path.read_bytes()
