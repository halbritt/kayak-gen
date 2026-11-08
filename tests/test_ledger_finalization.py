"""Ledger finalization derives current status only from applicable receipts.

Fixtures are a real Git lineage A -> B -> C, receipt files with exact bytes,
and a mixed ledger: proven-historical pending, newer pending, source-mismatched
receipt, timestamp-ordered pending, future obligation and undeclared pending.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from kayakgen.operations.ledger_finalization import (
    PolicyRefused,
    build_view,
    propose_finalized,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True, env=env).stdout.strip()


@pytest.fixture
def lineage(tmp_path: Path) -> dict[str, dict[str, str]]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    commits = {}
    for name in ("A", "B", "C"):
        (repo / "f.txt").write_text(name)
        git(repo, "add", "f.txt")
        git(repo, "commit", "-q", "-m", name)
        commits[name] = {"source_commit": git(repo, "rev-parse", "HEAD"),
                         "source_tree": git(repo, "rev-parse", "HEAD^{tree}")}
    return commits


def write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path


def receipt(tmp: Path, name: str, source: dict[str, str], observed_at: str | None = None,
            status: str = "passed", fields: tuple[str, ...] = ("source_tree", "source_commit")) -> dict:
    payload = {"status": status, **{k: source[k] for k in fields}}
    if observed_at:
        payload["finished_at"] = observed_at
    path = write_json(tmp / name, payload)
    spec = {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_fields": {k: f"/{k}" for k in fields}, "equals": {"/status": "passed"}}
    if observed_at:
        spec["observed_at"] = "/finished_at"
    return spec


def item(work_id: str, accepted: dict[str, str], verification: dict, state: str = "Done") -> dict:
    return {"work_id": work_id, "plane_state": state, "verification": verification,
            "final_source_commit": accepted["source_commit"],
            "final_source_tree": accepted["source_tree"]}


def pending(pointer: str, observed: object = "unknown", as_of: str = "unknown",
            evidence: list | None = None) -> dict:
    return {"pointer": pointer, "as_of": as_of, "observed_source": observed,
            "evidence": evidence or []}


def mandatory(cid: str, work_id: str, source: dict, receipts: list, pend: dict | None = None) -> dict:
    criterion = {"id": cid, "item": work_id, "obligation": "mandatory",
                 "requirement": f"{cid} requirement", "applicable_source": source,
                 "receipts": receipts}
    if pend is not None:
        criterion["pending"] = pend
    return criterion


def write_inputs(tmp: Path, items: list[dict], criteria: list[dict]) -> tuple[Path, Path]:
    ledger = write_json(tmp / "ledger.json", {"items": items})
    policy = write_json(tmp / "policy.json", {
        "schema_version": "1", "ledger": {"sha256": hashlib.sha256(ledger.read_bytes()).hexdigest()},
        "criteria": criteria})
    return ledger, policy


def by_id(view: dict) -> dict[str, dict]:
    return {v["work_id"]: v for v in view["items"]}


@pytest.mark.parametrize("pending_first", [True, False])
def test_duplicate_work_ids_refuse_in_both_orders(tmp_path: Path, lineage: dict, pending_first):
    accepted = lineage["B"]
    ordinary = item("W3", accepted, {})
    with_pending = item("W3", accepted, {"extra_render_pending": True})
    rows = [with_pending, ordinary] if pending_first else [ordinary, with_pending]
    ledger, policy = write_inputs(tmp_path, rows, [
        mandatory("render", "W3", accepted, [receipt(tmp_path, "render.json", accepted)])])
    with pytest.raises(PolicyRefused, match="duplicate.*work_id"):
        build_view(ledger, policy, tmp_path / "repo")
    result = subprocess.run(
        [sys.executable, "-m", "kayakgen.operations.ledger_finalization", "view",
         "--ledger", str(ledger), "--policy", str(policy), "--repo", str(tmp_path / "repo")],
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}, capture_output=True, text=True, timeout=30)
    assert result.returncode == 2, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "refused"
    assert "duplicate" in json.loads(result.stdout)["reason"]


@pytest.mark.parametrize("invalid", [None, {}, {"work_id": None}, {"work_id": 3},
                                    {"work_id": ""}, {"work_id": "   "}])
def test_missing_or_invalid_work_id_refuses_instead_of_skipping_an_item(
    tmp_path: Path, lineage: dict, invalid,
):
    accepted = lineage["B"]
    ledger, policy = write_inputs(tmp_path, [invalid, item("W3", accepted, {})], [
        mandatory("render", "W3", accepted, [receipt(tmp_path, "render.json", accepted)])])
    with pytest.raises(PolicyRefused, match="work_id"):
        build_view(ledger, policy, tmp_path / "repo")


def test_mixed_historical_and_current_ledger(tmp_path: Path, lineage: dict) -> None:
    a, b, c = lineage["A"], lineage["B"], lineage["C"]
    snapshot = receipt(tmp_path, "snapshot-a.json", a, fields=("source_commit",))
    items = [
        item("HIST", b, {"render_pending": True}),
        item("NEWER", b, {"render_pending": True}),
        item("MISMATCH", b, {}),
        item("TIMED", b, {"render_pending": True}),
        item("STALE_TIME", b, {"render_pending": True}),
        item("FUTURE", b, {}),
        item("UNDECLARED", b, {"other_pending": True}),
        item("UNKNOWN", b, {"render_pending": True}),
        item("NO_CRITERIA", b, {}),
    ]
    criteria = [
        mandatory("hist", "HIST", b, [receipt(tmp_path, "b1.json", b)],
                  pending("/verification/render_pending", {"source_commit": a["source_commit"]},
                          evidence=[snapshot])),
        mandatory("newer", "NEWER", b, [receipt(tmp_path, "b2.json", b)],
                  pending("/verification/render_pending", {"source_commit": c["source_commit"]},
                          evidence=[receipt(tmp_path, "snapshot-c.json", c, fields=("source_commit",))])),
        mandatory("mismatch", "MISMATCH", b, [receipt(tmp_path, "a-receipt.json", a)]),
        mandatory("timed", "TIMED", b,
                  [receipt(tmp_path, "b3.json", b, observed_at="2026-11-08T05:40:00+00:00")],
                  pending("/verification/render_pending", as_of="2026-11-08T04:00:00+00:00")),
        mandatory("stale-time", "STALE_TIME", b,
                  [receipt(tmp_path, "b4.json", b, observed_at="2026-11-08T03:00:00+00:00")],
                  pending("/verification/render_pending", as_of="2026-11-08T04:00:00+00:00")),
        mandatory("future-ok", "FUTURE", b, [receipt(tmp_path, "b5.json", b)]),
        {"id": "calibration", "item": "FUTURE", "obligation": "future",
         "requirement": "measured in-envelope resistance calibration"},
        mandatory("undeclared", "UNDECLARED", b, [receipt(tmp_path, "b6.json", b)]),
        mandatory("unknown", "UNKNOWN", b, [receipt(tmp_path, "b7.json", b)],
                  pending("/verification/render_pending")),
    ]
    ledger, policy = write_inputs(tmp_path, items, criteria)
    view = by_id(build_view(ledger, policy, tmp_path / "repo"))

    hist = view["HIST"]["criteria"][0]
    assert view["HIST"]["current_status"] == "accepted"
    assert hist["pending"]["classification"] == "historical"
    assert hist["pending"]["ordering_basis"] == ["git_ancestry"]
    assert hist["supporting_receipts"][0]["sha256"] == criteria[0]["receipts"][0]["sha256"]

    # A newer pending flag (observed on a descendant) is not cleared by an older receipt.
    assert view["NEWER"]["current_status"] == "conflict"
    assert "not an ancestor" in " ".join(view["NEWER"]["criteria"][0]["reasons"])

    # A successful receipt for another source does not apply to the accepted source.
    mismatch = view["MISMATCH"]["criteria"][0]
    assert mismatch["status"] == "conflict" and mismatch["supporting_receipts"] == []
    assert "source identity" in " ".join(mismatch["reasons"])

    assert view["TIMED"]["criteria"][0]["pending"]["ordering_basis"] == ["timestamps"]
    assert view["TIMED"]["current_status"] == "accepted"
    assert view["STALE_TIME"]["current_status"] == "conflict"

    # Future obligations stay open without blocking current acceptance.
    future = {c["id"]: c for c in view["FUTURE"]["criteria"]}
    assert future["calibration"]["status"] == "open_future"
    assert view["FUTURE"]["current_status"] == "accepted"

    assert view["UNDECLARED"]["undeclared_pending"] == ["/verification/other_pending"]
    assert view["UNDECLARED"]["current_status"] == "conflict"
    assert view["UNKNOWN"]["criteria"][0]["pending"]["classification"] == "current_conflict"
    # A Done item without declared criteria is not presented as receipt-backed acceptance.
    assert view["NO_CRITERIA"]["current_status"] == "claimed_unreviewed"


def test_finalize_moves_only_proven_history_and_is_reverifiable(tmp_path: Path, lineage: dict) -> None:
    a, b = lineage["A"], lineage["B"]
    items = [item("W3", b, {"render_pending": True, "unrelated_note": "kept"}),
             item("W10", b, {})]
    criteria = [
        mandatory("render", "W3", b, [receipt(tmp_path, "render.json", b)],
                  pending("/verification/render_pending", {"source_commit": a["source_commit"]},
                          evidence=[receipt(tmp_path, "snap.json", a, fields=("source_commit",))])),
        mandatory("w10-gate", "W10", b, [receipt(tmp_path, "gate.json", b)]),
        {"id": "calibration", "item": "W10", "obligation": "future",
         "requirement": "physical calibration remains a future obligation"},
    ]
    ledger, policy = write_inputs(tmp_path, items, criteria)
    original = ledger.read_bytes()
    out, history = tmp_path / "proposed.json", tmp_path / "history" / "ledger-original.json"
    history.parent.mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "kayakgen.operations.ledger_finalization", "finalize",
         "--ledger", str(ledger), "--policy", str(policy), "--repo", str(tmp_path / "repo"),
         "--out", str(out), "--history", str(history)],
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert ledger.read_bytes() == original and history.read_bytes() == original
    proposed = json.loads(out.read_text())
    w3 = proposed["items"][0]
    assert "render_pending" not in w3["verification"]
    assert w3["verification"]["unrelated_note"] == "kept"
    assert w3["ledger_history"][0]["value"] is True
    assert w3["ledger_history"][0]["as_of"] == "unknown"
    assert w3["current_criteria"][0]["supporting_receipts"][0]["path"].endswith("render.json")
    assert proposed["items"][1]["current_criteria"][1]["status"] == "open_future"
    assert proposed["finalization"]["previous_ledger_sha256"] == hashlib.sha256(original).hexdigest()

    # The proposed ledger re-verifies against the same receipts, reading history in place.
    again = json.loads(policy.read_text())
    again["ledger"]["sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
    write_json(policy, again)
    view = build_view(out, policy, tmp_path / "repo")
    assert view["status"] == "consistent"
    assert by_id(view)["W3"]["criteria"][0]["pending"]["location"] == "ledger_history"

    # Existing outputs are never overwritten.
    second = subprocess.run(
        [sys.executable, "-m", "kayakgen.operations.ledger_finalization", "finalize",
         "--ledger", str(out), "--policy", str(policy), "--repo", str(tmp_path / "repo"),
         "--out", str(out.with_name("p2.json")), "--history", str(history)],
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}, capture_output=True, text=True, timeout=30)
    assert second.returncode == 2 and json.loads(second.stdout)["status"] == "refused"


def test_conflicting_view_refuses_finalization_and_tampered_receipt_conflicts(
    tmp_path: Path, lineage: dict,
) -> None:
    b = lineage["B"]
    spec = receipt(tmp_path, "render.json", b)
    ledger, policy = write_inputs(tmp_path, [item("W3", b, {})], [mandatory("render", "W3", b, [spec])])
    (tmp_path / "render.json").write_text(json.dumps({"status": "passed", **b}))
    view = build_view(ledger, policy, tmp_path / "repo")
    assert view["status"] == "conflict"
    assert "SHA-256 mismatch" in view["items"][0]["criteria"][0]["reasons"][0]
    with pytest.raises(PolicyRefused):
        propose_finalized(ledger, view)


def test_applicable_source_must_be_the_items_accepted_source(tmp_path: Path, lineage: dict) -> None:
    a, b = lineage["A"], lineage["B"]
    ledger, policy = write_inputs(tmp_path, [item("W3", b, {})],
                                  [mandatory("render", "W3", a, [receipt(tmp_path, "r.json", a)])])
    criterion = build_view(ledger, policy, tmp_path / "repo")["items"][0]["criteria"][0]
    assert criterion["status"] == "conflict"
    assert "accepted final_source_tree" in " ".join(criterion["reasons"])


def test_policy_refusals(tmp_path: Path, lineage: dict) -> None:
    b = lineage["B"]
    future_with_receipt = {"id": "f", "item": "W3", "obligation": "future", "requirement": "r",
                           "receipts": [receipt(tmp_path, "r.json", b)]}
    ledger, policy = write_inputs(tmp_path, [item("W3", b, {})], [future_with_receipt])
    with pytest.raises(PolicyRefused, match="future obligations"):
        build_view(ledger, policy)
    ledger, policy = write_inputs(tmp_path, [item("W3", b, {})], [
        mandatory("m", "W3", b, [receipt(tmp_path, "r2.json", b)], pending("/verification/missing"))])
    with pytest.raises(PolicyRefused, match="absent"):
        build_view(ledger, policy)
    ledger.write_text(ledger.read_text() + " ")
    with pytest.raises(PolicyRefused, match="ledger bytes"):
        build_view(ledger, policy)
