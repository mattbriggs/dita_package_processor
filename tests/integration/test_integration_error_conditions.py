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


def test_missing_main_map_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    target_dir = package_dir / "out"

    exit_code = _run_cli(
        [
            "dita_package_processor",
            "run",
            "--package",
            str(package_dir),
            "--target",
            str(target_dir),
            "--docx-stem",
            "OutputDoc",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "no main map detected" in captured.err.lower()


def test_index_without_mapref_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    target_dir = package_dir / "out"

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
            "--target",
            str(target_dir),
            "--docx-stem",
            "OutputDoc",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "no main map detected" in captured.err.lower()


def test_referenced_main_map_missing_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    target_dir = package_dir / "out"

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
            "--target",
            str(target_dir),
            "--docx-stem",
            "OutputDoc",
        ],
        monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "main.ditamap" in captured.err.lower()


def test_definition_map_missing_is_non_fatal(tmp_path: Path, monkeypatch, capsys) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    target_dir = package_dir / "out"

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
            "--target",
            str(target_dir),
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
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()

    target_dir = package_dir / "out"

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
            "--target",
            str(target_dir),
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