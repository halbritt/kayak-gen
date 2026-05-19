"""Trame Fork-with-new-seed button module (RFC 0057 stage 4, D-12).

Provides a small, self-contained renderer that the Trame Generate-panel
integrator can drop next to a succeeded Pareto row. The button text
and callback wiring are stable; the integrator owns wiring
``app.ctrl.fork_generative_job`` to whatever submit/status helper its
panel uses.
"""

from __future__ import annotations

from typing import Any


FORK_BUTTON_LABEL = "Fork with new seed"
"""User-visible label for the fork-with-new-seed button."""


def next_default_seed(source_seed: int) -> int:
    """Suggested seed for a fork given the source job's seed.

    A deterministic increment is preferred over ``random.randint`` so
    tests can assert byte-stable behavior. Operators who want a
    different seed can still override the input field before clicking.
    """

    return int(source_seed) + 1


def render_fork_button(app: Any, *, job_summary: dict[str, Any]) -> Any:
    """Render a Vuetify ``VBtn`` wired to ``app.ctrl.fork_generative_job``.

    The integrator (``app.py``) is responsible for binding
    ``app.ctrl.fork_generative_job(job_id, new_seed)`` to its own
    submit helper; this module only emits the button widget.

    Args:
        app: The Trame application instance (exposes ``ctrl``).
        job_summary: A serialized :class:`GenerativeJobSummary` /
            :class:`GenerativeJob` payload. Must include ``job_id``.

    Returns:
        The constructed Vuetify ``VBtn`` widget object.
    """

    from trame.widgets import vuetify3 as v3

    job_id = job_summary.get("job_id")
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("job_summary must include a non-empty 'job_id'")

    # Seed default: prefer an explicit ``next_seed`` hint on the
    # summary, otherwise fall back to source seed + 1 via
    # ``next_default_seed``. Falls back to 0 when no seed is available.
    seed_hint = job_summary.get("next_seed")
    if not isinstance(seed_hint, int):
        source_seed = job_summary.get("source_seed", 0)
        seed_hint = next_default_seed(
            source_seed if isinstance(source_seed, int) else 0
        )

    return v3.VBtn(
        FORK_BUTTON_LABEL,
        click=(app.ctrl.fork_generative_job, f"['{job_id}', {seed_hint}]"),
        density="compact",
        classes="kg-fork-with-new-seed",
    )


__all__ = [
    "FORK_BUTTON_LABEL",
    "next_default_seed",
    "render_fork_button",
]
