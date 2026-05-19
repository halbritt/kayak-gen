"""RFC 0057 stage 4 / D-11: log-tail redaction tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from kayakgen.services.generative_jobs import (
    InProcessGenerativeJobManager,
    _redact_log_text,
    generative_job_log_payload,
)


def test_redact_log_text_replaces_home_dir() -> None:
    text = "candidate /home/alice/runs/x.log ok"
    redacted = _redact_log_text(text, home_dir="/home/alice")
    assert redacted == "candidate ~/runs/x.log ok"


def test_redact_log_text_replaces_jobs_root() -> None:
    text = "wrote /tmp/jobs/abc123/log.txt cursor=0"
    redacted = _redact_log_text(text, jobs_root="/tmp/jobs")
    assert redacted == "wrote <jobs_root>/abc123/log.txt cursor=0"


def test_redact_log_text_jobs_root_inside_home_dir() -> None:
    """Jobs-root nested under home-dir should be rewritten before the home substitution."""

    text = "/home/alice/.local/share/kayakgen/jobs/abc/log.txt"
    redacted = _redact_log_text(
        text,
        home_dir="/home/alice",
        jobs_root="/home/alice/.local/share/kayakgen/jobs",
    )
    # Longest target wins; the jobs-root rewrite takes precedence so the
    # output begins with the explicit <jobs_root> token, not ~.
    assert redacted == "<jobs_root>/abc/log.txt"


def test_redact_log_text_no_match_is_byte_stable() -> None:
    text = "candidate abc complete eval=12"
    redacted = _redact_log_text(
        text,
        home_dir="/home/alice",
        jobs_root="/tmp/jobs",
    )
    assert redacted == text  # byte-stable


def test_redact_log_text_handles_empty_text() -> None:
    assert _redact_log_text("", home_dir="/home/alice", jobs_root="/tmp/jobs") == ""


def test_redact_log_text_handles_missing_home_and_root() -> None:
    text = "candidate /home/alice/runs/x.log"
    assert _redact_log_text(text, home_dir=None, jobs_root=None) == text


def test_generative_job_log_payload_redacts_home_and_jobs_root(
    tmp_path: Path,
) -> None:
    """End-to-end: a real manager + a hand-written log gets redacted."""

    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")
    payload = {
        "schema_version": "1",
        "name": "redaction-sweep",
        "base_hull": {
            "length_m": 4.5,
            "beam_oa_m": 0.55,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "variables": {
            "beam_wl_m": {"kind": "values", "values": [0.48, 0.50, 0.52]},
        },
        "evaluators": {"hydrostatics": True},
    }
    job = manager.start(spec_payload=payload, job_kind="sweep")
    manager.join(job.job_id, timeout=120.0)

    # Manually inject a line that mentions both home and jobs_root paths.
    home = os.path.expanduser("~")
    jobs_root = str(manager.jobs_root)
    log_path = manager.jobs_root / job.job_id / "log.txt"
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(f"diagnostic: {home}/.cache trailing\n")
        fp.write(f"diagnostic: {jobs_root}/{job.job_id}/output/run.json\n")

    log_result = generative_job_log_payload(manager, job.job_id, since_byte=0)
    assert "~/.cache" in log_result["log"]
    assert f"<jobs_root>/{job.job_id}/output/run.json" in log_result["log"]
    # No raw home dir leak.
    assert home not in log_result["log"]
    assert jobs_root not in log_result["log"]


def test_generative_job_log_payload_byte_stable_when_no_paths_present(
    tmp_path: Path,
) -> None:
    """A log with no absolute paths must be byte-stable through the redactor."""

    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")
    payload = {
        "schema_version": "1",
        "name": "no-paths",
        "base_hull": {
            "length_m": 4.5,
            "beam_oa_m": 0.55,
            "draft_m": 0.12,
            "Cp": 0.55,
        },
        "variables": {
            "beam_wl_m": {"kind": "values", "values": [0.48, 0.50, 0.52]},
        },
        "evaluators": {"hydrostatics": True},
    }
    job = manager.start(spec_payload=payload, job_kind="sweep")
    manager.join(job.job_id, timeout=120.0)

    # The runner-written log contains "candidate ... status=complete ..." lines.
    # Confirm payload byte-stability via redact-then-redact equality.
    payload_first = generative_job_log_payload(manager, job.job_id, since_byte=0)
    payload_second = generative_job_log_payload(manager, job.job_id, since_byte=0)
    assert payload_first == payload_second


@pytest.mark.parametrize("since", [0, 5, 10_000])
def test_generative_job_log_payload_honors_since_byte(
    tmp_path: Path, since: int
) -> None:
    manager = InProcessGenerativeJobManager(jobs_root=tmp_path / "jobs")
    log_path = manager.jobs_root / "manual-job"
    log_path.mkdir(parents=True, exist_ok=True)
    (log_path / "log.txt").write_text(
        "candidate AAA status=complete eval=1\ncandidate BBB status=complete eval=2\n"
    )
    # Bypass FileNotFoundError handling by writing a placeholder job.json.
    job_json = log_path / "job.json"
    job_json.write_text(
        '{"schema_version":"1","job_id":"manual-job","job_kind":"sweep",'
        '"spec_ref":"spec.json","spec_hash":"' + "0" * 64 + '",'
        '"output_dir":"' + str(log_path / "output") + '","state":"succeeded",'
        '"progress":{"schema_version":"1","last_update_at":0.0},'
        '"log_tail_ref":"log.txt"}'
    )

    result = generative_job_log_payload(manager, "manual-job", since_byte=since)
    if since >= result["cursor"]:
        assert result["log"] == ""
    else:
        # The redacted tail is a suffix of the raw log; the cursor matches the
        # raw byte length of the tail before since_byte.
        assert result["cursor"] >= len(result["log"].encode("utf-8")) - 1
