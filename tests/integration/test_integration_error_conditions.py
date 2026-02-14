"""
Error condition integration tests for the DITA Package Processor.

These tests validate that the `run` orchestration command:

- Fails loudly for structural violations
- Emits warnings for optional enrichment failures
- Continues safely when enrichment is unavailable
- Always exercises real CLI wiring and filesystem state
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


def _run_cli(argv: list[str], monkeypatch) -> int:
    monkeypatch.setattr(sys, "argv", argv)
    return cli_main()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_missing_index_map_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    """
    index.ditamap is mandatory. Its absence is fatal.
    """
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    exit_code = _run_cli(
        [
            "dita_package_processor",
            "run",
            "--package",
            str(package_dir),
            "--docx-stem",
            "OutputDoc",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "index.ditamap" in captured.err.lower()


def test_index_map_without_mapref_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    """
    index.ditamap must reference a main map.
    """
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    _write_file(
        package_dir / "index.ditamap",
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <title>No mapref</title>
</map>
""",
    )

    exit_code = _run_cli(
        [
            "dita_package_processor",
            "run",
            "--package",
            str(package_dir),
            "--docx-stem",
            "OutputDoc",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "reference a main map" in captured.err.lower()


def test_referenced_main_map_missing_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    """
    The map referenced by index.ditamap must exist.
    """
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    _write_file(
        package_dir / "index.ditamap",
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <mapref href="Main.ditamap"/>
</map>
""",
    )

    exit_code = _run_cli(
        [
            "dita_package_processor",
            "run",
            "--package",
            str(package_dir),
            "--docx-stem",
            "OutputDoc",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "main map" in captured.err.lower()


def test_definition_map_missing_is_non_fatal(tmp_path: Path, monkeypatch, capsys) -> None:
    """
    Missing definition map must warn but not abort execution.
    """
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    _write_file(
        package_dir / "index.ditamap",
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <mapref href="Main.ditamap"/>
</map>
""",
    )

    _write_file(
        package_dir / "Main.ditamap",
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <title>Main</title>
</map>
""",
    )

    exit_code = _run_cli(
        [
            "dita_package_processor",
            "run",
            "--package",
            str(package_dir),
            "--docx-stem",
            "OutputDoc",
            "--definition-map",
            "DoesNotExist.ditamap",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "definition map not found" in captured.err.lower()


def test_definition_navtitle_not_found_is_non_fatal(tmp_path: Path, monkeypatch, capsys) -> None:
    """
    Missing definition navtitle must warn but not abort execution.
    """
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    _write_file(
        package_dir / "index.ditamap",
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <mapref href="Main.ditamap"/>
</map>
""",
    )

    _write_file(
        package_dir / "Main.ditamap",
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <title>Main</title>
</map>
""",
    )

    _write_file(
        package_dir / "Definitions.ditamap",
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <topicref navtitle="Something else"/>
</map>
""",
    )

    exit_code = _run_cli(
        [
            "dita_package_processor",
            "run",
            "--package",
            str(package_dir),
            "--docx-stem",
            "OutputDoc",
            "--definition-map",
            "Definitions.ditamap",
            "--definition-navtitle",
            "Definition topic",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "definition navtitle not found" in captured.err.lower()