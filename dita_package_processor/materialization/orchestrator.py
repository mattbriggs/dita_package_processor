"""
orchestrator.py
===============

Materialization orchestration for the DITA Package Processor.

Materialization is a first-class pipeline phase and MUST occur before
execution. This prevents publishing unsafe or ambiguous target layouts.

This orchestrator is intentionally split into two phases:

Preflight (MANDATORY, pre-execution):
    - validate target_root readiness
    - validate layout mapping rules
    - detect collisions among planned outputs
    - emit a materialization manifest (optional, deterministic)

Finalize (post-execution):
    - validate execution results are safe for publication (optional)
    - write finalized manifest / reports (optional)

Design constraints:
- deterministic
- idempotent
- no hidden filesystem mutation
- no inference
- explicit failure on ambiguity

Pattern notes:
- Orchestrator coordinates collaborators (Builder, Validator, CollisionDetector,
  ManifestWriter). Collaborators are dependency-injected for testability and
  stability.

Key compatibility note
----------------------
The default builder (TargetMaterializationBuilder) may change its __init__
signature over time (e.g., requiring a keyword-only ``manifest``). This
orchestrator adapts via runtime signature inspection and will pass only
supported kwargs.
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Protocol

from dita_package_processor.execution.models import ExecutionReport
from dita_package_processor.materialization.builder import (
    MaterializationError,
    TargetMaterializationBuilder,
)
from dita_package_processor.materialization.collision import (
    CollisionDetector,
    MaterializationCollisionError,
    TargetArtifact,
)
from dita_package_processor.materialization.layout import LayoutError, TargetLayout
from dita_package_processor.planning.models import Plan

LOGGER = logging.getLogger(__name__)


class MaterializationOrchestrationError(RuntimeError):
    """Raised when orchestration of materialization fails."""


# ----------------------------------------------------------------------
# Protocols for dependency injection
# ----------------------------------------------------------------------


class Builder(Protocol):
    """Protocol for target filesystem readiness builders."""

    def build(self) -> None:
        """Prepare the filesystem target for materialization."""


class Validator(Protocol):
    """Protocol for materialization validators."""

    def validate_preflight(self) -> None:
        """Validate pre-execution safety invariants."""


class CollisionDetectorProtocol(Protocol):
    """Protocol for collision detection implementations."""

    def detect(self) -> None:
        """Detect collisions and raise if any are found."""


class ManifestWriter(Protocol):
    """Protocol for manifest writers."""

    def write_preflight(self) -> None:
        """Optionally write a preflight manifest artifact."""

    def write_final(self, *, execution_report: ExecutionReport) -> None:
        """Optionally write a final manifest artifact."""


# ----------------------------------------------------------------------
# Defaults
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class NoOpValidator:
    """
    Default validator that performs no validation.

    This exists so materialization can be wired before all validators are
    implemented. Replace with real validators as the safety surface grows.
    """

    def validate_preflight(self) -> None:
        """No-op validation."""
        return


@dataclass(frozen=True)
class NoOpManifestWriter:
    """
    Default manifest writer that performs no I/O.

    The system can later be extended to emit JSON manifests deterministically.
    """

    def write_preflight(self) -> None:
        """No-op."""
        return

    def write_final(self, *, execution_report: ExecutionReport) -> None:
        """No-op."""
        return


# ----------------------------------------------------------------------
# Minimal manifest model (local fallback)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class MaterializationManifest:
    """
    Deterministic materialization manifest.

    This is a conservative, minimal representation of what materialization
    needs to prepare for (resolved target paths and their origin actions).

    Parameters
    ----------
    target_root:
        Target root directory for materialization.
    artifacts:
        Concrete resolved target artifacts derived from the plan.
    """

    target_root: Path
    artifacts: List[TargetArtifact]


# ----------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------


class MaterializationOrchestrator:
    """
    Coordinate the materialization layer.

    This orchestrator is a strict coordinator: it does not implement mapping
    logic or collision semantics itself. It delegates those concerns to
    collaborators.

    Parameters
    ----------
    plan:
        Immutable plan that will be executed.
    target_root:
        Target directory where the materialized package will live.
    builder:
        Prepares filesystem destination. If omitted, a compatible default
        TargetMaterializationBuilder is created using a derived manifest.
    validator:
        Preflight validator. Defaults to NoOpValidator.
    collision_detector:
        Detects collisions among resolved target artifacts. Defaults to a
        CollisionDetector built from derived target artifacts.
    manifest_writer:
        Optional manifest writer. Defaults to NoOpManifestWriter.
    """

    def __init__(
        self,
        *,
        plan: Plan,
        target_root: Path,
        builder: Optional[Builder] = None,
        validator: Optional[Validator] = None,
        collision_detector: Optional[CollisionDetectorProtocol] = None,
        manifest_writer: Optional[ManifestWriter] = None,
    ) -> None:
        self.plan = plan
        self.target_root = target_root.resolve()

        self.validator: Validator = validator or NoOpValidator()
        self.manifest_writer: ManifestWriter = manifest_writer or NoOpManifestWriter()

        # Derive concrete artifacts once. This is deterministic and used for both
        # collision detection and manifest construction.
        self._derived_artifacts: List[TargetArtifact] = self._derive_target_artifacts()

        # Build a manifest now (deterministic, no I/O).
        self.manifest = self._build_manifest()

        # Builder may require a manifest kwarg. If caller did not inject one,
        # create a compatible default builder.
        self.builder: Builder = builder or self._make_default_builder()

        # Collision detector may depend on resolved artifacts.
        if collision_detector is None:
            self.collision_detector = CollisionDetector(artifacts=self._derived_artifacts)
        else:
            self.collision_detector = collision_detector

        LOGGER.debug(
            "MaterializationOrchestrator initialized: target_root=%s actions=%d "
            "derived_artifacts=%d builder=%s collision_detector=%s validator=%s "
            "manifest_writer=%s",
            self.target_root,
            len(getattr(self.plan, "actions", [])),
            len(self._derived_artifacts),
            type(self.builder).__name__,
            type(self.collision_detector).__name__,
            type(self.validator).__name__,
            type(self.manifest_writer).__name__,
        )

    # ------------------------------------------------------------------
    # Phase 1: Preflight (MANDATORY)
    # ------------------------------------------------------------------

    def preflight(self) -> None:
        """
        Execute the pre-execution materialization safety gate.

        This MUST run before execution. If this fails, execution must not run.

        Raises
        ------
        MaterializationOrchestrationError
            If any preflight stage fails.
        """
        LOGGER.info("MATERIALIZATION PREFLIGHT START target_root=%s", self.target_root)
        LOGGER.debug(
            "Preflight inputs: actions=%d derived_artifacts=%d",
            len(getattr(self.plan, "actions", [])),
            len(self._derived_artifacts),
        )

        try:
            # 1) Prepare filesystem destination (no content mutation).
            LOGGER.debug("Preflight step: builder.build() using %s", type(self.builder).__name__)
            self.builder.build()

            # 2) Validate semantic preflight invariants (optional extension point).
            LOGGER.debug("Preflight step: validator.validate_preflight() using %s", type(self.validator).__name__)
            self.validator.validate_preflight()

            # 3) Detect collisions among planned outputs.
            LOGGER.debug(
                "Preflight step: collision_detector.detect() using %s (artifacts=%d)",
                type(self.collision_detector).__name__,
                len(self._derived_artifacts),
            )
            self.collision_detector.detect()

            # 4) Optional manifest emission (deterministic, safe).
            LOGGER.debug("Preflight step: manifest_writer.write_preflight() using %s", type(self.manifest_writer).__name__)
            self.manifest_writer.write_preflight()

        except (
            MaterializationError,
            MaterializationCollisionError,
            LayoutError,
            ValueError,
            TypeError,
        ) as exc:
            LOGGER.error("MATERIALIZATION PREFLIGHT FAILED: %s", exc, exc_info=True)
            raise MaterializationOrchestrationError(str(exc)) from exc

        LOGGER.info("MATERIALIZATION PREFLIGHT COMPLETE")

    # ------------------------------------------------------------------
    # Phase 2: Finalize (POST-EXECUTION)
    # ------------------------------------------------------------------

    def finalize(self, *, execution_report: ExecutionReport) -> None:
        """
        Finalize materialization after execution completes.

        This is a post-execution hook. It may write manifests or perform
        additional publication-safety checks based on execution outcomes.

        Parameters
        ----------
        execution_report:
            Immutable forensic execution report.

        Raises
        ------
        MaterializationOrchestrationError
            If finalization fails.
        """
        LOGGER.info("MATERIALIZATION FINALIZE START")
        LOGGER.debug(
            "Finalize inputs: execution_id=%s results=%d",
            getattr(execution_report, "execution_id", "<unknown>"),
            len(getattr(execution_report, "results", [])),
        )

        try:
            self.manifest_writer.write_final(execution_report=execution_report)
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("MATERIALIZATION FINALIZE FAILED: %s", exc, exc_info=True)
            raise MaterializationOrchestrationError(str(exc)) from exc

        LOGGER.info("MATERIALIZATION FINALIZE COMPLETE")

    # ------------------------------------------------------------------
    # Internal: manifest + builder wiring
    # ------------------------------------------------------------------

    def _build_manifest(self) -> Any:
        """
        Build a deterministic materialization manifest.

        If a first-party manifest class exists in the codebase, it can be used.
        Otherwise, this falls back to a local minimal MaterializationManifest.

        Returns
        -------
        Any
            A manifest object suitable for passing to the builder.
        """
        # Try to use a project-native manifest model if it exists, without
        # hard depending on its location/name.
        candidates = [
            ("dita_package_processor.materialization.manifest", "MaterializationManifest"),
            ("dita_package_processor.materialization.models", "MaterializationManifest"),
            ("dita_package_processor.materialization.manifest", "Manifest"),
            ("dita_package_processor.materialization.models", "Manifest"),
        ]

        for module_name, symbol_name in candidates:
            try:
                module = __import__(module_name, fromlist=[symbol_name])
                cls = getattr(module, symbol_name)
                LOGGER.debug("Using manifest class %s.%s", module_name, symbol_name)
                return cls(target_root=self.target_root, artifacts=self._derived_artifacts)
            except Exception:  # noqa: BLE001
                continue

        LOGGER.debug("Using local fallback MaterializationManifest")
        return MaterializationManifest(
            target_root=self.target_root,
            artifacts=self._derived_artifacts,
        )

    def _make_default_builder(self) -> Builder:
        """
        Instantiate a compatible TargetMaterializationBuilder.

        The builder's constructor signature may evolve (e.g., requiring a
        keyword-only ``manifest``). This method inspects the signature and
        passes only supported keyword arguments.

        Returns
        -------
        Builder
            A constructed TargetMaterializationBuilder instance.

        Raises
        ------
        TypeError
            If the builder cannot be constructed with any supported args.
        """
        builder_cls = TargetMaterializationBuilder
        sig = inspect.signature(builder_cls)

        kwargs: dict[str, object] = {}

        # Only provide kwargs that the constructor actually supports.
        if "manifest" in sig.parameters:
            kwargs["manifest"] = self.manifest
        if "target_root" in sig.parameters:
            kwargs["target_root"] = self.target_root
        if "plan" in sig.parameters:
            kwargs["plan"] = self.plan

        LOGGER.debug(
            "Constructing %s with kwargs=%s (signature=%s)",
            builder_cls.__name__,
            sorted(kwargs.keys()),
            sig,
        )

        try:
            builder = builder_cls(**kwargs)  # type: ignore[arg-type]
        except TypeError as exc:
            # Give extremely actionable logging.
            LOGGER.error(
                "Failed to construct %s with kwargs=%s. "
                "Constructor signature=%s. Error=%s",
                builder_cls.__name__,
                kwargs,
                sig,
                exc,
                exc_info=True,
            )
            raise

        LOGGER.info(
            "Materialization builder selected: %s (kwargs=%s)",
            type(builder).__name__,
            sorted(kwargs.keys()),
        )
        return builder

    # ------------------------------------------------------------------
    # Internal: derive resolved target artifacts
    # ------------------------------------------------------------------

    def _derive_target_artifacts(self) -> List[TargetArtifact]:
        """
        Derive concrete target artifacts from the plan.

        This is intentionally conservative and deterministic: it derives
        target paths from explicit plan action targets only.

        Returns
        -------
        list[TargetArtifact]
            Resolved target artifacts for collision detection.

        Notes
        -----
        If an action target is absolute, it is used as-is.
        If an action target is relative, it is resolved via TargetLayout.
        """
        layout = TargetLayout(target_root=self.target_root)

        artifacts: List[TargetArtifact] = []
        actions = getattr(self.plan, "actions", [])

        for action in actions:
            target_raw = Path(str(action.target))

            if target_raw.is_absolute():
                resolved = target_raw
                LOGGER.debug(
                    "Action target is absolute; using as-is: action_id=%s target=%s",
                    action.id,
                    resolved,
                )
            else:
                resolved = layout.resolve(rel_path=target_raw)
                LOGGER.debug(
                    "Resolved relative target: action_id=%s rel=%s resolved=%s",
                    action.id,
                    target_raw,
                    resolved,
                )

            artifacts.append(
                TargetArtifact(
                    path=resolved,
                    source_action_id=action.id,
                )
            )

        LOGGER.debug(
            "Derived %d target artifacts for collision detection (target_root=%s)",
            len(artifacts),
            self.target_root,
        )
        return artifacts


__all__ = [
    "MaterializationOrchestrator",
    "MaterializationOrchestrationError",
]