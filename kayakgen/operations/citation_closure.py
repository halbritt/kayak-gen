"""Bind doctrine citation classifications to the phase and packet that served them.

The installed Pincite ``pincite-citations`` command remains the only
classifier. This module retains the exact packet and observation bytes it
classified, checks that the report belongs to them, and decides closure from
the per-citation classifications rather than from the classifier's exit code.
Corrections are separate records that keep the original refused closure.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from kayakgen.operations.completion import CompletionRefused, _decode_json

SCHEMA_VERSION = "kayakgen-citation-closure/1"
CORRECTION_SCHEMA_VERSION = "kayakgen-citation-correction/1"
CLASSIFICATION_SCHEMA = "citation-classification/2"
PACKET_SCHEMAS = ("evidence-packet/2", "evidence-packet/3")
PHASE = re.compile(r"[a-z][a-z0-9-]{0,63}")
SHA256 = re.compile(r"[0-9a-f]{64}")
DOCTRINE_KINDS = ("concept-id", "formulation-id")
LOCATOR_KIND = "source-locator"
ACCEPTED = (
    "accepted-packet-citation", "accepted-packet-provenance", "accepted-external-provenance",
)
LIMITS = (
    "Mechanical classifier closure only: it records which packet served each cited "
    "identifier. It is not runtime verification, human adjudication or task acceptance."
)


class ClosureRefused(ValueError):
    """A closure, verification or correction input does not meet the contract."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json(raw: bytes, label: str) -> object:
    try:
        return _decode_json(raw, label)
    except CompletionRefused as exc:
        raise ClosureRefused(str(exc)) from exc


