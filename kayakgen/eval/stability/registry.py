"""Accepted-fit registry loader and acceptance gates (RFC 0043 stage 4).

This module is the **load-bearing safety surface** for the high-angle GZ
claim-state flip. The threat-model design review (workflow 0043) established
the central invariant it enforces:

    The presence of an accepted measured-stability fixture is NECESSARY but
    NOT SUFFICIENT to flip the analytical high-angle GZ claim label. The flip
    requires the full provenance chain — an immutable fixture *manifest*, a
    separate hash-bound *acceptance record* (the persisted promotion packet),
    and a strict-accepted *StabilityFitRecord* whose analytical evaluator
    version matches the runtime and whose hull-family scope covers the hull.

``load_stability_fit_registry`` walks ``data/stability/fits/*.json`` and, for
each candidate :class:`StabilityFitRecord`, runs the thirteen acceptance gates
below against the fit's cited fixture manifest + co-located promotion packet.
A fit that fails any gate is dropped from the registry and the reason recorded
in a diagnostic side-channel; only gate-passing fits reach
``resolve_analytical_claim_label`` and can flip a label.

The gates deliberately re-check evidence the ``MeasuredStabilityFixture`` /
``StabilityFixturePromotionPacket`` / ``StabilityFitRecord`` schema validators
do NOT gate (smoothness failures, on-disk trace resolution, self-declared
bound widths against operator-controlled maxima, rights redistribution,
post-sign byte tampering). Schema validity is necessary; the loader is the
acceptance authority. See DESIGN_SYNTHESIS.md §B for the full rationale.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from kayakgen.eval.calibration.rights import RightsChecklist  # noqa: F401  (documents the rights surface)
from kayakgen.eval.stability.accepted_fit import (
    FixtureRef,
    StabilityFitRecord,
    StabilityFixturePromotionPacket,
)
from kayakgen.eval.stability.measured_fixture import MeasuredStabilityFixture

# ---------------------------------------------------------------------------
# Structured rejection-code constants (one per gate)
# ---------------------------------------------------------------------------

REASON_FIXTURE_MANIFEST_MISSING: Final[str] = "fixture_manifest_missing"
REASON_FIXTURE_SMOOTHNESS_FAILURES: Final[str] = "fixture_smoothness_failures_nonempty"
REASON_FIXTURE_TRACE_PATH_UNRESOLVED: Final[str] = "fixture_trace_path_unresolved"
REASON_FIXTURE_BOUNDS_TOO_LOOSE: Final[str] = "fixture_declared_bounds_exceed_operator_maxima"
REASON_FIXTURE_RIGHTS_NOT_REDISTRIBUTABLE: Final[str] = "fixture_rights_redistribution_not_authorized"
REASON_PROMOTION_PACKET_MISSING: Final[str] = "promotion_packet_missing"
REASON_FIXTURE_SHA256_MISMATCH: Final[str] = "fixture_sha256_mismatch"
REASON_FIXTURE_NOT_PROMOTED: Final[str] = "fixture_not_promoted"
REASON_PROMOTION_PACKET_REVIEW_INCOMPLETE: Final[str] = "promotion_packet_review_incomplete"
REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE: Final[str] = "fit_record_does_not_cite_fixture"
REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH: Final[str] = "fit_hull_class_fixture_mismatch"
REASON_VALID_HEEL_RANGE_DISJOINT: Final[str] = "valid_heel_range_disjoint"
REASON_EVALUATOR_VERSION_MISMATCH: Final[str] = "evaluator_version_mismatch"
REASON_STRICT_CHECK_SKIPPED: Final[str] = "strict_check_skipped_blocks_acceptance"
REASON_FIT_METRICS_OUT_OF_THRESHOLDS: Final[str] = "stability_fit_metrics_outside_default_thresholds"
REASON_FIT_RECORD_UNREADABLE: Final[str] = "fit_record_unreadable"

# Operator-controlled maxima — these live OUTSIDE the manifest under review so a
# self-authored manifest cannot widen its own acceptance bounds (the §B.3a/3b
# threat-model hardening).
OPERATOR_MAX_CALIBRATION_DRIFT_BOUND_FRACTION: Final[float] = 0.005
OPERATOR_MAX_HYSTERESIS_BOUND_FRACTION: Final[float] = 0.03

REASON_NEXT_ACTION: Final[Mapping[str, str]] = {
    REASON_FIXTURE_MANIFEST_MISSING: "run `kayakgen stability ingest-rig-run` first.",
    REASON_FIXTURE_SMOOTHNESS_FAILURES: "re-run the sweep with smoother heel actuation.",
    REASON_FIXTURE_TRACE_PATH_UNRESOLVED: "correct the manifest's trace paths or stage the files.",
    REASON_FIXTURE_BOUNDS_TOO_LOOSE: "tighten the bound or escalate the operator threshold via RFC.",
    REASON_FIXTURE_RIGHTS_NOT_REDISTRIBUTABLE: "resolve rights with the source author.",
    REASON_PROMOTION_PACKET_MISSING: "run `kayakgen stability promote-fixture --packet` first.",
    REASON_FIXTURE_SHA256_MISMATCH: "re-ingest if the manifest changed intentionally, else re-sign the packet against the new bytes.",
    REASON_FIXTURE_NOT_PROMOTED: "packet's promotion_target is not measured_stability_fixture; revise and re-sign.",
    REASON_PROMOTION_PACKET_REVIEW_INCOMPLETE: "one of the five required reviews is not accepted; re-sign.",
    REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE: "pass `--fixture-id` matching a fixtures[].fixture_id and re-run accept-fit.",
    REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH: "the fit's hull_family_scope.hull_class must equal the fixture's hull_identity.hull_class; re-fit with the matching hull class.",
    REASON_VALID_HEEL_RANGE_DISJOINT: "re-fit on a heel range covering both fixture and fit.",
    REASON_EVALUATOR_VERSION_MISMATCH: "runtime evaluator changed; re-run accept-fit to record the new version.",
    REASON_STRICT_CHECK_SKIPPED: "re-fit with strict=True.",
    REASON_FIT_METRICS_OUT_OF_THRESHOLDS: "tighten the fit, or accept with strict=False for inspection only.",
    REASON_FIT_RECORD_UNREADABLE: "the fit JSON does not parse as a StabilityFitRecord; regenerate it.",
}


@dataclass(frozen=True, slots=True)
class FitRejectionDiagnostic:
    """One dropped fit + the gate it failed."""

    fit_id: str
    fit_path: Path
    reason_code: str
    detail: str


# ---------------------------------------------------------------------------
# Canonical hashing
# ---------------------------------------------------------------------------


def fixture_canonical_sha256(fixture: MeasuredStabilityFixture) -> str:
    """SHA-256 over the fixture's canonical JSON bytes.

    The canonical form is Pydantic's deterministic ``model_dump_json``; the
    ``ingest-rig-run`` writer and ``promote-fixture`` hasher use this same
    helper so a ``fixture_sha256`` in a promotion packet hash-binds to the
    exact on-disk manifest bytes.
    """

    return hashlib.sha256(fixture.model_dump_json().encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _fits_root(root: str | os.PathLike[str] | None) -> Path:
    if root is not None:
        return Path(root).expanduser()
    env = os.environ.get("KAYAKGEN_STABILITY_FITS_ROOT")
    if env:
        return Path(env).expanduser()
    return Path("data/stability/fits")


def _fixtures_root(fits_root: Path) -> Path:
    """The fixtures tree is the ``fixtures`` sibling of the ``fits`` tree.

    ``data/stability/fits`` ↔ ``data/stability/fixtures``. An explicit
    ``KAYAKGEN_STABILITY_FIXTURES_ROOT`` env overrides for split layouts.
    """

    env = os.environ.get("KAYAKGEN_STABILITY_FIXTURES_ROOT")
    if env:
        return Path(env).expanduser()
    return fits_root.parent / "fixtures"


# ---------------------------------------------------------------------------
# The thirteen gates
# ---------------------------------------------------------------------------


def _heel_ranges_overlap(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return max(a[0], b[0]) <= min(a[1], b[1])


def _evaluate_fit_gates(
    fit: StabilityFitRecord,
    fixtures_root: Path,
    runtime_evaluator_version: str,
) -> tuple[bool, str, str]:
    """Run the gate sequence for one fit. Returns ``(passed, reason, detail)``.

    Gate order short-circuits on first failure. ``reason`` is one of the
    ``REASON_*`` constants when ``passed`` is False, otherwise ``""``.
    """

    # The fit must cite at least one fixture (schema guarantees min_length=1).
    # We try each cited fixture; the fit passes if ANY cited fixture clears the
    # full chain (a fit could legitimately cite several fixtures). The reason
    # reported is from the last-tried fixture.
    last_reason = REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE
    last_detail = "fit cites no resolvable promoted fixture"

    for ref in fit.fixtures:
        ok, reason, detail = _evaluate_single_fixture_chain(
            fit, ref, fixtures_root, runtime_evaluator_version
        )
        if ok:
            return True, "", ""
        last_reason, last_detail = reason, detail

    return False, last_reason, last_detail


def _evaluate_single_fixture_chain(
    fit: StabilityFitRecord,
    ref: FixtureRef,
    fixtures_root: Path,
    runtime_evaluator_version: str,
) -> tuple[bool, str, str]:
    fixture_dir = fixtures_root / ref.fixture_id
    manifest_path = fixture_dir / "manifest.json"
    promotion_path = fixture_dir / "promotion.json"

    # Gate 1: manifest exists + parses.
    if not manifest_path.is_file():
        return False, REASON_FIXTURE_MANIFEST_MISSING, f"no manifest at {manifest_path}"
    try:
        manifest = MeasuredStabilityFixture.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except (ValidationError, ValueError, OSError) as exc:
        return False, REASON_FIXTURE_MANIFEST_MISSING, f"manifest unparseable: {exc}"

    # Gate 2: smoothness-failures empty.
    if manifest.free_equilibrium_trace.smoothness_failures:
        return (
            False,
            REASON_FIXTURE_SMOOTHNESS_FAILURES,
            f"smoothness_failures={manifest.free_equilibrium_trace.smoothness_failures}",
        )

    # Gate 3: trace paths + runs_dir resolve on disk (relative to the fixture dir).
    for label, raw in (
        ("pre_run_trace_path", manifest.calibration_trace.pre_run_trace_path),
        ("post_run_trace_path", manifest.calibration_trace.post_run_trace_path),
    ):
        if not _resolve_evidence(fixture_dir, raw).is_file():
            return False, REASON_FIXTURE_TRACE_PATH_UNRESOLVED, f"{label} -> {raw}"
    if manifest.runs_dir is not None and not _resolve_evidence(fixture_dir, manifest.runs_dir).is_dir():
        return False, REASON_FIXTURE_TRACE_PATH_UNRESOLVED, f"runs_dir -> {manifest.runs_dir}"

    # Gate 3a: self-declared bounds within operator-controlled maxima.
    if manifest.calibration_trace.drift_bound_fraction > OPERATOR_MAX_CALIBRATION_DRIFT_BOUND_FRACTION:
        return (
            False,
            REASON_FIXTURE_BOUNDS_TOO_LOOSE,
            f"drift_bound_fraction={manifest.calibration_trace.drift_bound_fraction} "
            f"> operator max {OPERATOR_MAX_CALIBRATION_DRIFT_BOUND_FRACTION}",
        )
    if manifest.hysteresis_bound.bound_fraction > OPERATOR_MAX_HYSTERESIS_BOUND_FRACTION:
        return (
            False,
            REASON_FIXTURE_BOUNDS_TOO_LOOSE,
            f"hysteresis bound_fraction={manifest.hysteresis_bound.bound_fraction} "
            f"> operator max {OPERATOR_MAX_HYSTERESIS_BOUND_FRACTION}",
        )

    # Gate 3b: rights redistribution authorized.
    if not manifest.rights.redistribution_authorized:
        return (
            False,
            REASON_FIXTURE_RIGHTS_NOT_REDISTRIBUTABLE,
            "manifest.rights.redistribution_authorized is False",
        )

    # Gate 4: promotion packet exists + parses.
    if not promotion_path.is_file():
        return False, REASON_PROMOTION_PACKET_MISSING, f"no promotion.json at {promotion_path}"
    try:
        packet = StabilityFixturePromotionPacket.model_validate_json(
            promotion_path.read_text(encoding="utf-8")
        )
    except (ValidationError, ValueError, OSError) as exc:
        return False, REASON_PROMOTION_PACKET_MISSING, f"promotion.json unparseable: {exc}"

    # Gate 5: packet hash-binds the on-disk manifest bytes.
    manifest_sha = fixture_canonical_sha256(manifest)
    if packet.fixture_ref.fixture_sha256 != manifest_sha:
        return (
            False,
            REASON_FIXTURE_SHA256_MISMATCH,
            f"packet sha={packet.fixture_ref.fixture_sha256} != manifest sha={manifest_sha}",
        )

    # Gate 6: promotion_target is measured_stability_fixture.
    if packet.promotion_target != "measured_stability_fixture":
        return False, REASON_FIXTURE_NOT_PROMOTED, f"promotion_target={packet.promotion_target}"

    # Gate 7: all five reviews accepted + rig_design_match + no rejection reasons.
    reviews = (
        packet.rights_review,
        packet.hull_identity_review,
        packet.calibration_drift_review,
        packet.hysteresis_review,
        packet.free_equilibrium_review,
    )
    if any(v != "accepted" for v in reviews) or not packet.rig_design_match or packet.rejection_reasons:
        return (
            False,
            REASON_PROMOTION_PACKET_REVIEW_INCOMPLETE,
            f"reviews={reviews} rig_design_match={packet.rig_design_match} "
            f"rejection_reasons={packet.rejection_reasons}",
        )

    # Gate 8: the fit cites THIS fixture by id AND sha (re-bind to manifest bytes).
    if ref.fixture_id != manifest.fixture_id or ref.fixture_sha256 != manifest_sha:
        return (
            False,
            REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE,
            f"fit ref ({ref.fixture_id},{ref.fixture_sha256[:8]}) != "
            f"manifest ({manifest.fixture_id},{manifest_sha[:8]})",
        )

    # Gate 8a: the fit's hull-family scope is bound to the fixture's measured
    # hull identity. Without this, a strict accepted fit anchored to a sea_kayak
    # fixture could declare hull_family_scope.hull_class="sprint_k1" and a
    # sprint hull's design hash, and the resolver would flip a sprint hull
    # against a sea-kayak measurement — exactly the over-broad cross-class path
    # the threat-model review surfaced. Equality is the minimum binding; a
    # successor RFC may relax it with an explicit cross-family-scope review
    # artifact.
    if fit.hull_family_scope.hull_class != manifest.hull_identity.hull_class:
        return (
            False,
            REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH,
            f"fit hull_family_scope.hull_class={fit.hull_family_scope.hull_class!r} "
            f"!= fixture hull_identity.hull_class={manifest.hull_identity.hull_class!r}",
        )

    # Gate 9: heel-range overlap.
    if not _heel_ranges_overlap(fit.valid_heel_range_deg, manifest.valid_heel_range_deg):
        return (
            False,
            REASON_VALID_HEEL_RANGE_DISJOINT,
            f"fit {fit.valid_heel_range_deg} vs fixture {manifest.valid_heel_range_deg}",
        )

    # Gate 10: evaluator-version match.
    if fit.analytical_evaluator_version != runtime_evaluator_version:
        return (
            False,
            REASON_EVALUATOR_VERSION_MISMATCH,
            f"fit version {fit.analytical_evaluator_version} != runtime {runtime_evaluator_version}",
        )

    # Gate 11: strict acceptance. (Metric thresholds are enforced at construction
    # for strict records; a strict=False record never carries an accepted flip.)
    if not fit.strict:
        return False, REASON_STRICT_CHECK_SKIPPED, "strict=False record cannot back a flip"
    if fit.acceptance_verdict != "accepted":
        return (
            False,
            REASON_FIT_METRICS_OUT_OF_THRESHOLDS,
            f"acceptance_verdict={fit.acceptance_verdict}",
        )

    return True, "", ""


def _resolve_evidence(fixture_dir: Path, raw: str) -> Path:
    """Resolve an evidence path: absolute as-is, else relative to the fixture dir."""

    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate
    return fixture_dir / candidate


# ---------------------------------------------------------------------------
# Registry loader (memoized by fits-root mtime)
# ---------------------------------------------------------------------------

_REGISTRY_CACHE: dict[
    tuple[str, int, int, str], tuple[StabilityFitRecord, ...]
] = {}


def load_stability_fit_registry(
    root: str | os.PathLike[str] | None = None,
    *,
    with_diagnostics: bool = False,
    runtime_evaluator_version: str | None = None,
) -> (
    tuple[StabilityFitRecord, ...]
    | tuple[tuple[StabilityFitRecord, ...], tuple[FitRejectionDiagnostic, ...]]
):
    """Load gate-passing accepted stability fits.

    Walks ``<root>/*.json`` (default ``data/stability/fits``), parses each as a
    :class:`StabilityFitRecord`, and runs the §B gate sequence against the cited
    fixture's manifest + promotion packet. Returns gate-passing fits sorted by
    ``fit_id``. With ``with_diagnostics=True`` returns ``(fits, diagnostics)``.

    Memoized on ``(resolved_root, directory_mtime_ns)`` so an operator who runs
    ``promote-fixture`` / ``accept-fit`` mid-session sees the new state on the
    next load without a process restart, while repeated reads in a stable tree
    are cheap. ``with_diagnostics`` reads bypass the cache (they re-scan to
    rebuild the diagnostic side-channel).
    """

    from kayakgen.eval.stability.evaluator import ANALYTICAL_EVALUATOR_VERSION

    version = runtime_evaluator_version or ANALYTICAL_EVALUATOR_VERSION
    fits_root = _fits_root(root)
    fixtures_root = _fixtures_root(fits_root)

    if not fits_root.is_dir():
        return ((), ()) if with_diagnostics else ()

    # Gate 10 (evaluator-version match) depends on ``version`` — the cache key
    # MUST include it, or a second load under a stale runtime version would
    # return a tuple cached under the matching version and silently bypass the
    # version gate. (Threat-model review, finding 2.)
    mtime_ns, entry_count = _dir_fingerprint(fits_root)
    cache_key = (str(fits_root.resolve()), mtime_ns, entry_count, version)
    if not with_diagnostics and cache_key in _REGISTRY_CACHE:
        return _REGISTRY_CACHE[cache_key]

    passing: list[StabilityFitRecord] = []
    diagnostics: list[FitRejectionDiagnostic] = []

    for fit_path in sorted(fits_root.glob("*.json")):
        try:
            fit = StabilityFitRecord.model_validate_json(fit_path.read_text(encoding="utf-8"))
        except (ValidationError, ValueError, OSError) as exc:
            diagnostics.append(
                FitRejectionDiagnostic(
                    fit_id=fit_path.stem,
                    fit_path=fit_path,
                    reason_code=REASON_FIT_RECORD_UNREADABLE,
                    detail=str(exc),
                )
            )
            continue

        ok, reason, detail = _evaluate_fit_gates(fit, fixtures_root, version)
        if ok:
            passing.append(fit)
        else:
            diagnostics.append(
                FitRejectionDiagnostic(
                    fit_id=fit.fit_id,
                    fit_path=fit_path,
                    reason_code=reason,
                    detail=detail,
                )
            )

    passing.sort(key=lambda r: r.fit_id)
    result = tuple(passing)

    if with_diagnostics:
        return result, tuple(diagnostics)

    _REGISTRY_CACHE[cache_key] = result
    return result


def _dir_fingerprint(path: Path) -> tuple[int, int]:
    """``(max_mtime_ns, entry_count)`` over the fits dir + the sibling fixtures tree.

    Walks EVERY entry (files + directories, any extension) under the fixtures
    tree, not only ``*.json``. Gate 3 trace evidence is non-JSON
    (``cal/pre.csv``, ``cal/post.csv``), so filtering to ``*.json`` would let
    a cached passing fit stay loaded after its trace evidence is deleted —
    the parent directory's mtime advances on delete, but a JSON-only filter
    never inspects it.

    Returning ``entry_count`` alongside the mtime defends against the
    sub-mtime-granularity race where a file is created and deleted within a
    single mtime tick (observed on tmpfs-backed pytest ``tmp_path`` trees):
    deleting any tracked file drops the count regardless of whether the
    parent dir's mtime managed to advance. (Threat-model review revision 1,
    P1.)
    """

    newest = path.stat().st_mtime_ns
    count = 1
    fixtures = _fixtures_root(path)
    if fixtures.is_dir():
        newest = max(newest, fixtures.stat().st_mtime_ns)
        count += 1
        for child in fixtures.rglob("*"):
            try:
                newest = max(newest, child.stat().st_mtime_ns)
                count += 1
            except OSError:
                continue
    for child in path.glob("*"):
        try:
            newest = max(newest, child.stat().st_mtime_ns)
            count += 1
        except OSError:
            continue
    return newest, count


def clear_registry_cache() -> None:
    """Drop the memoized registry (test + mid-session-refresh helper)."""

    _REGISTRY_CACHE.clear()


def registry_as_iterable(
    root: str | os.PathLike[str] | None = None,
) -> Iterable[StabilityFitRecord]:
    """Convenience accessor returning just the gate-passing fits."""

    result = load_stability_fit_registry(root)
    assert isinstance(result, tuple)
    return result


__all__ = [
    "FitRejectionDiagnostic",
    "OPERATOR_MAX_CALIBRATION_DRIFT_BOUND_FRACTION",
    "OPERATOR_MAX_HYSTERESIS_BOUND_FRACTION",
    "REASON_EVALUATOR_VERSION_MISMATCH",
    "REASON_FIT_METRICS_OUT_OF_THRESHOLDS",
    "REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH",
    "REASON_FIT_RECORD_DOES_NOT_CITE_FIXTURE",
    "REASON_FIT_RECORD_UNREADABLE",
    "REASON_FIXTURE_BOUNDS_TOO_LOOSE",
    "REASON_FIXTURE_MANIFEST_MISSING",
    "REASON_FIXTURE_NOT_PROMOTED",
    "REASON_FIXTURE_RIGHTS_NOT_REDISTRIBUTABLE",
    "REASON_FIXTURE_SHA256_MISMATCH",
    "REASON_FIXTURE_SMOOTHNESS_FAILURES",
    "REASON_FIXTURE_TRACE_PATH_UNRESOLVED",
    "REASON_NEXT_ACTION",
    "REASON_PROMOTION_PACKET_MISSING",
    "REASON_PROMOTION_PACKET_REVIEW_INCOMPLETE",
    "REASON_STRICT_CHECK_SKIPPED",
    "REASON_VALID_HEEL_RANGE_DISJOINT",
    "clear_registry_cache",
    "fixture_canonical_sha256",
    "load_stability_fit_registry",
    "registry_as_iterable",
]
