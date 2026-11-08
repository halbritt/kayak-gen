"""Run selected shared-input regressions before a complete release gate."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
import uuid
from xml.etree import ElementTree


@dataclass(frozen=True)
class ContractChecks:
    id: str
    shared_inputs: tuple[str, ...]
    producers: tuple[str, ...]
    consumers: tuple[str, ...]
    pytest_targets: tuple[str, ...]
    watched_paths: tuple[str, ...]


CONTRACTS = (
    ContractChecks(
        "operating-inputs",
        ("load and CG", "fluid", "exact speeds", "operating intent", "budget forwarding"),
        ("kayakgen/services/evaluation.py", "kayakgen/search/sweep.py", "kayakgen/cli/main.py"),
        ("kayakgen/search/compare.py", "kayakgen/search/active/runner.py",
         "kayakgen/services/design_report.py", "kayakgen/ui/web/handlers.py"),
        ("tests/test_operating_comparison.py", "tests/test_evaluation_context.py"),
        ("kayakgen/eval/contract.py", "kayakgen/eval/hydrostatics.py",
         "kayakgen/eval/stability/*", "kayakgen/model/operating_state.py",
         "kayakgen/services/evaluation.py", "kayakgen/services/design_report.py",
         "kayakgen/io/json.py", "kayakgen/eval/immersed_geometry.py", "kayakgen/search/sweep*",
         "kayakgen/ui/web/handlers.py", "kayakgen/ui/web/state.py", "kayakgen/ui/desktop.py",
         "kayakgen/search/compare.py", "kayakgen/search/active/*", "kayakgen/cli/main.py",
         "tests/test_operating_comparison.py", "tests/test_evaluation_context.py",
         "docs/research/rfc0077/context-integration/*"),
    ),
    ContractChecks(
        "recorded-methods",
        ("recorded method versions", "saved context and curve identity", "legacy missing metadata"),
        ("kayakgen/eval/contract.py", "kayakgen/eval/resistance.py"),
        ("kayakgen/io/json.py", "kayakgen/services/design_report.py",
         "kayakgen/search/compare.py"),
        ("tests/test_recorded_method_binding.py",),
        ("kayakgen/eval/contract.py", "kayakgen/eval/resistance.py",
         "kayakgen/eval/numerical_resistance.py", "kayakgen/eval/michell_quadrature.py",
         "kayakgen/io/json.py", "kayakgen/services/design_report.py", "kayakgen/cli/main.py",
         "tests/test_recorded_method_binding.py"),
    ),
    ContractChecks(
        "numerical-admission",
        ("exact speeds and Fn", "method and policy versions", "declared numerical budget",
         "wave and viscous uncertainty contributions", "comparison operating inputs"),
        ("kayakgen/eval/resistance.py", "kayakgen/eval/numerical_resistance.py"),
        ("kayakgen/eval/contract.py", "kayakgen/search/pareto.py",
         "kayakgen/search/compare.py", "kayakgen/search/active/runner.py"),
        ("tests/test_resistance_assessment.py", "tests/test_resistance_intervals.py",
         "tests/test_numerical_admission.py"),
        ("kayakgen/eval/contract.py", "kayakgen/eval/resistance.py",
         "kayakgen/eval/numerical*", "kayakgen/eval/michell_quadrature.py",
         "kayakgen/search/pareto.py", "kayakgen/search/compare.py",
         "kayakgen/search/active/*", "kayakgen/cli/main.py",
         "tests/test_resistance_assessment.py", "tests/test_resistance_intervals.py",
         "tests/test_numerical_admission.py", "tests/numerical_test_cases.py",
         "tests/fixtures/numerical/*", "docs/research/rfc0077/closure/*"),
    ),
    ContractChecks(
        "presentation",
        ("actual sampled speed", "off-grid view target", "explicit grid preservation"),
        ("kayakgen/services/evaluation.py",),
        ("kayakgen/ui/web/handlers.py", "kayakgen/ui/desktop.py",
         "kayakgen/services/design_report.py"),
        ("tests/test_web_speed_context.py", "tests/test_evaluation_context.py"),
        ("kayakgen/eval/contract.py", "kayakgen/services/evaluation.py",
         "kayakgen/services/design_report.py", "kayakgen/ui/web/handlers.py",
         "kayakgen/ui/web/read_models.py", "kayakgen/ui/web/state.py",
         "kayakgen/ui/desktop.py", "kayakgen/cli/main.py",
         "tests/test_web_speed_context.py"),
    ),
)


def preflight_plan(changed_paths: list[str], contracts: list[str]) -> dict:
    """Describe selected owned contracts, their existing checks and consumers."""
    known = {contract.id for contract in CONTRACTS}
    unknown = set(contracts) - known
    if unknown:
        raise ValueError("unknown semantic contracts: " + ", ".join(sorted(unknown)))
    normalized = []
    for name in changed_paths:
        path = PurePosixPath(name)
        if not path.parts or path.is_absolute() or ".." in path.parts or "\0" in name:
            raise ValueError("changed paths must be repository-relative: " + repr(name))
        normalized.append(str(path))
    selected = [
        contract for contract in CONTRACTS
        if contract.id in contracts or "kayakgen/operations/semantic_preflight.py" in normalized or any(
            fnmatchcase(path, watched) for path in normalized for watched in contract.watched_paths
        )
    ]
    return {
        "changed_paths": sorted(set(normalized)),
        "unmapped_paths": sorted({
            path for path in normalized
            if path != "kayakgen/operations/semantic_preflight.py"
            and not any(fnmatchcase(path, watched) for c in CONTRACTS for watched in c.watched_paths)
        }),
        "explicit_contracts": sorted(set(contracts)),
        "contracts": [asdict(contract) for contract in selected],
        "pytest_targets": sorted({target for contract in selected for target in contract.pytest_targets}),
        "operating_oracle_required": any(c.id == "operating-inputs" for c in selected),
        "full_release_gate_required": True,
        "scientific_claim_promotion": False,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _execute(command: dict, root: Path, out: Path) -> int:
    from kayakgen.operations.gate import GateInterrupted, _terminate_owned

    log = out / (command["name"] + ".log")
    env = {**os.environ, "PYTHONPATH": str(root)}
    for name in ("PYTEST_ADDOPTS", "KAYAKGEN_ENFORCE_SKIP_PIN", "KAYAKGEN_EXPECTED_SKIPS"):
        env.pop(name, None)
    command.update(status="running", started_at=_now(), log_path=str(log))
    started = time.monotonic()
    try:
        with log.open("w", encoding="utf-8") as stream:
            with subprocess.Popen(command["argv"], cwd=root, env=env, stdout=stream,
                                  stderr=subprocess.STDOUT, start_new_session=True) as child:
                try:
                    code = child.wait(timeout=900)
                except subprocess.TimeoutExpired:
                    _terminate_owned(child)
                    command.update(status="timed_out", exit_code=124)
                    return 124
                except BaseException:
                    _terminate_owned(child)
                    raise
        command.update(status="passed" if code == 0 else "failed", exit_code=code)
        return code if code >= 0 else 128 - code
    except GateInterrupted:
        command.update(status="interrupted", exit_code=None)
        raise
    finally:
        command.update(finished_at=_now(), seconds=time.monotonic() - started)
        if log.exists():
            command["log_sha256"] = _sha256(log)


def _pytest_checks(root: Path, out: Path, receipt: dict) -> None:
    from kayakgen.operations.gate import SUMMARY

    junit = out / "pytest.xml"
    command = {"name": "pytest", "argv": [sys.executable, "-m", "pytest", "-q",
               "-o", "addopts=", "--junitxml", str(junit), *receipt["pytest_targets"]]}
    receipt["commands"].append(command)
    _require(_execute(command, root, out) == 0, "selected pytest command failed")
    suite = ElementTree.parse(junit).getroot()
    cases = list(suite.iter("testcase"))
    _require(bool(cases), "selected pytest produced no executed cases")
    _require(not any(case.find(tag) is not None for case in cases
                     for tag in ("failure", "error", "skipped")),
             "selected pytest cases failed, errored or skipped")
    text = Path(command["log_path"]).read_text(encoding="utf-8")
    summaries = [line.strip() for line in text.splitlines() if SUMMARY.match(line.strip())]
    _require(bool(summaries), "selected pytest produced no terminal summary")
    _require(re.search(r"(?:^|, )[1-9][0-9]* deselected", summaries[-1]) is None,
             "selected pytest deselected required cases")
    receipt["pytest_result"] = {"executed_cases": len(cases), "skipped": 0,
                                "summary": summaries[-1], "junit_sha256": _sha256(junit)}


def _operating_oracle(root: Path, out: Path, receipt: dict) -> None:
    retained = root / "docs/research/rfc0077"
    script = retained / "context-integration/operating-comparison-oracle.py.txt"
    target = out / "operating-oracle"
    command = {"name": "operating-oracle", "argv": [sys.executable, str(script),
               "--integration", "--out", str(target), "--cached-curves", str(retained / "closure"),
               "--study", str(retained / "context-integration/study")]}
    receipt["commands"].append(command)
    _require(_execute(command, root, out) == 0, "retained operating oracle failed")
    path = target / "receipt.json"
    observed = json.loads(path.read_text(encoding="utf-8"))
    _require(observed["status"] == "passed" and observed["contract_source_unchanged"],
             "operating oracle did not finish on unchanged source")
    _require(observed["oracle_sha256"] == _sha256(script), "operating oracle identity changed")
    _require(observed["constructed_actual_context_cases"] == len(observed["cases"]) == 34
             and all(case["passed"] for case in observed["cases"]),
             "operating oracle did not pass all 34 retained cases")
    _require(observed["numerical_evaluator_calls"] == [], "operating oracle ran an evaluator")
    consumer = observed["integration"]
    _require(sum(consumer["positive_numerical_dominance"]) == 1
             and consumer["incompatible_dominance"] is False
             and consumer["missing_new_provenance_dominance"] is False,
             "operating oracle consumer controls failed")
    receipt["operating_oracle"] = {"receipt_path": str(path), "receipt_sha256": _sha256(path),
                                    "context_cases": 34, "numerical_evaluator_calls": []}


def _prepare_output(root: Path, out: Path) -> Path:
    out = out.expanduser().resolve()
    _require(not out.exists(), "output must be a new external directory; prior attempts are retained")
    _require(not any((p / ".git").exists() for p in (out, *out.parents)),
             "output must be outside a source checkout")
    _require(Path(__file__).resolve().is_relative_to(root / "kayakgen"),
             "preflight module must come from the selected source checkout")
    out.mkdir(parents=True)
    return out


def _finish_source(root: Path, receipt: dict) -> None:
    from kayakgen.operations.gate import source_snapshot

    receipt["source_after"] = source_snapshot(root)
    before, after = receipt["source_before"], receipt["source_after"]
    receipt["source_unchanged"] = all(
        before[key] == after[key] for key in ("tree_sha", "fingerprint_sha256")
    )
    _require(receipt["source_unchanged"], "source changed during semantic preflight")


def run_preflight(plan: dict, output: Path) -> int:
    from kayakgen.operations.gate import GateInterrupted, _interrupt_signals, _write_receipt, source_snapshot

    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()).resolve()
    out = _prepare_output(root, output)
    path = out / "receipt.json"
    receipt = {**plan, "schema_version": "kayakgen-semantic-preflight/1",
        "run_id": str(uuid.uuid4()), "evidence_scope": "semantic_preflight",
        "release_acceptance": False, "status": "running", "exit_code": None,
        "full_release_gate_required": True, "scientific_claim_promotion": False,
        "started_at": _now(), "source_before": source_snapshot(root), "source_after": None,
        "source_unchanged": None, "commands": [], "failure_reasons": [],
        "interpreter": {"executable": sys.executable, "version": sys.version},
        "environment_policy": "clear environment-only pytest selectors/full-gate skip pin; fixed selected files"}
    _write_receipt(path, receipt)
    code = 0
    with _interrupt_signals():
        try:
            if receipt["pytest_targets"]:
                _pytest_checks(root, out, receipt)
                if receipt["operating_oracle_required"]:
                    _operating_oracle(root, out, receipt)
                receipt["status"] = "passed"
            else:
                receipt["status"] = "not_applicable"
            _finish_source(root, receipt)
        except GateInterrupted as exc:
            receipt.update(status="interrupted", failure_reasons=[str(exc)])
            code = 128 + exc.signum
        except (OSError, ValueError, KeyError, ElementTree.ParseError, subprocess.CalledProcessError) as exc:
            receipt.update(status="failed", failure_reasons=[str(exc)])
            code = 1
        finally:
            receipt.update(exit_code=code, finished_at=_now())
            try:
                _write_receipt(path, receipt)
            except GateInterrupted as exc:
                code = 128 + exc.signum
                receipt.update(status="interrupted", exit_code=code, failure_reasons=[str(exc)])
                _write_receipt(path, receipt)
    print(json.dumps({"status": receipt["status"], "evidence_scope": "semantic_preflight",
                      "release_acceptance": False, "receipt": str(path)}))
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--contract", action="append", default=[], choices=[c.id for c in CONTRACTS])
    parser.add_argument("--out", type=Path, required=True, help="New external attempt directory")
    args = parser.parse_args()
    if not args.changed_path and not args.contract:
        parser.error("supply at least one changed path or explicit contract")
    try:
        return run_preflight(preflight_plan(args.changed_path, args.contract), args.out)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
