"""The web handler labels the real sample without changing an explicit grid."""

from types import SimpleNamespace
import math

import pytest

from kayakgen.eval.contract import EvaluationContext
from kayakgen.eval.resistance import GRAVITY_M_S2, KNOTS_TO_MS
from kayakgen.model.hull import Hull
from kayakgen.services import evaluation
from kayakgen.ui.web.handlers import HandlersMixin
from kayakgen.ui.web.state import state_dict_from_hull


@pytest.mark.parametrize("target,notice", [(3.5, True), (4.5, False)])
def test_explicit_speed_sample_and_view_target_are_distinguished(target, notice, monkeypatch):
    hull = Hull()
    context = EvaluationContext.for_hull(
        hull, speeds_knots=(4.5,), n_stations=40, n_depths=8, n_theta=12
    )
    state = {
        **state_dict_from_hull(hull),
        "target_speed_kt": target,
        "evaluation_context": context.model_dump(mode="json"),
    }
    before = context.fingerprint()
    observed = []
    original = evaluation.evaluate_with_context

    def actual(*args, **kwargs):
        result = original(*args, **kwargs)
        observed.append((args[1].speeds_knots, tuple(result.resistance.V_knots)))
        return result

    monkeypatch.setattr(evaluation, "evaluate_with_context", actual)
    model = evaluation.metrics_from_state(state)
    assert model["evaluated_speed_kt"] == 4.5
    assert model["Fn"] * math.sqrt(GRAVITY_M_S2 * hull.length_m) / KNOTS_TO_MS == pytest.approx(4.5)
    assert bool(model["speed_selection_warning"]) == notice

    class Web(HandlersMixin):
        def _state_snapshot(self):
            return state

        def _refresh_status_segments(self):
            pass

        def _refresh_validity_badge(self):
            pass

    web = Web()
    web.state = SimpleNamespace(**state)
    web._refresh_metrics()
    assert any(line.startswith("At 4.5 kt") for line in web.state.metrics_lines)
    assert not any(line.startswith("At 3.5 kt") for line in web.state.metrics_lines)
    assert (
        any("not in the evaluation speed grid" in line for line in web.state.metrics_lines)
        == notice
    )
    assert observed == [((4.5,), (4.5,)), ((4.5,), (4.5,))]
    assert context.fingerprint() == before
    assert state["evaluation_context"]["speeds_knots"] == [4.5]


def test_legacy_metrics_evaluate_at_the_view_target():
    hull = Hull()
    model = evaluation.metrics_from_state({**state_dict_from_hull(hull), "target_speed_kt": 3.7})
    assert model["evaluated_speed_kt"] == 3.7
    assert model["speed_selection_warning"] is None
    assert model["Fn"] * math.sqrt(GRAVITY_M_S2 * hull.length_m) / KNOTS_TO_MS == pytest.approx(3.7)
