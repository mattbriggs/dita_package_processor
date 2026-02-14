#!/usr/bin/env python3
"""
Generate Markdown documentation from JSON Schema files.

This script scans the DITA Package Processor repository for *project-owned*
JSON Schemas and produces human-readable Markdown reference documentation
suitable for MkDocs.

It is intentionally conservative:
- Only schemas inside the project source tree are processed
- JSON Schema boolean schemas are handled safely
- Metaschemas and third-party dependencies are ignored
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGER = logging.getLogger("schema_docs")
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)

# ---------------------------------------------------------------------------
# Schema Parsing
# ---------------------------------------------------------------------------


class JsonSchemaParser:
    """
    Parses a JSON Schema document into Markdown sections.

    This parser is intentionally shallow: it documents *structure*, not
    every nuance of the JSON Schema specification.
    """

    def parse(self, raw: Dict[str, Any], source_path: Path) -> str:
        """
        Convert a JSON Schema document into Markdown.

        :param raw: Parsed JSON schema
        :param source_path: Path to the schema file
        :return: Markdown document
        """
        title = raw.get("title", source_path.stem)
        description = raw.get("description", "")

        lines: List[str] = [
            f"# {title}",
            "",
        ]

        if description:
            lines.extend(
                [
                    description,
                    "",
                ]
            )

        properties = raw.get("properties")
        if not isinstance(properties, dict):
            LOGGER.warning(
                "Schema %s has no object properties; skipping field table",
                source_path,
            )
            return "\n".join(lines)

        required = raw.get("required", [])

        lines.extend(
            [
                "## Properties",
                "",
                "| Name | Type | Required | Description |",
                "|------|------|----------|-------------|",
            ]
        )

        for name, spec in properties.items():
            field_type = self._render_type(spec)
            is_required = "yes" if name in required else "no"
            field_desc = self._render_description(spec)

            lines.append(
                f"| `{name}` | {field_type} | {is_required} | {field_desc} |"
            )

        return "\n".join(lines)

    @staticmethod
    def _render_type(spec: Any) -> str:
        """
        Render a human-readable type from a JSON Schema fragment.

        JSON Schema permits boolean schemas and composite constructs; these
        are rendered conservatively.
        """
        if isinstance(spec, bool):
            return "boolean-schema"

        if not isinstance(spec, dict):
            return "unknown"

        if "type" in spec:
            return str(spec["type"])

        if "$ref" in spec:
            return f"ref({spec['$ref']})"

        if "oneOf" in spec:
            return "oneOf"

        if "anyOf" in spec:
            return "anyOf"

        if "allOf" in spec:
            return "allOf"

        return "object"

    @staticmethod
    def _render_description(spec: Any) -> str:
        """
        Extract a description from a schema fragment.
        """
        if isinstance(spec, dict):
            return spec.get("description", "")
        return ""


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class SchemaDocGenerator:
    """
    Orchestrates schema discovery and documentation generation.
    """

    def __init__(
        self,
        repo_root: Path,
        output_dir: Path,
    ) -> None:
        self.repo_root = repo_root
        self.output_dir = output_dir
        self.parser = JsonSchemaParser()

    def run(self) -> None:
        """
        Execute schema discovery and documentation generation.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        for path in self._find_schema_files():
            LOGGER.info("Processing schema: %s", path)
            self._process_schema(path)

    def _find_schema_files(self) -> Iterable[Path]:
        """
        Yield project-owned JSON Schema files.

        This deliberately excludes:
        - virtual environments
        - site-packages
        - third-party schemas
        """
        source_root = self.repo_root / "dita_package_processor"

        for path in source_root.rglob("*.schema.json"):
            yield path

        for path in source_root.rglob("*.schema.yaml"):
            yield path

        for path in source_root.rglob("*.schema.yml"):
            yield path

    def _process_schema(self, path: Path) -> None:
        """
        Load, parse, and write documentation for a single schema.
        """
        try:
            raw = self._load_schema(path)
            doc = self.parser.parse(raw, path)
            self._write_doc(path, doc)
        except Exception:
            LOGGER.exception("Schema documentation generation failed.")
            raise

    @staticmethod
    def _load_schema(path: Path) -> Dict[str, Any]:
        """
        Load a JSON Schema file.

        :param path: Schema file path
        :return: Parsed schema
        """
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write_doc(self, schema_path: Path, content: str) -> None:
        """
        Write Markdown documentation for a schema.

        Output filename mirrors schema name.
        """
        target = self.output_dir / f"{schema_path.stem}.md"
        target.write_text(content, encoding="utf-8")
        LOGGER.info("Wrote %s", target)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    CLI entry point.
    """
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "docs" / "reference" / "schemas"

    generator = SchemaDocGenerator(
        repo_root=repo_root,
        output_dir=output_dir,
    )
    generator.run()


if __name__ == "__main__":
    main()