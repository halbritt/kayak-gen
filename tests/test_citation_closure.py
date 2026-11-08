"""Citation closure binds classifier results to the phase and packet that served them.

The classifier here is a canned-output stand-in at the installed release
layout: it echoes the caller's observations with preset classifications and
never decides a classification itself. Acceptance against the actual
installed Pincite classifier is retained as external evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

FAKE_CLASSIFIER = f"""#!{sys.executable}
import json, os, sys
args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
packet = json.load(open(args["--packet"], encoding="utf-8"))
observations = json.load(open(args["--observations"], encoding="utf-8"))
labels = json.loads(os.environ["FAKE_CLASSIFICATIONS"])
report = {{
    "schema_version": "citation-classification/2",
    "packet_id": packet["packet_id"],
    "packet_content_sha256": packet["packet_content_sha256"],
    "corpus_version": packet["corpus_version"],
    "doctrine_version": packet["doctrine_version"],
    "index_content_hash": "c" * 64,
    "receipt_id": None,
    "output_citation_channel": "structured",
    "citations": [
        {{"origin": "output", "kind": c["kind"], "identifier": c["identifier"],
          "classification": labels[c["identifier"]]}}
        for c in observations["citations"]
    ],
}}
report.update(json.loads(os.environ.get("FAKE_OVERRIDE", "{{}}")))
sys.stderr.write("fake classifier ran\\n")
print(json.dumps(report, indent=2))
raise SystemExit(int(os.environ.get("FAKE_EXIT", "0")))
"""

VALID = "valid-packet-citation"
INJECTED = "injected-non-activated-citation"
FOREIGN = "foreign-citation"


@pytest.fixture()
def home(tmp_path: Path) -> Path:
    release = tmp_path / "pincite-release"
    (release / "doctrine" / "bin").mkdir(parents=True)
    (release / "doctrine" / "runtime").mkdir(parents=True)
    classifier = release / "doctrine" / "bin" / "pincite-citations"
    classifier.write_text(FAKE_CLASSIFIER, encoding="utf-8")
    classifier.chmod(0o755)
    (release / "doctrine" / "runtime" / "doctrine-index.sqlite3").write_bytes(b"index")
    return release


def packet(tmp_path: Path, name: str, activated: list[str]) -> Path:
    digest = hashlib.sha256(name.encode()).hexdigest()
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps({
        "schema_version": "evidence-packet/3",
        "packet_id": f"pkt-{digest[:16]}",
        "packet_content_sha256": digest,
        "corpus_version": "corpus-test",
        "doctrine_version": "doctrine-test",
        "activated_concepts": activated,
    }), encoding="utf-8")
    return path


def observations(tmp_path: Path, name: str, citations: list[tuple[str, str]]) -> Path:
    path = tmp_path / f"{name}-observations.json"
    path.write_text(json.dumps({
        "schema_version": "citation-observations/1",
        "citations": [{"kind": kind, "identifier": ident} for kind, ident in citations],
    }), encoding="utf-8")
    return path


def run(
    home: Path, *arguments: str, labels: dict[str, str] | None = None,
    override: dict | None = None, exit_code: int = 0,
) -> subprocess.CompletedProcess:
    env = {
        **os.environ, "PYTHONPATH": str(REPO_ROOT), "PINCITE_RELEASE_HOME": str(home),
        "FAKE_CLASSIFICATIONS": json.dumps(labels or {}),
        "FAKE_OVERRIDE": json.dumps(override or {}), "FAKE_EXIT": str(exit_code),
    }
    return subprocess.run(
        [sys.executable, "-m", "kayakgen.operations.citation_closure", *arguments],
        env=env, capture_output=True, text=True, timeout=30,
    )


def close(home, tmp_path, phase, packet_path, obs_path, out, **kwargs):
    return run(home, "close", "--phase", phase, "--packet", str(packet_path),
               "--observations", str(obs_path), "--out", str(out), **kwargs)


def record(out: Path) -> dict:
    return json.loads((out / "closure.json").read_text(encoding="utf-8"))


def test_closure_records_phase_and_packet_identity_and_runs_installed_classifier(
    tmp_path: Path, home: Path,
) -> None:
    final = packet(tmp_path, "final", ["concept-a"])
    obs = observations(tmp_path, "final", [("concept-id", "concept-a")])
    out = tmp_path / "closures" / "final"
    result = close(home, tmp_path, "final", final, obs, out, labels={"concept-a": VALID})
    assert result.returncode == 0, result.stdout + result.stderr
    closure = record(out)
    assert closure["status"] == "closed"
    assert closure["phase"] == "final"
    raw = final.read_bytes()
    assert closure["packet"]["packet_id"] == json.loads(raw)["packet_id"]
    assert closure["packet"]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert (out / "packet.json").read_bytes() == raw
    classifier = home / "doctrine" / "bin" / "pincite-citations"
    assert closure["classifier"]["argv"][0] == str(classifier)
    assert closure["classifier"]["argv"][closure["classifier"]["argv"].index("--packet") + 1] \
        == str(out / "packet.json")
    assert closure["classifier"]["executable_sha256"] == hashlib.sha256(
        classifier.read_bytes()).hexdigest()
    assert closure["classifier"]["exit_code"] == 0
    assert (out / "classifier.stderr").read_text() == "fake classifier ran\n"
    assert closure["citations"] == [{
        "kind": "concept-id", "identifier": "concept-a",
        "classification": VALID, "disposition": "accepted-packet-citation",
    }]
    assert json.loads(result.stdout)["status"] == "closed"


def test_classifier_exit_zero_with_non_activated_concept_refuses_closure(
    tmp_path: Path, home: Path,
) -> None:
    final = packet(tmp_path, "final", ["concept-a"])
    obs = observations(tmp_path, "final", [("concept-id", "concept-a"),
                                           ("concept-id", "concept-b")])
    out = tmp_path / "final"
    result = close(home, tmp_path, "final", final, obs, out,
                   labels={"concept-a": VALID, "concept-b": INJECTED})
    assert result.returncode == 2, result.stdout + result.stderr
    closure = record(out)
    assert closure["classifier"]["exit_code"] == 0
    assert closure["status"] == "refused"
    assert closure["citations"][1]["disposition"] == "refused-not-served-by-packet"
    assert "concept-b" in " ".join(closure["reasons"])


def test_foreign_repository_locator_is_external_provenance_not_doctrine(
    tmp_path: Path, home: Path,
) -> None:
    final = packet(tmp_path, "final", ["concept-a"])
    obs = observations(tmp_path, "final", [("concept-id", "concept-a"),
                                           ("source-locator", "kayakgen/operations/gate.py")])
    out = tmp_path / "final"
    result = close(home, tmp_path, "final", final, obs, out, labels={
        "concept-a": VALID, "kayakgen/operations/gate.py": FOREIGN})
    assert result.returncode == 0, result.stdout + result.stderr
    assert record(out)["citations"][1]["disposition"] == "accepted-external-provenance"


def test_foreign_concept_identifier_is_refused(tmp_path: Path, home: Path) -> None:
    final = packet(tmp_path, "final", ["concept-a"])
    obs = observations(tmp_path, "final", [("concept-id", "made-up")])
    out = tmp_path / "final"
    result = close(home, tmp_path, "final", final, obs, out, labels={"made-up": FOREIGN})
    assert result.returncode == 2
    assert record(out)["citations"][0]["disposition"] == "refused-unknown-doctrine-identifier"


def test_classifier_failure_is_retained_and_not_a_closure(tmp_path: Path, home: Path) -> None:
    final = packet(tmp_path, "final", ["concept-a"])
    obs = observations(tmp_path, "final", [("concept-id", "concept-a")])
    out = tmp_path / "final"
    result = close(home, tmp_path, "final", final, obs, out,
                   labels={"concept-a": VALID}, exit_code=1)
    assert result.returncode == 1
    closure = record(out)
    assert closure["status"] == "classifier_failed"
    assert closure["classifier"]["exit_code"] == 1
    assert closure["citations"] == []


@pytest.mark.parametrize("override", [
    {"packet_content_sha256": "0" * 64},
    {"output_citation_channel": "text-fallback"},
    {"citations": []},
    {"schema_version": "citation-classification/1"},
])
def test_report_not_bound_to_the_packet_and_observations_is_refused(
    tmp_path: Path, home: Path, override: dict,
) -> None:
    final = packet(tmp_path, "final", ["concept-a"])
    obs = observations(tmp_path, "final", [("concept-id", "concept-a")])
    out = tmp_path / "final"
    result = close(home, tmp_path, "final", final, obs, out,
                   labels={"concept-a": VALID}, override=override)
    assert result.returncode == 1, result.stdout
    assert record(out)["status"] == "classifier_failed"


def test_existing_closure_is_never_overwritten(tmp_path: Path, home: Path) -> None:
    final = packet(tmp_path, "final", ["concept-a"])
    obs = observations(tmp_path, "final", [("concept-id", "concept-b")])
    out = tmp_path / "final"
    assert close(home, tmp_path, "final", final, obs, out,
                 labels={"concept-b": INJECTED}).returncode == 2
    before = (out / "closure.json").read_bytes()
    again = close(home, tmp_path, "final", final, obs, out, labels={"concept-b": VALID})
    assert again.returncode == 2
    assert json.loads(again.stdout)["status"] == "refused"
    assert (out / "closure.json").read_bytes() == before


def test_verify_reruns_classifier_and_detects_edited_records(tmp_path: Path, home: Path) -> None:
    final = packet(tmp_path, "final", ["concept-a"])
    obs = observations(tmp_path, "final", [("concept-id", "concept-b")])
    out = tmp_path / "final"
    labels = {"concept-b": INJECTED}
    close(home, tmp_path, "final", final, obs, out, labels=labels)
    verified = run(home, "verify", str(out / "closure.json"), labels=labels)
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert json.loads(verified.stdout)["closure_status"] == "refused"

    closure = record(out)
    closure["status"] = "closed"
    (out / "closure.json").write_text(json.dumps(closure), encoding="utf-8")
    edited = run(home, "verify", str(out / "closure.json"), labels=labels)
    assert edited.returncode == 2
    assert "status" in json.loads(edited.stdout)["reason"]


def correction_case(tmp_path: Path, home: Path, *, discovery_cites: bool = True,
                    discovery_phase: str = "discovery"):
    labels = {"concept-a": VALID, "concept-b": INJECTED}
    final = packet(tmp_path, "final", ["concept-a"])
    original = tmp_path / "c" / "final-original"
    close(home, tmp_path, "final", final,
          observations(tmp_path, "orig", [("concept-id", "concept-a"),
                                          ("concept-id", "concept-b")]),
          original, labels=labels)
    corrected = tmp_path / "c" / "final-corrected"
    close(home, tmp_path, "final", final,
          observations(tmp_path, "fixed", [("concept-id", "concept-a")]),
          corrected, labels=labels)
    discovery = tmp_path / "c" / "discovery"
    disc_packet = packet(tmp_path, "discovery", ["concept-a", "concept-b"])
    cited = [("concept-id", "concept-b")] if discovery_cites else [("concept-id", "concept-a")]
    close(home, tmp_path, discovery_phase, disc_packet,
          observations(tmp_path, "disc", cited), discovery,
          labels={"concept-a": VALID, "concept-b": VALID})
    return original, corrected, discovery


def correct(home, original, corrected, out, *extra, labels):
    return run(home, "correct", "--original", str(original / "closure.json"),
               "--corrected", str(corrected / "closure.json"), "--out", str(out),
               *extra, labels=labels)


@pytest.fixture()
def stateful_home(home: Path) -> Path:
    """Classifier stand-in that keys canned labels by packet id and identifier."""
    classifier = home / "doctrine" / "bin" / "pincite-citations"
    text = classifier.read_text(encoding="utf-8").replace(
        'labels[c["identifier"]]',
        'labels.get(packet["packet_id"] + "/" + c["identifier"], labels.get(c["identifier"]))',
    )
    classifier.write_text(text, encoding="utf-8")
    return home


def packet_labels(tmp_path: Path) -> dict[str, str]:
    final = json.loads((tmp_path / "final.json").read_text())["packet_id"]
    return {f"{final}/concept-a": VALID, f"{final}/concept-b": INJECTED,
            "concept-a": VALID, "concept-b": VALID}


def test_discovery_attribution_corrects_final_closure_without_new_evidence(
    tmp_path: Path, stateful_home: Path,
) -> None:
    home = stateful_home
    original, corrected, discovery = correction_case(tmp_path, home)
    labels = packet_labels(tmp_path)
    for directory in (original, corrected, discovery):
        assert run(home, "verify", str(directory / "closure.json"), labels=labels).returncode == 0
    assert record(original)["status"] == "refused"
    preserved = {p: p.read_bytes() for p in original.iterdir()}
    out = tmp_path / "correction.json"
    result = correct(home, original, corrected, out, "--attribute",
                     f"concept-b={discovery / 'closure.json'}", labels=labels)
    assert result.returncode == 0, result.stdout + result.stderr
    trail = json.loads(out.read_text())
    assert trail["original"]["status"] == "refused"
    assert trail["original"]["closure_sha256"] == hashlib.sha256(
        preserved[original / "closure.json"]).hexdigest()
    assert trail["attributions"][0]["identifier"] == "concept-b"
    assert trail["attributions"][0]["phase"] == "discovery"
    assert trail["attributions"][0]["packet_id"] == record(discovery)["packet"]["packet_id"]
    assert trail["evidence_effect"] == {"runtime_verification": "none", "acceptance": "none"}
    assert {p: p.read_bytes() for p in original.iterdir()} == preserved
    # The correction record itself is never replaced either.
    assert not run(home, "correct", "--original", str(original / "closure.json"),
                   "--corrected", str(corrected / "closure.json"), "--out", str(out),
                   "--attribute", f"concept-b={discovery / 'closure.json'}",
                   labels=labels).returncode == 0


def test_activation_without_discovery_consumption_cannot_attribute(
    tmp_path: Path, stateful_home: Path,
) -> None:
    original, corrected, discovery = correction_case(
        tmp_path, stateful_home, discovery_cites=False)
    result = correct(stateful_home, original, corrected, tmp_path / "correction.json",
                     "--attribute", f"concept-b={discovery / 'closure.json'}",
                     labels=packet_labels(tmp_path))
    assert result.returncode == 2
    assert "concept-b" in json.loads(result.stdout)["reason"]
    assert not (tmp_path / "correction.json").exists()


def test_same_phase_closure_cannot_serve_as_discovery_attribution(
    tmp_path: Path, stateful_home: Path,
) -> None:
    original, corrected, discovery = correction_case(
        tmp_path, stateful_home, discovery_phase="final")
    result = correct(stateful_home, original, corrected, tmp_path / "correction.json",
                     "--attribute", f"concept-b={discovery / 'closure.json'}",
                     labels=packet_labels(tmp_path))
    assert result.returncode == 2
    assert "phase" in json.loads(result.stdout)["reason"]


def test_every_refused_citation_needs_an_explicit_disposition(
    tmp_path: Path, stateful_home: Path,
) -> None:
    original, corrected, _discovery = correction_case(tmp_path, stateful_home)
    labels = packet_labels(tmp_path)
    missing = correct(stateful_home, original, corrected, tmp_path / "a.json", labels=labels)
    assert missing.returncode == 2
    withdrawn = correct(stateful_home, original, corrected, tmp_path / "b.json",
                        "--withdraw", "concept-b=cited in error", labels=labels)
    assert withdrawn.returncode == 0, withdrawn.stdout
    trail = json.loads((tmp_path / "b.json").read_text())
    assert trail["withdrawals"] == [{"kind": "concept-id", "identifier": "concept-b",
                                     "reason": "cited in error"}]


def test_correction_cannot_add_citations_or_change_packet(
    tmp_path: Path, stateful_home: Path,
) -> None:
    home = stateful_home
    original, _corrected, discovery = correction_case(tmp_path, home)
    labels = packet_labels(tmp_path)
    labels["concept-c"] = VALID
    final = tmp_path / "final.json"
    added = tmp_path / "c" / "added"
    close(home, tmp_path, "final", final,
          observations(tmp_path, "added", [("concept-id", "concept-a"),
                                           ("concept-id", "concept-c")]),
          added, labels=labels)
    result = correct(home, original, added, tmp_path / "x.json", "--attribute",
                     f"concept-b={discovery / 'closure.json'}", labels=labels)
    assert result.returncode == 2
    assert "original" in json.loads(result.stdout)["reason"]

    other = tmp_path / "c" / "other-packet"
    close(home, tmp_path, "final", packet(tmp_path, "other", ["concept-a"]),
          observations(tmp_path, "other", [("concept-id", "concept-a")]), other, labels=labels)
    result = correct(home, original, other, tmp_path / "y.json", "--attribute",
                     f"concept-b={discovery / 'closure.json'}", labels=labels)
    assert result.returncode == 2
    assert "packet" in json.loads(result.stdout)["reason"]