def _read(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ClosureRefused(f"cannot read {label} {path}: {exc}") from exc


def _write_new(path: Path, raw: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(raw)


def _dump(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def release_home() -> Path:
    configured = os.environ.get("PINCITE_RELEASE_HOME")
    return Path(configured) if configured else Path.home() / ".local/share/pincite/release"


def installed_classifier(home: Path) -> tuple[Path, Path]:
    return (home / "doctrine" / "bin" / "pincite-citations",
            home / "doctrine" / "runtime" / "doctrine-index.sqlite3")


def _packet_identity(raw: bytes) -> dict[str, object]:
    packet = _json(raw, "evidence packet")
    if not isinstance(packet, dict) or packet.get("schema_version") not in PACKET_SCHEMAS:
        raise ClosureRefused(f"packet schema_version must be one of {list(PACKET_SCHEMAS)}")
    packet_id, content = packet.get("packet_id"), packet.get("packet_content_sha256")
    if not isinstance(packet_id, str) or not packet_id.startswith("pkt-"):
        raise ClosureRefused("packet must carry a pkt- packet_id")
    if not isinstance(content, str) or not SHA256.fullmatch(content):
        raise ClosureRefused("packet must carry a lowercase packet_content_sha256")
    return {
        "schema_version": packet["schema_version"], "packet_id": packet_id,
        "packet_content_sha256": content, "sha256": _sha256(raw),
        "corpus_version": packet.get("corpus_version"),
        "doctrine_version": packet.get("doctrine_version"),
    }


def _observed(raw: bytes) -> list[tuple[str, str]]:
    document = _json(raw, "citation observations")
    if not isinstance(document, dict) or document.get("schema_version") != (
        "citation-observations/1"
    ) or not isinstance(document.get("citations"), list):
        raise ClosureRefused("observations must be citation-observations/1 with a citations list")
    observed = []
    for citation in document["citations"]:
        if not isinstance(citation, dict) or not all(
            isinstance(citation.get(key), str) for key in ("kind", "identifier")
        ):
            raise ClosureRefused("each observation needs string kind and identifier")
        observed.append((citation["kind"], citation["identifier"]))
    return observed


def _disposition(kind: str, classification: object) -> str:
    if classification == "valid-packet-citation":
        return "accepted-packet-provenance" if kind == LOCATOR_KIND else "accepted-packet-citation"
    if classification == "injected-non-activated-citation":
        return "refused-not-served-by-packet"
    if classification == "foreign-citation":
        # A locator outside the doctrine index is ordinary repository or
        # evidence provenance; a foreign doctrine identifier names nothing.
        if kind == LOCATOR_KIND:
            return "accepted-external-provenance"
        return "refused-unknown-doctrine-identifier"
    return "refused-unrecognized-classification"


def evaluate(
    packet: dict[str, object], observed: list[tuple[str, str]],
    exit_code: int | None, stdout: bytes,
) -> tuple[str, list[str], list[dict[str, object]], dict[str, object]]:
    """Derive closure status from one retained classifier result."""
    if exit_code != 0:
        return "classifier_failed", [f"classifier exit code {exit_code}"], [], {}
    try:
        report = _json(stdout, "classifier report")
    except ClosureRefused as exc:
        return "classifier_failed", [str(exc)], [], {}
    if not isinstance(report, dict):
        return "classifier_failed", ["classifier report must be an object"], [], {}
    expected = {
        "schema_version": CLASSIFICATION_SCHEMA, "packet_id": packet["packet_id"],
        "packet_content_sha256": packet["packet_content_sha256"],
        "output_citation_channel": "structured",
    }
    mismatched = [key for key, value in expected.items() if report.get(key) != value]
    citations = report.get("citations")
    if not isinstance(citations, list) or [
        (c.get("kind"), c.get("identifier")) if isinstance(c, dict) else None
        for c in citations
    ] != observed or any(c.get("origin") != "output" for c in citations):
        mismatched.append("citations")
    if mismatched:
        return "classifier_failed", [
            f"classifier report is not bound to this packet and observations: {mismatched}"
        ], [], {}
    rows = [{
        "kind": c["kind"], "identifier": c["identifier"],
        "classification": c.get("classification"),
        "disposition": _disposition(c["kind"], c.get("classification")),
    } for c in citations]
    reasons = [f"{row['kind']} {row['identifier']!r}: {row['classification']} -> "
               f"{row['disposition']}" for row in rows if row["disposition"] not in ACCEPTED]
    meta = {key: report.get(key) for key in
            ("schema_version", "index_content_hash", "output_citation_channel", "receipt_id")}
    return ("refused" if reasons else "closed"), reasons, rows, meta


def _classify(home: Path, packet_path: Path, observations_path: Path):
    classifier, index = installed_classifier(home)
    argv = [str(classifier), "--index", str(index), "--packet", str(packet_path),
            "--observations", str(observations_path)]
    try:
        completed = subprocess.run(argv, capture_output=True, check=False)
    except OSError as exc:
        return argv, None, b"", f"cannot run classifier: {exc}\n".encode()
    return argv, completed.returncode, completed.stdout, completed.stderr


def _file_sha(path: Path) -> str | None:
    try:
        return _sha256(path.read_bytes())
    except OSError:
        return None


def close(phase: str, packet_path: Path, observations_path: Path, out: Path,
          home: Path | None = None) -> dict[str, object]:
    """Classify one phase's observations against its packet and retain the result."""
    if not PHASE.fullmatch(phase):
        raise ClosureRefused("phase must match [a-z][a-z0-9-]{0,63}")
    packet_raw = _read(packet_path, "packet")
    observations_raw = _read(observations_path, "observations")
    packet = _packet_identity(packet_raw)
    observed = _observed(observations_raw)
    home = home or release_home()
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ClosureRefused(f"closure directory already exists and is never replaced: {out}") \
            from exc
    retained_packet, retained_observations = out / "packet.json", out / "observations.json"
    _write_new(retained_packet, packet_raw)
    _write_new(retained_observations, observations_raw)
    argv, exit_code, stdout, stderr = _classify(home, retained_packet, retained_observations)
    _write_new(out / "classification.json", stdout)
    _write_new(out / "classifier.stderr", stderr)
    status, reasons, rows, meta = evaluate(packet, observed, exit_code, stdout)
    classifier, index = installed_classifier(home)
    closure = {
        "schema_version": SCHEMA_VERSION, "created_at": _now(), "phase": phase,
        "status": status, "reasons": reasons,
        "packet": {**packet, "source_path": str(packet_path.absolute()),
                   "retained": retained_packet.name},
        "observations": {"sha256": _sha256(observations_raw),
                         "source_path": str(observations_path.absolute()),
                         "retained": retained_observations.name},
        "classifier": {
            "release_home": str(home), "executable_sha256": _file_sha(classifier),
            "index_sha256": _file_sha(index), "argv": argv, "exit_code": exit_code,
            "stdout": {"retained": "classification.json", "sha256": _sha256(stdout)},
            "stderr": {"retained": "classifier.stderr", "sha256": _sha256(stderr)},
        },
        "classification": meta, "citations": rows, "limits": LIMITS,
    }
    _write_new(out / "closure.json", _dump(closure))
    return closure


def _retained(directory: Path, entry: object, label: str) -> bytes:
    if not isinstance(entry, dict) or not isinstance(entry.get("retained"), str) \
            or "/" in entry["retained"]:
        raise ClosureRefused(f"closure {label} must name a retained file")
    raw = _read(directory / entry["retained"], f"retained {label}")
    if _sha256(raw) != entry.get("sha256"):
        raise ClosureRefused(f"retained {label} bytes changed: {directory / entry['retained']}")
    return raw


def verify(closure_path: Path, home: Path | None = None) -> dict[str, object]:
    """Recheck retained bytes, rerun the classifier and rederive the recorded status."""
    raw = _read(closure_path, "closure")
    closure = _json(raw, "closure")
    if not isinstance(closure, dict) or closure.get("schema_version") != SCHEMA_VERSION:
        raise ClosureRefused(f"closure schema_version must be {SCHEMA_VERSION}")
    directory = closure_path.absolute().parent
    packet_raw = _retained(directory, closure.get("packet"), "packet")
    observed = _observed(_retained(directory, closure.get("observations"), "observations"))
    recorded = closure.get("classifier")
    if not isinstance(recorded, dict):
        raise ClosureRefused("closure must record its classifier run")
    stdout = _retained(directory, recorded.get("stdout"), "classifier stdout")
    _retained(directory, recorded.get("stderr"), "classifier stderr")
    packet = _packet_identity(packet_raw)
    if any(closure["packet"].get(key) != value for key, value in packet.items()):
        raise ClosureRefused("recorded packet identity does not match retained packet")
    status, reasons, rows, _meta = evaluate(packet, observed, recorded.get("exit_code"), stdout)
    if (status, reasons, rows) != (closure.get("status"), closure.get("reasons"),
                                   closure.get("citations")):
        raise ClosureRefused("recorded status or citations differ from the retained report")
    _argv, exit_code, rerun, _stderr = _classify(
        home or release_home(), directory / closure["packet"]["retained"],
        directory / closure["observations"]["retained"])
    if exit_code != recorded.get("exit_code") or _sha256(rerun) != _sha256(stdout):
        raise ClosureRefused("installed classifier no longer reproduces the retained report")
    if not PHASE.fullmatch(str(closure.get("phase"))):
        raise ClosureRefused("closure phase is invalid")
    return {**closure, "_closure_sha256": _sha256(raw), "_path": str(closure_path.absolute())}


def _reference(closure: dict[str, object]) -> dict[str, object]:
    return {"path": closure["_path"], "closure_sha256": closure["_closure_sha256"],
            "phase": closure["phase"], "status": closure["status"],
            "packet_id": closure["packet"]["packet_id"],
            "packet_sha256": closure["packet"]["sha256"]}


def _key(row: dict[str, object]) -> tuple[str, str]:
    return row["kind"], row["identifier"]


def correct(original_path: Path, corrected_path: Path, out: Path,
            attributions: dict[str, Path], withdrawals: dict[str, str],
            home: Path | None = None) -> dict[str, object]:
    """Record an attribution correction for a refused closure without replacing it."""
    if out.exists():
        raise ClosureRefused(f"correction record already exists and is never replaced: {out}")
    original = verify(original_path, home)
    corrected = verify(corrected_path, home)
    if original["status"] != "refused":
        raise ClosureRefused("only a refused original closure can be corrected")
    if corrected["status"] != "closed":
        raise ClosureRefused("corrected closure must be closed")
    if corrected["phase"] != original["phase"]:
        raise ClosureRefused("corrected closure must keep the original phase")
    if corrected["packet"]["sha256"] != original["packet"]["sha256"]:
        raise ClosureRefused("corrected closure must classify the original immutable packet")
    refused = [row for row in original["citations"] if row["disposition"] not in ACCEPTED]
    kept = [_key(row) for row in original["citations"] if row["disposition"] in ACCEPTED]
    if [_key(row) for row in corrected["citations"]] != kept:
        raise ClosureRefused(
            "corrected citations must equal the original accepted citations in order")
    refused_ids = [row["identifier"] for row in refused]
    disposed = list(attributions) + list(withdrawals)
    if sorted(disposed) != sorted(set(refused_ids)) or len(disposed) != len(set(disposed)):
        raise ClosureRefused(
            f"every refused citation needs exactly one attribution or withdrawal: {refused_ids}")
    trail_attributions = []
    for identifier, discovery_path in attributions.items():
        discovery = verify(discovery_path, home)
        if discovery["phase"] == original["phase"]:
            raise ClosureRefused(
                f"attribution for {identifier!r} must come from a different phase")
        if discovery["status"] != "closed":
            raise ClosureRefused(f"attribution closure for {identifier!r} is not closed")
        kinds = {row["kind"] for row in refused if row["identifier"] == identifier}
        served = [row for row in discovery["citations"] if row["identifier"] == identifier
                  and row["kind"] in kinds and row["disposition"] == "accepted-packet-citation"]
        if not served:
            raise ClosureRefused(
                f"{identifier!r} was not cited and served in the attributed closure")
        trail_attributions.append({"kind": served[0]["kind"], "identifier": identifier,
                                   **_reference(discovery)})
    trail = {
        "schema_version": CORRECTION_SCHEMA_VERSION, "created_at": _now(),
        "phase": original["phase"], "original": _reference(original),
        "corrected": _reference(corrected), "attributions": trail_attributions,
        "withdrawals": [{"kind": row["kind"], "identifier": row["identifier"],
                         "reason": withdrawals[row["identifier"]]}
                        for row in refused if row["identifier"] in withdrawals],
        "evidence_effect": {"runtime_verification": "none", "acceptance": "none"},
        "limits": "An attribution correction re-labels where doctrine was served. It creates no "
                  "runtime verification or acceptance evidence and keeps the original closure.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    _write_new(out, _dump(trail))
    return trail


def _pairs(values: Sequence[str], label: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for value in values:
        key, separator, content = value.partition("=")
        if not separator or not key or not content or key in pairs:
            raise ClosureRefused(f"{label} must be unique IDENTIFIER=VALUE pairs")
        pairs[key] = content
    return pairs


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    closing = commands.add_parser("close", help="classify one phase against its packet")
    closing.add_argument("--phase", required=True)
    closing.add_argument("--packet", type=Path, required=True)
    closing.add_argument("--observations", type=Path, required=True)
    closing.add_argument("--out", type=Path, required=True, help="new closure directory")
    checking = commands.add_parser("verify", help="recheck a retained closure")
    checking.add_argument("closure", type=Path)
    fixing = commands.add_parser("correct", help="record an attribution correction")
    fixing.add_argument("--original", type=Path, required=True)
    fixing.add_argument("--corrected", type=Path, required=True)
    fixing.add_argument("--out", type=Path, required=True, help="new correction JSON file")
    fixing.add_argument("--attribute", action="append", default=[],
                        metavar="IDENTIFIER=CLOSURE")
    fixing.add_argument("--withdraw", action="append", default=[], metavar="IDENTIFIER=REASON")
    args = parser.parse_args(argv)
    try:
        if args.command == "close":
            closure = close(args.phase, args.packet, args.observations, args.out)
            print(json.dumps({"status": closure["status"], "phase": closure["phase"],
                              "packet_id": closure["packet"]["packet_id"],
                              "closure": str((args.out / "closure.json").absolute()),
                              "reasons": closure["reasons"]}))
            return {"closed": 0, "refused": 2}.get(closure["status"], 1)
        if args.command == "verify":
            closure = verify(args.closure)
            print(json.dumps({"status": "verified", "closure_status": closure["status"],
                              "closure_sha256": closure["_closure_sha256"]}))
            return 0
        trail = correct(args.original, args.corrected, args.out,
                        {k: Path(v) for k, v in _pairs(args.attribute, "--attribute").items()},
                        _pairs(args.withdraw, "--withdraw"))
        print(json.dumps({"status": "recorded", "correction": str(args.out.absolute()),
                          "attributions": len(trail["attributions"]),
                          "withdrawals": len(trail["withdrawals"])}))
        return 0
    except ClosureRefused as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
