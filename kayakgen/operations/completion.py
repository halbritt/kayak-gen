"""Permit a completion action only after its declared audit evidence passes."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import TypeVar

T = TypeVar("T")


class CompletionRefused(ValueError):
    """A required audit or evidence condition did not permit the action."""


@dataclass(frozen=True)
class VerifiedReceipt:
    path: str
    sha256: str
    checked_fields: tuple[str, ...]


@dataclass(frozen=True)
class CompletionEvidence:
    expected_source: tuple[tuple[str, str], ...]
    requirements_sha256: str
    receipts: tuple[VerifiedReceipt, ...]

    def as_dict(self) -> dict:
        return {
            "expected_source": dict(self.expected_source),
            "requirements_sha256": self.requirements_sha256,
            "receipts": [
                {"path": receipt.path, "sha256": receipt.sha256,
                 "checked_fields": list(receipt.checked_fields)}
                for receipt in self.receipts
            ],
        }


def _require_terminal_audit(audit_result: Mapping[str, object]) -> None:
    if not isinstance(audit_result, Mapping):
        raise CompletionRefused("audit result must be a JSON object")
    audit = dict(audit_result)
    if any(audit.get(key) is not None for key in ("session_id", "cell_id")):
        raise CompletionRefused("audit is still running: a session or cell handle is present")
    if "status" in audit and audit["status"] not in ("passed", "succeeded", "success"):
        raise CompletionRefused("audit status must be passed, succeeded or success when present")
    exit_code = audit.get("exit_code")
    if type(exit_code) is not int or exit_code != 0:
        raise CompletionRefused("audit requires a terminal integer exit_code of zero")


def _canonical_json(payload: object) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, allow_nan=False,
                          sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise CompletionRefused("evidence must contain only finite JSON values") from exc


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    payload = {}
    for key, content in pairs:
        if key in payload:
            raise ValueError(f"duplicate JSON key {key!r}")
        payload[key] = content
    return payload


def _nonfinite_constant(constant: str) -> None:
    raise ValueError(f"non-finite JSON constant {constant}")


def _decode_json(raw: bytes, label: str) -> object:
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=_nonfinite_constant)
    except (UnicodeDecodeError, ValueError) as exc:
        raise CompletionRefused(f"invalid JSON in {label}: {exc}") from exc
    _canonical_json(payload)
    return payload


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except (OSError, ValueError) as exc:
        raise CompletionRefused(f"cannot read {label} {path}: {exc}") from exc


def _object_keys(payload: object, expected: set[str], label: str) -> dict:
    if not isinstance(payload, dict) or set(payload) != expected:
        raise CompletionRefused(f"{label} must contain exactly {sorted(expected)}")
    return payload


def _nonempty_mapping(payload: object, label: str) -> dict:
    if not isinstance(payload, dict) or not payload:
        raise CompletionRefused(f"{label} must be a nonempty object")
    return payload


def _source_expectation(payload: object) -> tuple[tuple[str, str], ...]:
    source = _nonempty_mapping(payload, "expected_source")
    for name, digest in source.items():
        if not name or not isinstance(digest, str) or not re.fullmatch(
            r"(?:[0-9a-f]{40}|[0-9a-f]{64})", digest
        ):
            raise CompletionRefused("expected_source values must be lowercase 40/64-digit hashes")
    return tuple(sorted(source.items()))


def _pointer_segments(pointer: object) -> list[str]:
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise CompletionRefused("evidence selectors must be JSON pointers")
    if re.search(r"~(?![01])", pointer):
        raise CompletionRefused(f"invalid JSON pointer escape in {pointer!r}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]


def _selected(payload: object, pointer: object) -> object:
    current = payload
    for segment in _pointer_segments(pointer):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        elif isinstance(current, list) and re.fullmatch(r"0|[1-9][0-9]*", segment):
            try:
                current = current[int(segment)]
            except (ValueError, IndexError) as exc:
                raise CompletionRefused(f"missing evidence field {pointer!r}") from exc
        else:
            raise CompletionRefused(f"missing evidence field {pointer!r}")
    return current


def _verify_receipt(
    spec: object, policy_dir: Path, source: tuple[tuple[str, str], ...],
) -> VerifiedReceipt:
    spec = _object_keys(spec, {"path", "sha256", "source_fields", "equals"}, "receipt requirement")
    if not isinstance(spec["path"], str) or not spec["path"]:
        raise CompletionRefused("receipt path must be a nonempty string")
    expected_sha = spec["sha256"]
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise CompletionRefused("receipt sha256 must be a lowercase SHA-256")
    bindings = _nonempty_mapping(spec["source_fields"], "receipt source_fields")
    if set(bindings) != {name for name, _ in source}:
        raise CompletionRefused("receipt must bind every expected source identity")
    predicates = _nonempty_mapping(spec["equals"], "receipt equals")
    receipt_path = (policy_dir / spec["path"]).absolute()
    raw = _read_bytes(receipt_path, "required receipt")
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha:
        raise CompletionRefused(f"receipt SHA-256 mismatch: {receipt_path}")
    payload = _decode_json(raw, f"receipt {receipt_path}")
    for name, expected in source:
        if _selected(payload, bindings[name]) != expected:
            raise CompletionRefused(f"receipt source identity {name!r} does not match: {receipt_path}")
    for pointer, expected in predicates.items():
        if _canonical_json(_selected(payload, pointer)) != _canonical_json(expected):
            raise CompletionRefused(f"receipt predicate {pointer!r} does not match: {receipt_path}")
    return VerifiedReceipt(str(receipt_path), actual_sha, tuple(sorted(predicates)))


def _verified_evidence(requirements_path: Path) -> CompletionEvidence:
    raw = _read_bytes(requirements_path, "completion requirements")
    policy = _object_keys(_decode_json(raw, "completion requirements"),
                          {"schema_version", "expected_source", "receipts"}, "completion requirements")
    if policy["schema_version"] != "1":
        raise CompletionRefused("unsupported completion requirements schema_version")
    source = _source_expectation(policy["expected_source"])
    requirements = policy["receipts"]
    if not isinstance(requirements, list) or not requirements:
        raise CompletionRefused("at least one mandatory receipt is required")
    receipts = tuple(_verify_receipt(spec, requirements_path.absolute().parent, source)
                     for spec in requirements)
    return CompletionEvidence(source, hashlib.sha256(raw).hexdigest(), receipts)


def guarded_completion(
    audit_result: Mapping[str, object], requirements_path: Path,
    action: Callable[[CompletionEvidence], T],
) -> T:
    """Invoke one action after terminal audit and declared receipt checks pass.

    Receipt bytes are read once for hashing and validation. This is a local
    admission decision, not authentication, an action rollback, or a guarantee
    against files changing after validation. The action owns its side effects.
    """
    _require_terminal_audit(audit_result)
    evidence = _verified_evidence(requirements_path)
    return action(evidence)


def _execute_action(argv: list[str], evidence: CompletionEvidence) -> int:
    try:
        # Keep action output visible without mixing it into the JSON admission result.
        completed = subprocess.run(argv, check=False, stdout=sys.stderr)
    except OSError as exc:
        print(json.dumps({"schema_version": "1", "status": "action_failed",
                          "reason": str(exc), **evidence.as_dict()}))
        return 127 if isinstance(exc, FileNotFoundError) else 126
    status = "action_succeeded" if completed.returncode == 0 else "action_failed"
    print(json.dumps({"schema_version": "1", "status": status,
                      "action_exit_code": completed.returncode, **evidence.as_dict()}))
    return completed.returncode if completed.returncode >= 0 else 128 - completed.returncode


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-result", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("action", nargs=argparse.REMAINDER,
                        help="Explicit action argv after --; no shell or retry.")
    args = parser.parse_args(argv)
    action_argv = args.action[1:] if args.action[:1] == ["--"] else args.action
    if not action_argv:
        parser.error("a completion action argv is required after --")
    try:
        audit = _decode_json(_read_bytes(args.audit_result, "audit result"), "audit result")
        return guarded_completion(audit, args.requirements,
                                  lambda evidence: _execute_action(action_argv, evidence))
    except CompletionRefused as exc:
        print(json.dumps({"schema_version": "1", "status": "refused", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
