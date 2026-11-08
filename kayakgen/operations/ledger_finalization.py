"""Derive current ledger criterion status from applicable, source-bound receipts.

A finalization policy declares, per ledger item, which criteria are mandatory
for current acceptance and which are future obligations, which retained
pending flag each criterion explains, and which receipts support it. The view
checks receipt bytes and source bindings with the RFC 0079 validator, checks
that the criterion source is the item's accepted source, and only classifies a
pending flag as history when recorded timestamps or Git ancestry prove it
precedes that source. Everything else stays an explicit conflict.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

from kayakgen.operations.completion import (
    CompletionRefused,
    _canonical_json,
    _decode_json,
    _object_keys,
    _pointer_segments,
    _read_bytes,
    _selected,
    _verify_receipt,
)

VIEW_SCHEMA = "kayakgen.ledger-view/1"
HISTORY_KEY = "ledger_history"
CURRENT_KEY = "current_criteria"
# Ledger item fields that record the source an item was accepted on.
ACCEPTED_SOURCE_FIELDS = {"source_tree": "final_source_tree", "source_commit": "final_source_commit"}
_HASH = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")


class PolicyRefused(ValueError):
    """The ledger or finalization policy is malformed or does not match."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _timestamp(value: object, label: str) -> datetime | None:
    if value == "unknown":
        return None
    if not isinstance(value, str):
        raise PolicyRefused(f"{label} must be an RFC 3339 timestamp or 'unknown'")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PolicyRefused(f"{label} is not an RFC 3339 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise PolicyRefused(f"{label} must carry a UTC offset: {value!r}")
    return parsed


def _source_map(payload: object, label: str) -> dict[str, str]:
    if not isinstance(payload, dict) or not payload:
        raise PolicyRefused(f"{label} must be a nonempty object of hashes")
    for name, digest in payload.items():
        if not isinstance(name, str) or not name or not isinstance(digest, str) or not _HASH.fullmatch(digest):
            raise PolicyRefused(f"{label} values must be lowercase 40/64-digit hashes")
    return dict(payload)


def _check_receipts(
    specs: object, base: Path, source: dict[str, str], label: str,
) -> tuple[list[dict], list[str]]:
    """Verify receipt specs; each binds a nonempty subset, together all of ``source``."""
    if not isinstance(specs, list) or not specs:
        raise PolicyRefused(f"{label} requires at least one receipt")
    verified, reasons, covered = [], [], set()
    for spec in specs:
        if not isinstance(spec, dict):
            raise PolicyRefused(f"{label} receipt must be an object")
        spec = dict(spec)
        observed_pointer = spec.pop("observed_at", None)
        fields = spec.get("source_fields")
        if not isinstance(fields, dict) or not fields or not set(fields) <= set(source):
            raise PolicyRefused(f"{label} receipt source_fields must be a nonempty subset of {sorted(source)}")
        subset = tuple(sorted((name, source[name]) for name in fields))
        try:
            receipt = _verify_receipt(spec, base, subset)
        except CompletionRefused as exc:
            reasons.append(f"receipt not applicable: {exc}")
            continue
        observed = "unknown"
        if observed_pointer is not None:
            raw = _read_bytes(Path(receipt.path), "receipt")
            if _sha256(raw) != receipt.sha256:
                reasons.append(f"receipt changed while reading observed_at: {receipt.path}")
                continue
            payload = _decode_json(raw, receipt.path)
            try:
                observed = _selected(payload, observed_pointer)
            except CompletionRefused as exc:
                reasons.append(f"receipt observed_at unavailable: {exc}")
                continue
            _timestamp(observed, f"{receipt.path} observed_at")
        covered.update(fields)
        verified.append({"path": receipt.path, "sha256": receipt.sha256,
                         "checked_fields": list(receipt.checked_fields),
                         "source_fields": sorted(fields), "observed_at": observed})
    if not reasons and covered != set(source):
        reasons.append(f"receipts do not bind every source identity: missing {sorted(set(source) - covered)}")
    return verified, reasons


def _is_strict_ancestor(repo: Path | None, older: str, newer: str) -> tuple[bool, str]:
    if repo is None:
        return False, "Git ancestry needs --repo"
    if older == newer:
        return False, "pending snapshot was observed on the accepted commit itself"
    result = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", older, newer],
                            capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return True, ""
    if result.returncode == 1:
        return False, f"pending commit {older} is not an ancestor of accepted commit {newer}"
    return False, f"git ancestry check failed: {result.stderr.strip()}"


def _resolve(item: dict, pointer: object) -> tuple[bool, object]:
    current: object = item
    for segment in _pointer_segments(pointer):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        else:
            return False, None
    return True, current


def _history_record(item: dict, criterion_id: str) -> dict | None:
    for record in item.get(HISTORY_KEY, []):
        if isinstance(record, dict) and record.get("criterion") == criterion_id:
            return record
    return None


def _pending_view(
    item: dict, criterion: dict, base: Path, repo: Path | None,
    applicable: dict[str, str], receipts: list[dict],
) -> tuple[dict | None, list[str]]:
    pending = criterion.get("pending")
    if pending is None:
        return None, []
    pending = _object_keys(
        pending, {"pointer", "as_of", "observed_source", "evidence"}, "pending declaration")
    present, value = _resolve(item, pending["pointer"])
    location = "ledger"
    if not present:
        record = _history_record(item, criterion["id"])
        if record is None or record.get("pointer") != pending["pointer"]:
            raise PolicyRefused(f"{criterion['id']}: pending pointer {pending['pointer']!r} is absent")
        value, location = record.get("value"), HISTORY_KEY
    view = {"pointer": pending["pointer"], "value": value, "location": location,
            "as_of": pending["as_of"], "observed_source": pending["observed_source"]}
    if value is not True:
        view["classification"] = "not_pending"
        return view, []
    as_of = _timestamp(pending["as_of"], f"{criterion['id']} pending as_of")
    observed = pending["observed_source"]
    reasons, bases = [], []
    if observed != "unknown":
        observed = _source_map(observed, f"{criterion['id']} pending observed_source")
        evidence, evidence_reasons = _check_receipts(
            pending["evidence"], base, observed, f"{criterion['id']} pending evidence")
        view["evidence"] = evidence
        reasons += evidence_reasons
        if "source_commit" in observed and "source_commit" in applicable:
            ok, why = _is_strict_ancestor(repo, observed["source_commit"], applicable["source_commit"])
            if ok:
                bases.append("git_ancestry")
            else:
                reasons.append(why)
        elif observed == {k: applicable.get(k) for k in observed}:
            reasons.append("pending snapshot was observed on the accepted source")
    elif pending["evidence"] not in (None, []):
        raise PolicyRefused(f"{criterion['id']}: unknown observed_source cannot carry evidence")
    if as_of is not None:
        times = [_timestamp(r["observed_at"], r["path"]) for r in receipts]
        if not times or any(t is None for t in times):
            reasons.append("pending as_of is known but a supporting receipt has no observed_at")
        elif all(t > as_of for t in times):
            bases.append("timestamps")
        else:
            reasons.append("pending snapshot is not older than every supporting receipt")
    if not bases and not reasons:
        reasons.append("pending snapshot ordering relative to the accepted source is unproven")
    view["ordering_basis"] = bases
    view["classification"] = "historical" if bases and not reasons else "current_conflict"
    return view, reasons


def _undeclared_pending(item: dict, declared: set[str]) -> list[str]:
    found = []

    def walk(node: object, pointer: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if pointer == "" and key in (HISTORY_KEY, CURRENT_KEY):
                    continue
                escaped = key.replace("~", "~0").replace("/", "~1")
                path = f"{pointer}/{escaped}"
                if child is True and "pending" in key.lower() and path not in declared:
                    found.append(path)
                walk(child, path)
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, f"{pointer}/{index}")

    walk(item, "")
    return found


def _criterion_view(item: dict, criterion: object, base: Path, repo: Path | None) -> dict:
    if not isinstance(criterion, dict):
        raise PolicyRefused("criterion must be an object")
    keys = set(criterion)
    allowed = {"id", "item", "obligation", "requirement", "applicable_source", "pending", "receipts"}
    if not keys <= allowed or not {"id", "item", "obligation", "requirement"} <= keys:
        raise PolicyRefused(f"criterion keys must be within {sorted(allowed)}")
    view = {"id": criterion["id"], "obligation": criterion["obligation"],
            "requirement": criterion["requirement"]}
    if criterion["obligation"] == "future":
        if {"applicable_source", "receipts", "pending"} & keys:
            raise PolicyRefused(f"{criterion['id']}: future obligations cannot be cleared by receipts")
        view.update(status="open_future", reasons=[], supporting_receipts=[])
        return view
    if criterion["obligation"] != "mandatory":
        raise PolicyRefused(f"{criterion['id']}: obligation must be 'mandatory' or 'future'")
    applicable = _source_map(criterion.get("applicable_source"), f"{criterion['id']} applicable_source")
    reasons = []
    for name, digest in applicable.items():
        field = ACCEPTED_SOURCE_FIELDS.get(name)
        if field is None:
            raise PolicyRefused(f"{criterion['id']}: unsupported source identity {name!r}")
        if item.get(field) != digest:
            reasons.append(f"applicable {name} {digest} is not the item's accepted {field} {item.get(field)}")
    receipts, receipt_reasons = _check_receipts(
        criterion.get("receipts"), base, applicable, f"{criterion['id']} receipts")
    reasons += receipt_reasons
    pending, pending_reasons = _pending_view(item, criterion, base, repo, applicable, receipts)
    reasons += pending_reasons
    view.update(applicable_source=applicable, supporting_receipts=receipts, pending=pending,
                status="conflict" if reasons else "accepted", reasons=reasons)
    return view


def build_view(ledger_path: Path, policy_path: Path, repo: Path | None = None) -> dict:
    """Return the current criterion view; raise PolicyRefused for invalid inputs."""
    policy_raw = _read_bytes(policy_path, "finalization policy")
    try:
        policy = _object_keys(_decode_json(policy_raw, "finalization policy"),
                              {"schema_version", "ledger", "criteria"}, "finalization policy")
        if policy["schema_version"] != "1":
            raise PolicyRefused("unsupported finalization policy schema_version")
        ledger_ref = _object_keys(policy["ledger"], {"sha256"}, "policy ledger")
        ledger_raw = _read_bytes(ledger_path, "ledger")
        if _sha256(ledger_raw) != ledger_ref["sha256"]:
            raise PolicyRefused("ledger bytes do not match the policy's ledger sha256")
        ledger = _decode_json(ledger_raw, "ledger")
        base = policy_path.absolute().parent
        items = {item.get("work_id"): item for item in ledger.get("items", [])
                 if isinstance(item, dict)}
        criteria = policy["criteria"]
        if not isinstance(criteria, list) or not criteria:
            raise PolicyRefused("policy requires at least one criterion")
        ids = [c.get("id") if isinstance(c, dict) else None for c in criteria]
        if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
            raise PolicyRefused("criterion ids must be unique nonempty strings")
        views = []
        for work_id, item in items.items():
            mine = [c for c in criteria if c.get("item") == work_id]
            criterion_views = [_criterion_view(item, c, base, repo) for c in mine]
            declared = {c["pending"]["pointer"] for c in mine if isinstance(c.get("pending"), dict)}
            undeclared = _undeclared_pending(item, declared)
            claimed = item.get("plane_state") == "Done"
            conflict = bool(undeclared) or any(v["status"] == "conflict" for v in criterion_views)
            reviewed = any(v["status"] == "accepted" for v in criterion_views)
            if conflict:
                status = "conflict"
            elif not claimed:
                status = "not_accepted"
            else:
                status = "accepted" if reviewed else "claimed_unreviewed"
            views.append({
                "work_id": work_id, "claimed_accepted": claimed, "current_status": status,
                "accepted_source": {k: item.get(f) for k, f in ACCEPTED_SOURCE_FIELDS.items()},
                "undeclared_pending": undeclared, "criteria": criterion_views,
            })
        unknown = {c.get("item") for c in criteria} - set(items)
        if unknown:
            raise PolicyRefused(f"policy names unknown ledger items {sorted(map(str, unknown))}")
    except CompletionRefused as exc:
        raise PolicyRefused(str(exc)) from exc
    conflicts = [f"{v['work_id']}" for v in views if v["current_status"] == "conflict"]
    return {"schema_version": VIEW_SCHEMA, "ledger": {"path": str(ledger_path.absolute()),
            "sha256": _sha256(ledger_raw)}, "policy": {"path": str(policy_path.absolute()),
            "sha256": _sha256(policy_raw)}, "repo": None if repo is None else str(repo.absolute()),
            "status": "conflict" if conflicts else "consistent", "conflicting_items": conflicts,
            "items": views}


def propose_finalized(ledger_path: Path, view: dict) -> dict:
    """Return a ledger copy where proven-historical pending flags move into item history.

    Every other field, including unrelated or conflicting pending flags, is unchanged.
    """
    if view["status"] != "consistent":
        raise PolicyRefused("refusing to finalize a ledger view with conflicts")
    raw = _read_bytes(ledger_path, "ledger")
    if _sha256(raw) != view["ledger"]["sha256"]:
        raise PolicyRefused("ledger changed after the view was built")
    ledger = copy.deepcopy(_decode_json(raw, "ledger"))
    by_id = {item["work_id"]: item for item in ledger["items"]}
    for item_view in view["items"]:
        item = by_id[item_view["work_id"]]
        current = []
        for criterion in item_view["criteria"]:
            entry = {k: criterion[k] for k in ("id", "obligation", "requirement", "status")}
            if criterion["status"] == "accepted":
                entry["applicable_source"] = criterion["applicable_source"]
                entry["supporting_receipts"] = [
                    {k: r[k] for k in ("path", "sha256", "observed_at")}
                    for r in criterion["supporting_receipts"]]
            pending = criterion.get("pending")
            if pending and pending["classification"] == "historical" and pending["location"] == "ledger":
                segments = _pointer_segments(pending["pointer"])
                parent = item
                for segment in segments[:-1]:
                    parent = parent[segment]
                del parent[segments[-1]]
                item.setdefault(HISTORY_KEY, []).append({
                    "criterion": criterion["id"], "pointer": pending["pointer"],
                    "value": pending["value"], "as_of": pending["as_of"],
                    "observed_source": pending["observed_source"],
                    "classification": "historical", "ordering_basis": pending["ordering_basis"],
                    "superseded_by": [r["sha256"] for r in criterion["supporting_receipts"]],
                })
            current.append(entry)
        if current:
            item[CURRENT_KEY] = current
    ledger["finalization"] = {"view_schema": VIEW_SCHEMA, "previous_ledger_sha256": view["ledger"]["sha256"],
                              "policy_sha256": view["policy"]["sha256"]}
    return ledger


def _write_new(path: Path, raw: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(raw)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("view", "finalize"):
        command = sub.add_parser(name)
        command.add_argument("--ledger", type=Path, required=True)
        command.add_argument("--policy", type=Path, required=True)
        command.add_argument("--repo", type=Path)
        if name == "finalize":
            command.add_argument("--out", type=Path, required=True,
                                 help="New path for the proposed ledger; never the original.")
            command.add_argument("--history", type=Path, required=True,
                                 help="New path receiving the exact original ledger bytes.")
    args = parser.parse_args(argv)
    try:
        view = build_view(args.ledger, args.policy, args.repo)
        if args.command == "view":
            print(json.dumps(view, indent=2, sort_keys=True))
            return 0 if view["status"] == "consistent" else 1
        if view["status"] != "consistent":
            print(json.dumps(view, indent=2, sort_keys=True))
            return 1
        resolved = {p.resolve() for p in (args.out, args.history)}
        if args.ledger.resolve() in resolved or len(resolved) != 2:
            raise PolicyRefused("--out and --history must be distinct new paths")
        proposed = propose_finalized(args.ledger, view)
        original = _read_bytes(args.ledger, "ledger")
        proposed_raw = (json.dumps(proposed, indent=2, ensure_ascii=False) + "\n").encode()
        _canonical_json(proposed)
        _write_new(args.history, original)
        _write_new(args.out, proposed_raw)
        print(json.dumps({"schema_version": VIEW_SCHEMA, "status": "proposed",
                          "history": {"path": str(args.history.absolute()), "sha256": _sha256(original)},
                          "proposed": {"path": str(args.out.absolute()), "sha256": _sha256(proposed_raw)},
                          "view": view}, indent=2, sort_keys=True))
        return 0
    except (PolicyRefused, CompletionRefused, FileExistsError) as exc:
        print(json.dumps({"schema_version": VIEW_SCHEMA, "status": "refused", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
