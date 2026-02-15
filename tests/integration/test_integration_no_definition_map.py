"""
Integration test: running without a definition map.

Validates that glossary refactoring is optional and that the
pipeline completes successfully when no definition map is provided.

- Glossary logic must be skipped cleanly
- Execution succeeds
- No filesystem mutation in dry-run
"""

from __future__ import annotations

import sys
from pathlib import Path

from dita_package_processor.cli import main as cli_main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pipeline_runs_without_definition_map(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """
    Ensure processor completes successfully when no definition map
    is configured.

    - Glossary logic must be skipped
    - Execution succeeds
    - No filesystem mutation in dry-run
    """

    package_dir = tmp_path / "pkg"
    topics_dir = package_dir / "topics"
    topics_dir.mkdir(parents=True)

    target_dir = package_dir / "out"

    index_map = package_dir / "index.ditamap"
    main_map = package_dir / "Main.ditamap"
    topic_a = topics_dir / "a.dita"
    topic_t1 = topics_dir / "t1.dita"

    # ------------------------------------------------------------
    # Minimal valid package
    # ------------------------------------------------------------

    _write_file(
        index_map,
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <mapref href="Main.ditamap"/>
</map>
""",
    )

    _write_file(
        main_map,
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <title>Main</title>
  <topicref href="topics/a.dita"/>
</map>
""",
    )

    _write_file(
        topic_a,
        """<?xml version="1.0" encoding="UTF-8"?>
<concept id="a">
  <title>A</title>
  <conbody/>
</concept>
""",
    )

    _write_file(
        topic_t1,
        """<?xml version="1.0" encoding="UTF-8"?>
<concept id="t1">
  <title>T1</title>
  <conbody/>
</concept>
""",
    )

    # ------------------------------------------------------------
    # Run CLI (dry-run default, no definition-map)
    # ------------------------------------------------------------

    argv = [
        "dita_package_processor",
        "run",
        "--package",
        str(package_dir),
        "--target",
        str(target_dir),
        "--docx-stem",
        "OutputDoc",
    ]

    monkeypatch.setattr(sys, "argv", argv)

    exit_code = cli_main()

    # ------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------

    # Pipeline completes successfully
    assert exit_code == 0

    # Dry-run mode: no filesystem mutation
    assert index_map.exists()
    assert main_map.exists()
    assert topic_a.exists()
    assert topic_t1.exists()

    # No glossary artifacts created
    glossary_files = list(topics_dir.glob("*gloss*.dita"))
    assert glossary_files == []