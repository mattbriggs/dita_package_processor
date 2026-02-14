#!/usr/bin/env python3
"""
Generate Markdown documentation from known_patterns.yaml.

This script documents *structural knowledge*, not execution logic.
Patterns are treated as declarative, auditable facts about real-world
DITA packages.

The output is designed for MkDocs consumption.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGER = logging.getLogger("pattern_docs")
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)

# ---------------------------------------------------------------------------
# Pattern Rendering
# ---------------------------------------------------------------------------


class PatternRenderer:
    """
    Converts a single pattern definition into Markdown.
    """

    def render(self, pattern: Dict[str, Any]) -> str:
        """
        Render a pattern to Markdown.

        :param pattern: Pattern definition from YAML
        :return: Markdown content
        """
        lines: List[str] = []

        lines.append(f"# Pattern: `{pattern['id']}`")
        lines.append("")

        lines.append("## Applies To")
        lines.append(f"`{pattern['applies_to']}`")
        lines.append("")

        lines.append("## Signals")
        lines.append("```yaml")
        lines.append(yaml.safe_dump(pattern.get("signals", {}), sort_keys=False))
        lines.append("```")
        lines.append("")

        lines.append("## Asserts")
        lines.append("```yaml")
        lines.append(yaml.safe_dump(pattern.get("asserts", {}), sort_keys=False))
        lines.append("```")
        lines.append("")

        rationale = pattern.get("rationale", [])
        if rationale:
            lines.append("## Rationale")
            for item in rationale:
                lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class PatternDocGenerator:
    """
    Orchestrates pattern documentation generation.
    """

    def __init__(
        self,
        patterns_file: Path,
        output_dir: Path,
    ) -> None:
        self.patterns_file = patterns_file
        self.output_dir = output_dir
        self.renderer = PatternRenderer()

    def run(self) -> None:
        """
        Generate documentation for all known patterns.
        """
        data = self._load_patterns()
        patterns = data.get("patterns", [])

        self.output_dir.mkdir(parents=True, exist_ok=True)

        index_lines = [
            "# Known Structural Patterns",
            "",
            "This section documents the *structural knowledge* used during "
            "Discovery to emit evidence about DITA artifacts.",
            "",
            "Patterns are declarative. They do not mutate content.",
            "",
            "## Pattern Index",
            "",
        ]

        for pattern in patterns:
            doc = self.renderer.render(pattern)
            filename = f"{pattern['id']}.md"
            target = self.output_dir / filename

            target.write_text(doc, encoding="utf-8")
            LOGGER.info("Wrote %s", target)

            index_lines.append(f"- [{pattern['id']}]({filename})")

        index_path = self.output_dir / "index.md"
        index_path.write_text("\n".join(index_lines), encoding="utf-8")
        LOGGER.info("Wrote %s", index_path)

    def _load_patterns(self) -> Dict[str, Any]:
        """
        Load the known_patterns.yaml file.
        """
        LOGGER.info("Loading patterns from %s", self.patterns_file)
        with self.patterns_file.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    patterns_file = (
        repo_root
        / "dita_package_processor"
        / "knowledge"
        / "known_patterns.yaml"
    )

    output_dir = repo_root / "docs" / "reference" / "patterns"

    generator = PatternDocGenerator(
        patterns_file=patterns_file,
        output_dir=output_dir,
    )
    generator.run()


if __name__ == "__main__":
    main()