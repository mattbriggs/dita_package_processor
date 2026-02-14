#!/usr/bin/env python3
"""
tree.py

Generates an ASCII tree representation of the project repository and
writes a detailed report to a timestamped text file.

Key guarantees:
- The scan root is always the repository root (working directory)
- Ignore patterns are always loaded from tools/tree_ignore.txt
- Behavior is deterministic regardless of invocation location
"""

from __future__ import annotations

import fnmatch
import time
from datetime import datetime
from pathlib import Path
from typing import List

# ------------------------------------------------------------
# Ignore handling
# ------------------------------------------------------------

def load_ignore_patterns(ignore_file: Path) -> List[str]:
    """
    Load gitignore-style patterns from the ignore file.

    :param ignore_file: Path to tree_ignore.txt
    :return: List of ignore patterns
    """
    if not ignore_file.exists():
        print(f"WARNING: Ignore file not found: {ignore_file}")
        return []

    patterns: List[str] = []

    for line in ignore_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)

    return patterns


def is_ignored(path: Path, patterns: List[str], root: Path) -> bool:
    """
    Determine whether a path should be ignored based on ignore patterns.

    :param path: Path being evaluated
    :param patterns: Ignore patterns
    :param root: Scan root
    :return: True if ignored
    """
    rel = path.relative_to(root).as_posix()

    for pattern in patterns:
        # Directory ignore
        if pattern.endswith("/") and rel.startswith(pattern[:-1]):
            return True

        # Glob ignore
        if fnmatch.fnmatch(rel, pattern):
            return True

    return False


# ------------------------------------------------------------
# Tree building and metrics
# ------------------------------------------------------------

file_count = 0
dir_count = 0
line_count = 0


def build_tree(
    path: Path,
    root: Path,
    ignore: List[str],
    prefix: str = "",
) -> List[str]:
    """
    Recursively build an ASCII tree representation.

    :param path: Current directory
    :param root: Scan root
    :param ignore: Ignore patterns
    :param prefix: Tree prefix
    :return: List of tree lines
    """
    global file_count, dir_count, line_count

    lines: List[str] = []

    try:
        entries = sorted(
            [
                e for e in path.iterdir()
                if not e.is_symlink() and not is_ignored(e, ignore, root)
            ],
            key=lambda p: (p.is_file(), p.name.lower()),
        )
    except PermissionError:
        return lines

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            dir_count += 1
            extension = "    " if index == len(entries) - 1 else "│   "
            lines.extend(build_tree(entry, root, ignore, prefix + extension))
        else:
            file_count += 1
            try:
                with entry.open("r", encoding="utf-8", errors="ignore") as f:
                    line_count += sum(1 for _ in f)
            except Exception:
                pass

        # Heartbeat every ~200 files
        if file_count > 0 and file_count % 200 == 0:
            print(f"Scanning… {file_count} files, {dir_count} dirs, {line_count} lines")

    return lines


# ------------------------------------------------------------
# Main execution
# ------------------------------------------------------------

def main() -> None:
    global file_count, dir_count, line_count

    # Scan root is always the repository root (cwd)
    root = Path.cwd()

    # Ignore file is always colocated with this script
    script_dir = Path(__file__).resolve().parent
    ignore_file = script_dir / "tree_ignore.txt"

    ignore_patterns = load_ignore_patterns(ignore_file)

    print("\nProject tree scan starting…")
    print(f"Scan root: {root}")
    print(f"Ignore file: {ignore_file}")
    print(f"Ignore patterns loaded: {len(ignore_patterns)}")
    print("-" * 60)

    start = time.time()

    tree_lines = [root.name]
    tree_lines.extend(build_tree(root, root, ignore_patterns))

    elapsed = time.time() - start

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = root / f"project_tree_{timestamp}.txt"

    report = [
        "Project Tree Report",
        f"Generated: {datetime.now().isoformat()}",
        f"Root: {root}",
        "",
        "ASCII TREE",
        "=" * 60,
        *tree_lines,
        "",
        "PROJECT METRICS",
        "=" * 60,
        f"Directories: {dir_count}",
        f"Files:       {file_count}",
        f"Lines of code: {line_count}",
        f"Scan time:    {elapsed:.2f} seconds",
        "",
        "Interpretation:",
        (
            "This is a structural snapshot of your repository. "
            "It reflects architecture, complexity, and surface area. "
            "If this feels large, it’s because the project is doing real work."
        ),
    ]

    output_file.write_text("\n".join(report), encoding="utf-8")

    print("\nScan complete.")
    print(f"Files: {file_count}")
    print(f"Dirs: {dir_count}")
    print(f"Lines: {line_count}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Report written to: {output_file}\n")


if __name__ == "__main__":
    main()