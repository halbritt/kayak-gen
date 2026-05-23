"""Render-verification tests for the web Generate panel label surfaces.

Closes audit finding ``AUD-O-009`` from
``docs/audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md``
(workflow 0035). RFC 0060 wires the ``HullParameterMetadata`` registry
into the Generate panel form via the Vuetify ``:hint`` prop, but no
existing test verifies that the hint actually attaches to the rendered
``VTextField`` widgets on the base-hull rail. The round-trip / payload
tests in :mod:`tests.test_generate_spec_form` and the layout / source
checks in :mod:`tests.test_web_layout` pass even if a future refactor
silently drops the ``hint=`` wiring; this module's purpose is to catch
that drift.

The strategy follows the audit's R4 recommendation: monkeypatch the
``trame.widgets.vuetify3.VTextField.__init__`` (and ``VSelect.__init__``)
constructor around a :func:`kayakgen.ui.web.app.create_app` call to
capture every widget's keyword arguments, then assert the captured
``hint`` / ``label`` / ``items`` keys carry the expected registry-
sourced values keyed by the ``data-testid`` attribute. This is the
cheapest render verification given Trame's client-side rendering — the
captured constructor kwargs are exactly what get serialised into the
client template.

A complementary state-level assertion pins the seeded picklist items
(objectives + variable selector) for completeness; those are the
upstream truth value the Vue template iterates when rendering ``items``
in the picklist widgets.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("trame", reason="kayakgen[web] not installed")
pytest.importorskip("vtk", reason="kayakgen[web] not installed")

from trame.widgets import vuetify3 as v3  # noqa: E402

from kayakgen.model.hull import Hull  # noqa: E402
from kayakgen.search.objectives import OBJECTIVE_METADATA  # noqa: E402
from kayakgen.ui.parameter_metadata import (  # noqa: E402
    description,
    label_with_unit,
)
from kayakgen.ui.web.app import create_app  # noqa: E402
from kayakgen.ui.web.generate_spec_form import BASE_HULL_KEYS  # noqa: E402


def _capture_widget_calls() -> tuple[Any, list[dict[str, Any]], list[dict[str, Any]]]:
    """Build a web app while capturing VTextField + VSelect constructor kwargs.

    Returns ``(web, text_field_kwargs, select_kwargs)`` where the two
    kwarg lists contain one dict per widget construction call captured
    during ``create_app``. The captured dicts are shallow copies of the
    real kwargs so test assertions are isolated from any later mutation.
    """

    text_field_kwargs: list[dict[str, Any]] = []
    select_kwargs: list[dict[str, Any]] = []

    original_text_field_init = v3.VTextField.__init__
    original_select_init = v3.VSelect.__init__

    def text_field_spy(self: Any, *args: Any, **kwargs: Any) -> None:
        text_field_kwargs.append(dict(kwargs))
        return original_text_field_init(self, *args, **kwargs)

    def select_spy(self: Any, *args: Any, **kwargs: Any) -> None:
        select_kwargs.append(dict(kwargs))
        return original_select_init(self, *args, **kwargs)

    v3.VTextField.__init__ = text_field_spy  # type: ignore[method-assign]
    v3.VSelect.__init__ = select_spy  # type: ignore[method-assign]
    try:
        web = create_app(initial_hull=Hull())
    finally:
        v3.VTextField.__init__ = original_text_field_init  # type: ignore[method-assign]
        v3.VSelect.__init__ = original_select_init  # type: ignore[method-assign]
    return web, text_field_kwargs, select_kwargs


# ---------------------------------------------------------------------------
# (a) base-hull rail :hint render check (AUD-O-009)
# ---------------------------------------------------------------------------


def test_base_hull_rail_vtextfield_hint_equals_registry_description() -> None:
    """Each base-hull VTextField must render the registry description as hint.

    This is the load-bearing assertion for AUD-O-009. If a future
    refactor drops the ``hint=description(_hull_key) or ""`` keyword in
    ``render_spec_form_section``, this test fails because the captured
    constructor kwargs no longer carry the expected ``hint`` value.

    Each base-hull row is identified by its
    ``data-testid="generative-base-hull-{key}"`` attribute, which is set
    inline alongside ``hint`` / ``label`` in the form-builder.
    """

    _web, text_field_kwargs, _select_kwargs = _capture_widget_calls()

    captured_by_testid: dict[str, dict[str, Any]] = {}
    for kwargs in text_field_kwargs:
        testid = kwargs.get("data-testid")
        if isinstance(testid, str) and testid.startswith("generative-base-hull-"):
            captured_by_testid[testid] = kwargs

    for hull_key in BASE_HULL_KEYS:
        testid = f"generative-base-hull-{hull_key}"
        assert testid in captured_by_testid, (
            f"base-hull VTextField for {hull_key!r} (testid={testid!r}) was "
            f"never constructed during create_app(); captured testids: "
            f"{sorted(captured_by_testid)}"
        )
        captured = captured_by_testid[testid]

        # The load-bearing AUD-O-009 assertion: the rendered widget's
        # `hint` constructor kwarg equals the registry description for
        # the key. `description(key) or ""` is the form-builder's exact
        # call site, so an empty-string fallback would only kick in for
        # unregistered keys — every BASE_HULL_KEYS entry is registered.
        expected_hint = description(hull_key) or ""
        assert captured.get("hint") == expected_hint, (
            f"base-hull VTextField for {hull_key!r} should carry "
            f"hint={expected_hint!r}, got hint={captured.get('hint')!r}. "
            "AUD-O-009 regression: the :hint wiring on the base-hull rail "
            "no longer surfaces the registry description."
        )

        # Defense-in-depth: the label kwarg must also be the registry-
        # sourced friendly label. A regression here is the AUD-O-009
        # twin failure mode (display the raw JSON key as the label).
        assert captured.get("label") == label_with_unit(hull_key), (
            f"base-hull VTextField for {hull_key!r} should carry "
            f"label={label_with_unit(hull_key)!r}, got "
            f"label={captured.get('label')!r}."
        )


# ---------------------------------------------------------------------------
# (b) objectives picklist items render check
# ---------------------------------------------------------------------------


def test_objectives_picklist_items_use_registry_label_and_unit() -> None:
    """Each objective picklist item title must equal ``label (unit)``.

    The picklist items are seeded into Trame state by
    :func:`kayakgen.ui.web.generate_spec_form.initialize_form_state`;
    the Vue template iterates ``generative_objective_picklist_items`` to
    render the dropdown. The bare metric name stays as the picklist
    ``value`` so the submitted JSON payload is byte-stable; only the
    rendered ``title`` changes.
    """

    web, _text_field_kwargs, _select_kwargs = _capture_widget_calls()

    picklist_items = web.state.generative_objective_picklist_items
    assert isinstance(picklist_items, list), (
        "generative_objective_picklist_items should be a list seeded by "
        "initialize_form_state"
    )
    assert picklist_items, (
        "generative_objective_picklist_items is empty; the admissibility "
        "filter dropped every metric, which would mean the form's picklist "
        "is unusable"
    )

    for item in picklist_items:
        assert isinstance(item, dict), (
            f"picklist item {item!r} should be a dict with value+title keys"
        )
        metric = item.get("value")
        title = item.get("title")
        assert isinstance(metric, str) and metric, (
            f"picklist item {item!r} missing a non-empty 'value' string"
        )
        assert metric in OBJECTIVE_METADATA, (
            f"picklist item value {metric!r} is not in OBJECTIVE_METADATA; "
            f"the admissibility filter let through an unknown metric"
        )
        meta = OBJECTIVE_METADATA[metric]
        expected_title = f"{meta.label} ({meta.unit})"
        assert title == expected_title, (
            f"objective picklist item for {metric!r} should carry "
            f"title={expected_title!r}, got title={title!r}. The picklist's "
            "registry-sourced friendly title wiring (RFC 0060 §4(d)) has "
            "drifted from OBJECTIVE_METADATA."
        )


# ---------------------------------------------------------------------------
# (c) variable-selector picklist items render check
# ---------------------------------------------------------------------------


def test_variable_picklist_items_use_label_with_unit() -> None:
    """Variable-selector picklist items must title with ``label_with_unit(key)``.

    RFC 0060 §4(b): operators pick a variable for sweep / search by
    friendly label (e.g. ``"Beam WL (m)"``) but the submitted JSON
    payload uses the raw key (e.g. ``"beam_wl_m"``). The picklist items
    list is seeded into ``state.generative_variable_picklist_items`` by
    :func:`initialize_form_state` and consumed by the Vue template's
    ``<select v-for>`` block on the variable rows.
    """

    web, _text_field_kwargs, _select_kwargs = _capture_widget_calls()

    picklist_items = web.state.generative_variable_picklist_items
    assert isinstance(picklist_items, list), (
        "generative_variable_picklist_items should be a list seeded by "
        "initialize_form_state"
    )

    # Pin the picklist to BASE_HULL_KEYS — the form-builder iterates that
    # tuple to seed the items, so the ordering must match.
    captured_values = [item.get("value") for item in picklist_items]
    assert captured_values == list(BASE_HULL_KEYS), (
        f"variable picklist items should carry values matching "
        f"BASE_HULL_KEYS={list(BASE_HULL_KEYS)!r} in order, got "
        f"{captured_values!r}"
    )

    for item in picklist_items:
        assert isinstance(item, dict)
        key = item["value"]
        expected_title = label_with_unit(key)
        assert item.get("title") == expected_title, (
            f"variable picklist item for {key!r} should carry "
            f"title={expected_title!r}, got title={item.get('title')!r}. "
            "The label_with_unit() wiring on the variable selector has "
            "drifted from the HullParameterMetadata registry."
        )
