"""Render diagrams from Markdown front matter into image files, fully offline.

Renders the Mermaid-style flowchart diagrams stored in ``assets/image_desc``
to real diagram images without any network access, Node.js, or browser. It:

1. Reads the ``mermaid:`` front-matter field from each Markdown file in
   ``assets/image_desc`` (the same field used for the client-side Mermaid.js
   pipeline -- see ``generate_images_from_markdown.py`` for the front-matter
   format).
2. Translates the simple Mermaid flowchart syntax used in this project
   (``graph TD|LR`` with ``ID[Label] --> ID2[Label2]`` edges forming a single
   chain) into an equivalent PlantUML activity diagram.
3. Renders that diagram to an image using the local ``plantuml.jar`` (bundled
   in this folder) via the Java runtime already installed on this machine --
   no network access, Node.js, or browser required.

PlantUML activity diagrams use PlantUML's own built-in layout engine, not
Graphviz, so no ``dot`` binary needs to be installed or bundled for the
diagrams used in this project. If a future diagram type requires Graphviz,
drop a `dot` executable next to ``plantuml.jar`` and PlantUML will pick it up
automatically (or set the ``GRAPHVIZ_DOT`` environment variable to point at
it) -- none of the current diagrams need this.

Usage:
    python generate_plantuml_images.py
    python generate_plantuml_images.py --format png
    python generate_plantuml_images.py --source-dir ../image_desc --output-dir ../images_gen

Prerequisites:
    - Python 3.10+ and this folder's dependencies (PyYAML; this script reuses
      generate_images_from_markdown.parse_markdown()):
        pip install -r requirements.txt
    - A local Java runtime (JRE/JDK 8+) available on PATH, check with:
        java -version
    - plantuml.jar present next to this script (already bundled here)

Running the tests for this script:
    pip install -r ../tests/requirements.txt
    pytest ../tests                                        # all asset tests
    pytest ../tests/test_generate_plantuml_images.py       # this script only
    pytest ../tests -k plantuml                            # filter by test name
    pytest ../tests -v                                     # verbose output
    (tests that need Java/plantuml.jar are skipped automatically if missing)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from generate_images_from_markdown import parse_markdown

PLANTUML_JAR = Path(__file__).resolve().parent / "plantuml.jar"
DEFAULT_FORMAT = "svg"

EDGE_RE = re.compile(
    r"^\s*([A-Za-z0-9_]+)(?:\[([^\]]+)\])?\s*-->\s*([A-Za-z0-9_]+)(?:\[([^\]]+)\])?\s*$"
)


def mermaid_chain_to_plantuml(mermaid_source: str) -> str:
    """Convert a simple Mermaid flowchart chain (``A[Label] --> B[Label]``)
    into an equivalent PlantUML activity diagram string.

    Only supports the single-chain flowchart subset used in this project's
    ``image_desc`` files; branching/merging diagrams are not handled.
    """
    labels: dict[str, str] = {}
    edges: list[tuple[str, str]] = []

    for line in mermaid_source.splitlines():
        match = EDGE_RE.match(line)
        if not match:
            continue
        src_id, src_label, dst_id, dst_label = match.groups()
        if src_label:
            labels[src_id] = src_label
        if dst_label:
            labels[dst_id] = dst_label
        edges.append((src_id, dst_id))

    if not edges:
        raise ValueError("No 'ID[Label] --> ID2[Label2]' edges found in mermaid source")

    targets = {dst for _, dst in edges}
    chain_start = next(src for src, _ in edges if src not in targets)

    next_node = dict(edges)
    ordered_ids = [chain_start]
    while ordered_ids[-1] in next_node:
        ordered_ids.append(next_node[ordered_ids[-1]])

    steps = [labels.get(node_id, node_id) for node_id in ordered_ids]
    body = "\n".join(f':{step.replace(";", ",")};' for step in steps)
    return f"@startuml\nstart\n{body}\nstop\n@enduml\n"


def render_plantuml(diagram_source: str, output_format: str) -> bytes:
    """Render PlantUML diagram source to image bytes using the local jar."""
    format_flag = {"svg": "-tsvg", "png": "-tpng"}[output_format]
    result = subprocess.run(
        ["java", "-jar", str(PLANTUML_JAR), format_flag, "-pipe"],
        input=diagram_source.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"PlantUML failed (exit {result.returncode}): {result.stderr.decode('utf-8', 'replace')}")
    return result.stdout


def generate_all(source_dir: Path, output_dir: Path, output_format: str = DEFAULT_FORMAT) -> list[Path]:
    generated = []
    for md_path in sorted(source_dir.glob("*.md")):
        front_matter, _ = parse_markdown(md_path)
        mermaid_source = front_matter.get("mermaid")
        if not mermaid_source:
            continue

        plantuml_source = mermaid_chain_to_plantuml(mermaid_source)
        image_bytes = render_plantuml(plantuml_source, output_format)

        output_name = front_matter.get("mermaid_output", f"{md_path.stem}_diagram.{output_format}")
        output_path = output_dir / output_name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)
        generated.append(output_path)
    return generated


def main() -> None:
    if not PLANTUML_JAR.exists():
        print(f"plantuml.jar not found at {PLANTUML_JAR}", file=sys.stderr)
        raise SystemExit(1)

    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-dir", type=Path, default=script_dir / ".." / "image_desc")
    parser.add_argument("--output-dir", type=Path, default=script_dir / ".." / "images_gen")
    parser.add_argument("--format", choices=("svg", "png"), default=DEFAULT_FORMAT, help="Output image format")
    args = parser.parse_args()

    generated = generate_all(args.source_dir.resolve(), args.output_dir.resolve(), args.format)
    if not generated:
        print("No 'mermaid' front matter found in any description.")
        return
    for path in generated:
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
