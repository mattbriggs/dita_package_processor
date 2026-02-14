"""
Integration test: running without a definition map.

These tests validate that glossary refactoring is truly optional and that
the pipeline completes successfully when no definition map is provided.

No glossary-related mutation must occur.
No warnings or errors should be emitted.
Filesystem content must remain untouched in dry-run mode.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dita_package_processor.cli import main as cli_main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_file(path: Path, content: str) -> None:
    """
    Write text content to a file, ensuring parent directories exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pipeline_runs_without_definition_map(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    """
    Ensure the processor completes successfully when no definition map
    is configured.

    - Glossary logic must be skipped cleanly
    - No warnings or errors emitted
    - No filesystem mutation in dry-run
    - No glossary artifacts created
    """
    package_dir = tmp_path / "pkg"
    topics_dir = package_dir / "topics"
    topics_dir.mkdir(parents=True)

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
    # Run CLI (no definition-map, dry-run default)
    # ------------------------------------------------------------

    argv = [
        "dita_package_processor",
        "run",
        "--package",
        str(package_dir),
        "--docx-stem",
        "OutputDoc",
    ]

    monkeypatch.setattr(sys, "argv", argv)
    exit_code = cli_main()

    captured = capsys.readouterr()

    # ------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------

    # Pipeline completes successfully
    assert exit_code == 0

    # No errors or warnings should be emitted
    assert captured.err.strip() == ""

    # Source files remain untouched (dry-run safety)
    assert index_map.exists()
    assert main_map.exists()
    assert topic_a.exists()
    assert topic_t1.exists()

    # No glossary artifacts created
    glossary_files = list(topics_dir.glob("*gloss*.dita"))
    assert glossary_files == []