"""Generative-jobs panel methods for the kayakgen web UI.

Extracted verbatim from ``kayakgen.ui.web.app`` (refactoring campaign
kayakgen-smoke-1, slice S3). ``KayakgenApp`` composes ``GeneratePanelMixin``;
``app.py`` re-exports ``_default_generative_jobs_root_for_app`` and
``kayakgen/cli/main.py`` imports it from here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kayakgen.ui.web.controllers import (
    cancel_generative_job_payload,
    fork_generative_job_payload,
    generative_job_frontier_payload,
    generative_job_list_payload,
    generative_job_log_payload,
    resume_generative_job_payload,
    start_generative_job_payload,
)
from kayakgen.ui.web.generate_fork_button import next_default_seed
from kayakgen.ui.web.generate_frontier_view import (
    apply_candidate_to_hull,
    refresh_frontier_view,
    undo_candidate_handoff,
)
from kayakgen.ui.web.generate_spec_form import (
    GenerateSpecFormError,
    build_spec_from_form_state,
    refresh_concurrency_advisory,
)
from kayakgen.ui.web.presentation import (
    GENERATIVE_JOBS_EMPTY_COPY,
    _generative_job_state_flags,
)
from kayakgen.ui.web.state import (
    decode_hull_query,
    state_dict_from_hull,
)


def _default_generative_jobs_root_for_app() -> str:
    """Default jobs root for the Trame app's in-process job manager.

    Honors ``KAYAKGEN_GENERATIVE_JOBS_ROOT`` for tests/operators; otherwise
    falls back to ``~/.local/share/kayakgen/generative_jobs/``.
    """

    import os
    from pathlib import Path as _Path

    override = os.environ.get("KAYAKGEN_GENERATIVE_JOBS_ROOT")
    if override:
        return str(_Path(override).expanduser())
    return str(_Path.home() / ".local" / "share" / "kayakgen" / "generative_jobs")


class GeneratePanelMixin:
    """Generative-jobs panel methods of :class:`~kayakgen.ui.web.app.KayakgenApp`."""

    def _generative_spec_payload_for_submit(self, kind: str) -> dict[str, Any] | None:
        text = str(self.state.generative_spec_json or "").strip()
        if text:
            try:
                spec_payload = json.loads(text)
            except ValueError as exc:
                self.state.generative_status = f"Spec is not valid JSON: {exc}"
                return None
            if not isinstance(spec_payload, dict):
                self.state.generative_status = "Spec JSON must be an object."
                return None
            return spec_payload
        self.state.generative_job_kind = kind
        try:
            spec_payload = build_spec_from_form_state(self.state)
        except GenerateSpecFormError as exc:
            self.state.generative_status = f"Form is incomplete: {exc}"
            return None
        except Exception as exc:  # noqa: BLE001 - keep the panel non-throwing
            self.state.generative_status = f"Form is incomplete: {exc}"
            return None
        self.state.generative_spec_json = json.dumps(
            spec_payload, indent=2, sort_keys=True
        )
        return spec_payload

    def _apply_generative_form_to_json(self) -> None:
        try:
            spec_payload = build_spec_from_form_state(self.state)
        except GenerateSpecFormError as exc:
            self.state.generative_status = f"Form is incomplete: {exc}"
            return
        except Exception as exc:  # noqa: BLE001
            self.state.generative_status = f"Form is incomplete: {exc}"
            return
        self.state.generative_spec_json = json.dumps(
            spec_payload, indent=2, sort_keys=True
        )
        self.state.generative_status = "Form spec copied to the raw JSON editor."

    def _submit_generative_job(self, kind: str) -> None:
        spec_payload = self._generative_spec_payload_for_submit(kind)
        if spec_payload is None:
            return
        try:
            payload = start_generative_job_payload(
                {"spec": spec_payload},
                self._generative_manager,
                job_kind=kind,  # type: ignore[arg-type]
            )
        except Exception as exc:  # noqa: BLE001 - surface a clean message
            self.state.generative_status = f"Submit failed: {exc}"
            return
        job_id = payload["job_id"]
        self.state.generative_job_id = job_id
        self.state.generative_status = (
            f"Submitted {kind} job {job_id}; state={payload['state']}."
        )
        self._refresh_generative_jobs()

    def _refresh_generative_jobs(self) -> None:
        listing = generative_job_list_payload(self._generative_manager)
        rows: list[str] = []
        table_rows: list[dict[str, Any]] = []
        for job in listing.get("jobs", []):
            error_kind = ""
            try:
                full_job = self._generative_manager.get(str(job["job_id"]))
                if full_job.error is not None:
                    error_kind = full_job.error.kind
            except Exception:  # noqa: BLE001 - summary rows remain useful
                error_kind = ""
            rows.append(
                f"{job['job_id']}\t{job['job_kind']}\t{job['state']}\t"
                f"{job['realized_evaluations']}/{job['completed_count']}c/"
                f"{job['failed_count']}f"
            )
            table_rows.append(
                {
                    "job_id": job["job_id"],
                    "job_kind": job["job_kind"],
                    "state": job["state"],
                    "error_kind": error_kind,
                    "resumable": bool(job["state"] in {"resumable", "failed", "cancelled"}),
                }
            )
        if not rows:
            rows = [GENERATIVE_JOBS_EMPTY_COPY]
        self.state.generative_jobs_lines = rows
        self.state.generative_jobs_table_rows = table_rows
        flags = _generative_job_state_flags(table_rows)
        self.state.generative_jobs_empty = flags["empty"]
        self.state.generative_jobs_running = flags["running"]
        self.state.generative_jobs_failed = flags["failed"]
        self.state.generative_jobs_cancelled = flags["cancelled"]
        self.state.generative_jobs_resumable = flags["resumable"]
        self.state.generative_jobs_failed_kind = next(
            (
                str(row.get("error_kind") or "")
                for row in table_rows
                if row.get("state") == "failed" and row.get("error_kind")
            ),
            "",
        )
        refresh_concurrency_advisory(self)

    def _cancel_generative_job(self) -> None:
        job_id = str(self.state.generative_job_id or "").strip()
        if not job_id:
            self.state.generative_status = "Enter a job id to cancel."
            return
        try:
            payload = cancel_generative_job_payload(
                self._generative_manager, job_id
            )
        except Exception as exc:  # noqa: BLE001
            self.state.generative_status = f"Cancel failed: {exc}"
            return
        self.state.generative_status = (
            f"Cancel requested for {payload['job_id']}; state={payload['state']}."
        )
        self._refresh_generative_jobs()

    def _resume_generative_job(self) -> None:
        job_id = str(self.state.generative_job_id or "").strip()
        if not job_id:
            self.state.generative_status = "Enter a job id to resume."
            return
        try:
            payload = resume_generative_job_payload(
                self._generative_manager, job_id
            )
        except Exception as exc:  # noqa: BLE001
            self.state.generative_status = f"Resume failed: {exc}"
            return
        self.state.generative_status = (
            f"Resumed {payload['job_id']}; state={payload['state']}."
        )
        self._refresh_generative_jobs()

    def _load_generative_log(self) -> None:
        job_id = str(self.state.generative_job_id or "").strip()
        if not job_id:
            self.state.generative_log_lines = ["(enter a job id)"]
            return
        try:
            payload = generative_job_log_payload(
                self._generative_manager, job_id, since_byte=0
            )
        except Exception as exc:  # noqa: BLE001
            self.state.generative_log_lines = [f"log unavailable: {exc}"]
            return
        log_text = payload.get("log", "")
        if not log_text.strip():
            self.state.generative_log_lines = ["(no log lines yet)"]
            return
        self.state.generative_log_lines = log_text.splitlines()[-200:]

    def _load_generative_frontier(self) -> None:
        # Legacy text-list surface; kept for the existing `Load Frontier`
        # button. Stage 4 also drives the 2D-scatter view via
        # ``_refresh_generative_frontier_view``.
        job_id = str(self.state.generative_job_id or "").strip()
        if not job_id:
            self.state.generative_frontier_lines = ["(enter a job id)"]
            return
        try:
            payload = generative_job_frontier_payload(
                self._generative_manager, job_id
            )
        except Exception as exc:  # noqa: BLE001
            self.state.generative_frontier_lines = [f"frontier unavailable: {exc}"]
            return
        if not payload.get("frontier_available"):
            note = payload.get("note") or "frontier not available yet"
            self.state.generative_frontier_lines = [note]
            return
        rows: list[str] = []
        for row in payload.get("frontier", []):
            params = ", ".join(
                f"{k}={v}" for k, v in sorted((row.get("parameters") or {}).items())
            )
            rows.append(
                f"{row.get('candidate_key')}\t{row.get('status')}\t{params}"
            )
        self.state.generative_frontier_lines = rows or ["(empty frontier)"]
        # Mirror into the scatter+table view-model so the stage 4 widgets
        # update at the same time.
        self._refresh_generative_frontier_view()

    def _refresh_generative_frontier_view(self) -> None:
        job_id = str(self.state.generative_job_id or "").strip()
        if not job_id:
            return
        self.state.generative_frontier_loading = True
        try:
            refresh_frontier_view(self, job_id)
        except Exception:  # noqa: BLE001
            # Frontier view is read-only; refusal is non-fatal.
            return
        finally:
            self.state.generative_frontier_loading = False
        self.state.generative_frontier_rendered = bool(
            self.state.generative_frontier_view_available
        )

    def _fork_generative_job(
        self, job_id: str, new_seed: int | None
    ) -> None:
        job_id = str(job_id or "").strip()
        if not job_id:
            self.state.generative_status = "Enter a job id to fork."
            return
        if new_seed is None:
            try:
                current = self._generative_manager.get(job_id)
                spec_path = (
                    Path(current.output_dir).parent / "spec.json"
                    if current.output_dir
                    else None
                )
                source_seed = 0
                if spec_path is not None and spec_path.exists():
                    spec_data = json.loads(spec_path.read_text())
                    source_seed = int(
                        ((spec_data.get("algorithm") or {}).get("seed") or 0)
                    )
                new_seed = next_default_seed(source_seed)
            except Exception:  # noqa: BLE001
                new_seed = next_default_seed(0)
        try:
            payload = fork_generative_job_payload(
                self._generative_manager,
                job_id,
                new_seed=int(new_seed),
            )
        except Exception as exc:  # noqa: BLE001
            self.state.generative_status = f"Fork failed: {exc}"
            return
        forked_id = payload.get("job_id")
        self.state.generative_job_id = forked_id or job_id
        self.state.generative_status = (
            f"Forked {job_id} → {forked_id} with seed={new_seed}."
        )
        self._refresh_generative_jobs()

    def _load_generative_candidate(
        self, candidate_payload: Any
    ) -> None:
        try:
            apply_candidate_to_hull(self, candidate_payload)
        except Exception as exc:  # noqa: BLE001
            self.state.generative_status = f"Candidate load failed: {exc}"
            return
        candidate_key = ""
        if isinstance(candidate_payload, dict):
            candidate_key = str(candidate_payload.get("candidate_key", ""))
        self.state.generative_status = (
            f"Loaded {candidate_key} into the single-hull view."
            if candidate_key
            else "Loaded candidate into the single-hull view."
        )

    def _undo_generative_handoff(self) -> None:
        if undo_candidate_handoff(self):
            self.state.generative_status = "Undid the most recent candidate handoff."

    def load_from_query(self, query: str) -> None:
        try:
            hull = decode_hull_query(query)
        except Exception:
            return
        self.state.update(state_dict_from_hull(hull))
        self.state.class_preset = "custom"
        self._apply_slider_bounds("custom")
        self._refresh_current_hull_surface()
