"""
Materialization domain models.

These models describe the *intended final shape* of a materialized
DITA package after execution has completed.

They do NOT:
- perform filesystem operations
- execute handlers
- infer missing artifacts

They DO:
- represent resolved, final target paths
- preserve traceability to source actions
- guarantee collision-free materialization
- serve as the execution → publishing contract
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

LOGGER = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Core materialization semantics
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class MaterializedFile:
    """
    Declarative record of a single materialized file.

    This represents a *resolved* target artifact, not a filesystem operation.

    Attributes
    ----------
    path:
        Absolute path of the file in the target package.
    source_action_id:
        ID of the execution action that produced this file.
    role:
        Optional semantic role (e.g. "map", "topic", "media").
    layout_metadata:
        Deterministic layout annotations explaining how this file
        was placed (policy name, original relative path, etc.).
    """

    path: Path
    source_action_id: Optional[str] = None
    role: Optional[str] = None
    layout_metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """
        Serialize the materialized file record.

        :return: JSON-safe dictionary.
        """
        LOGGER.debug("Serializing MaterializedFile path=%s", self.path)
        return {
            "path": str(self.path),
            "source_action_id": self.source_action_id,
            "role": self.role,
            "layout_metadata": dict(self.layout_metadata),
        }


# ----------------------------------------------------------------------
# Manifest (collision-free contract)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class MaterializationManifest:
    """
    Declarative manifest describing a fully materialized target package.

    This object is the *authoritative contract* between materialization
    and execution.

    Invariants guaranteed by this model:
    - All target paths are resolved and absolute
    - No duplicate target paths exist
    - Every file is intentional and traceable
    """

    target_root: Path
    files: List[MaterializedFile]
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Enforce collision-free and structurally valid manifests.
        """
        LOGGER.debug(
            "Validating MaterializationManifest target_root=%s files=%d",
            self.target_root,
            len(self.files),
        )

        seen: Set[Path] = set()

        for file in self.files:
            if not file.path.is_absolute():
                raise ValueError(
                    f"MaterializedFile path must be absolute: {file.path}"
                )

            if self.target_root not in file.path.parents:
                raise ValueError(
                    f"File path {file.path} is not under target_root {self.target_root}"
                )

            resolved = file.path.resolve()
            if resolved in seen:
                raise ValueError(
                    f"Duplicate materialized target path detected: {resolved}"
                )

            seen.add(resolved)

        LOGGER.info(
            "MaterializationManifest validated: %d files, collision-free",
            len(self.files),
        )

    def iter_files(self) -> Iterable[MaterializedFile]:
        """
        Iterate over materialized files.

        :return: Iterable of MaterializedFile.
        """
        return iter(self.files)

    def to_dict(self) -> Dict[str, object]:
        """
        Serialize the materialization manifest.

        :return: JSON-safe dictionary.
        """
        LOGGER.info(
            "Serializing MaterializationManifest target_root=%s files=%d",
            self.target_root,
            len(self.files),
        )
        return {
            "target_root": str(self.target_root),
            "files": [f.to_dict() for f in self.files],
            "metadata": dict(self.metadata),
        }


__all__ = [
    "MaterializedFile",
    "MaterializationManifest",
]