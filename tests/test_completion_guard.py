"""Completion actions are conditional on terminal, source-bound evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def invoke(
    tmp_path: Path, audit: dict, requirements: Path, action: list[str] | None = None,
) -> subprocess.CompletedProcess:
    audit_path = write_json(tmp_path / "audit-result.json", audit)
    action = action or [
        sys.executable, "-c",
        "from pathlib import Path; import sys; "
        "p=Path(sys.argv[1]); "
        "p.write_text(p.read_text()+'accepted\\n' if p.exists() else 'accepted\\n')",
        str(tmp_path / "completion-marker"),
    ]
    return subprocess.run(
        [sys.executable, "-m", "kayakgen.operations.completion",
         "--audit-result", str(audit_path), "--requirements", str(requirements),
         "--", *action],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True, text=True, timeout=10,
    )


def test_failed_audit_blocks_the_real_completion_action(tmp_path: Path) -> None:
    result = invoke(tmp_path, {"exit_code": 1, "output": "inactive"}, tmp_path / "policy.json")
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "refused"
    assert "exit_code" in json.loads(result.stdout)["reason"]
    assert not (tmp_path / "completion-marker").exists()


def requirements(tmp_path: Path) -> Path:
    receipt = write_json(tmp_path / "receipt.json", {
        "source_tree": "a" * 40, "status": "passed", "owner_source_unchanged": True,
    })
    return write_json(tmp_path / "policy.json", {
        "schema_version": "1", "expected_source": {"tree": "a" * 40},
        "receipts": [{
            "path": receipt.name,
            "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
            "source_fields": {"tree": "/source_tree"},
            "equals": {"/status": "passed", "/owner_source_unchanged": True},
        }],
    })


def test_terminal_success_with_bound_receipt_runs_real_action_once(tmp_path: Path) -> None:
    result = invoke(tmp_path, {"exit_code": 0, "session_id": None}, requirements(tmp_path))
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout)["status"] == "action_succeeded"
    assert (tmp_path / "completion-marker").read_text() == "accepted\n"


@pytest.mark.parametrize("exit_code", [False, True, 0.0, "0", None])
def test_only_terminal_integer_zero_permits_completion(tmp_path: Path, exit_code) -> None:
    result = invoke(tmp_path, {"exit_code": exit_code}, requirements(tmp_path))
    assert result.returncode == 2
    assert "exit_code" in json.loads(result.stdout)["reason"]
    assert not (tmp_path / "completion-marker").exists()


@pytest.mark.parametrize("handle,value", [("session_id", 0), ("session_id", ""), ("cell_id", False)])
def test_nonnull_handles_remain_incomplete_even_if_falsey(tmp_path: Path, handle, value) -> None:
    result = invoke(tmp_path, {"exit_code": 0, handle: value}, requirements(tmp_path))
    assert result.returncode == 2
    assert "still running" in json.loads(result.stdout)["reason"]
    assert not (tmp_path / "completion-marker").exists()


def test_missing_exit_code_and_nonterminal_status_refuse_completion(tmp_path: Path) -> None:
    policy = requirements(tmp_path)
    for audit in ({}, {"exit_code": 0, "status": "running"}):
        result = invoke(tmp_path, audit, policy)
        assert result.returncode == 2
        assert json.loads(result.stdout)["status"] == "refused"
        assert not (tmp_path / "completion-marker").exists()


@pytest.mark.parametrize("status", ["failed", "interrupted", "cancelled", "unknown", None, True])
def test_explicit_unsuccessful_or_malformed_audit_status_refuses_action(tmp_path: Path, status):
    result = invoke(tmp_path, {"exit_code": 0, "status": status}, requirements(tmp_path))
    assert result.returncode == 2
    assert "status" in json.loads(result.stdout)["reason"]
    assert not (tmp_path / "completion-marker").exists()


@pytest.mark.parametrize("status", ["passed", "succeeded", "success"])
def test_supported_successful_audit_status_allows_action(tmp_path: Path, status):
    result = invoke(tmp_path, {"exit_code": 0, "status": status}, requirements(tmp_path))
    assert result.returncode == 0
    assert (tmp_path / "completion-marker").read_text() == "accepted\n"


def replace_receipt(tmp_path: Path, raw: bytes, *, refresh_digest: bool = True) -> Path:
    policy_path = requirements(tmp_path)
    receipt = tmp_path / "receipt.json"
    receipt.write_bytes(raw)
    if refresh_digest:
        policy = json.loads(policy_path.read_text())
        policy["receipts"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
        write_json(policy_path, policy)
    return policy_path


@pytest.mark.parametrize(
    "raw,reason",
    [
        (b'{"source_tree":"' + b'a' * 40 + b'","source_tree":"' + b'a' * 40 + b'"}',
         "duplicate JSON key"),
        (b'{"extra":NaN}', "non-finite JSON"),
        (b'{"extra":1e999}', "finite JSON"),
        (b'not json', "invalid JSON"),
        (b'\xff', "invalid JSON"),
    ],
)
def test_malformed_required_receipt_refuses_real_action(tmp_path: Path, raw, reason) -> None:
    policy = replace_receipt(tmp_path, raw)
    result = invoke(tmp_path, {"exit_code": 0}, policy)
    assert result.returncode == 2
    assert reason in json.loads(result.stdout)["reason"]
    assert not (tmp_path / "completion-marker").exists()


def test_absent_receipt_and_changed_receipt_bytes_are_refused(tmp_path: Path) -> None:
    policy = requirements(tmp_path)
    (tmp_path / "receipt.json").unlink()
    missing = invoke(tmp_path, {"exit_code": 0}, policy)
    assert missing.returncode == 2
    assert "cannot read required receipt" in json.loads(missing.stdout)["reason"]
    changed = invoke(tmp_path, {"exit_code": 0}, replace_receipt(
        tmp_path, b'{"status":"passed"}', refresh_digest=False,
    ))
    assert changed.returncode == 2
    assert "SHA-256 mismatch" in json.loads(changed.stdout)["reason"]
    assert not (tmp_path / "completion-marker").exists()


@pytest.mark.parametrize(
    "field,value,reason",
    [("source_tree", "b" * 40, "source identity"),
     ("status", "failed", "predicate"),
     ("owner_source_unchanged", 1, "predicate")],
)
def test_source_and_predicates_are_checked_with_json_type_equality(
    tmp_path: Path, field, value, reason,
) -> None:
    payload = {"source_tree": "a" * 40, "status": "passed", "owner_source_unchanged": True}
    payload[field] = value
    policy = replace_receipt(tmp_path, json.dumps(payload).encode())
    result = invoke(tmp_path, {"exit_code": 0}, policy)
    assert result.returncode == 2
    assert reason in json.loads(result.stdout)["reason"]
    assert not (tmp_path / "completion-marker").exists()


def test_task_declares_all_required_receipts_and_source_dimensions(tmp_path: Path) -> None:
    policy_path = requirements(tmp_path)
    policy = json.loads(policy_path.read_text())
    policy["receipts"].append({**policy["receipts"][0], "path": "missing-runtime.json"})
    write_json(policy_path, policy)
    result = invoke(tmp_path, {"exit_code": 0}, policy_path)
    assert result.returncode == 2
    assert "missing-runtime.json" in json.loads(result.stdout)["reason"]
    assert not (tmp_path / "completion-marker").exists()
    policy["receipts"] = policy["receipts"][:1]
    policy["expected_source"]["commit"] = "c" * 40
    write_json(policy_path, policy)
    result = invoke(tmp_path, {"exit_code": 0}, policy_path)
    assert result.returncode == 2
    assert "every expected source" in json.loads(result.stdout)["reason"]


@pytest.mark.parametrize("change", ["no_receipts", "no_source", "no_predicates", "wrong_schema"])
def test_incomplete_requirements_do_not_silently_pass(tmp_path: Path, change) -> None:
    policy_path = requirements(tmp_path)
    policy = json.loads(policy_path.read_text())
    if change == "no_receipts":
        policy["receipts"] = []
    elif change == "no_source":
        policy["expected_source"] = {}
    elif change == "no_predicates":
        policy["receipts"][0]["equals"] = {}
    else:
        policy["schema_version"] = "unsupported"
    write_json(policy_path, policy)
    result = invoke(tmp_path, {"exit_code": 0}, policy_path)
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "refused"
    assert not (tmp_path / "completion-marker").exists()


def test_different_receipt_layout_and_explicit_historical_source_are_allowed(tmp_path: Path) -> None:
    receipt = write_json(tmp_path / "preuve-évaluation.json", {
        "source": {"fingerprint": "b" * 64},
        "checks": {"a/b": {"~ready": [True]}}, "preview_kind": "transient",
    })
    policy = write_json(tmp_path / "policy.json", {
        "schema_version": "1", "expected_source": {"snapshot": "b" * 64},
        "receipts": [{
            "path": receipt.name, "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
            "source_fields": {"snapshot": "/source/fingerprint"},
            "equals": {"/checks/a~1b/~0ready/0": True, "/preview_kind": "transient"},
        }],
    })
    result = invoke(tmp_path, {"exit_code": 0}, policy)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["expected_source"] == {"snapshot": "b" * 64}
    assert (tmp_path / "completion-marker").read_text() == "accepted\n"


def test_action_failure_is_visible_and_is_never_retried(tmp_path: Path) -> None:
    action = [sys.executable, "-c", "print('action output'); raise SystemExit(7)"]
    result = invoke(tmp_path, {"exit_code": 0}, requirements(tmp_path), action)
    assert result.returncode == 7
    assert json.loads(result.stdout)["status"] == "action_failed"
    assert json.loads(result.stdout)["action_exit_code"] == 7
    assert result.stderr.count("action output") == 1


def test_programmatic_action_receives_immutable_evidence_once_and_exceptions_propagate(
    tmp_path: Path,
) -> None:
    from dataclasses import FrozenInstanceError
    from kayakgen.operations.completion import guarded_completion

    observations = []

    def action(evidence):
        observations.append(evidence.as_dict())
        with pytest.raises(FrozenInstanceError):
            evidence.expected_source = ()
        raise RuntimeError("completion action failed")

    with pytest.raises(RuntimeError, match="completion action failed"):
        guarded_completion({"exit_code": 0}, requirements(tmp_path), action)
    assert len(observations) == 1
    assert observations[0]["expected_source"] == {"tree": "a" * 40}


@pytest.mark.parametrize("selector", ["/missing", "/bad~escape"])
def test_missing_or_malformed_required_selectors_refuse_action(tmp_path: Path, selector) -> None:
    policy_path = requirements(tmp_path)
    policy = json.loads(policy_path.read_text())
    policy["receipts"][0]["equals"] = {selector: True}
    write_json(policy_path, policy)
    result = invoke(tmp_path, {"exit_code": 0}, policy_path)
    assert result.returncode == 2
    assert "field" in json.loads(result.stdout)["reason"] or "pointer" in result.stdout
    assert not (tmp_path / "completion-marker").exists()


def test_ambiguous_policy_and_audit_json_cannot_authorize_action(tmp_path: Path) -> None:
    from kayakgen.operations.completion import main

    policy = requirements(tmp_path)
    audit_path = tmp_path / "audit-result.json"
    audit_path.write_text('{"exit_code":1,"exit_code":0}', encoding="utf-8")
    marker = tmp_path / "completion-marker"
    argv = ["--audit-result", str(audit_path), "--requirements", str(policy),
            "--", sys.executable, "-c", "raise AssertionError('action ran')"]
    assert main(argv) == 2
    write_json(audit_path, {"exit_code": 0})
    policy.write_text('{"schema_version":"1","schema_version":"1"}', encoding="utf-8")
    assert main(argv) == 2
    assert not marker.exists()


def test_action_launch_failure_is_reported_without_success(tmp_path: Path) -> None:
    result = invoke(tmp_path, {"exit_code": 0}, requirements(tmp_path),
                    [str(tmp_path / "absent-action")])
    assert result.returncode == 127
    assert json.loads(result.stdout)["status"] == "action_failed"


def test_invalid_receipt_filename_retains_a_refusal_reason(tmp_path: Path) -> None:
    policy_path = requirements(tmp_path)
    policy = json.loads(policy_path.read_text())
    policy["receipts"][0]["path"] = "invalid\x00receipt"
    write_json(policy_path, policy)
    result = invoke(tmp_path, {"exit_code": 0}, policy_path)
    assert result.returncode == 2
    assert "cannot read required receipt" in json.loads(result.stdout)["reason"]
    assert not (tmp_path / "completion-marker").exists()
