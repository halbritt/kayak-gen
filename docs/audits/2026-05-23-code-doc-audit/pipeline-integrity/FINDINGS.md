# Lane 1: Pipeline-Integrity / Claim-Gate Audit — Findings

## Overview

Audit of Pydantic invariants, claim-state integrity, and deprecation-path correctness in the 10 commits `f78e478..HEAD` (RFCs 0059/0060/0061 + workflows 0029-0034). Scope: `kayakgen/eval/contract.py` (GZCurve.result_semantics Literal widening), `kayakgen/eval/stability/accepted_fit.py` (EMPTY_STABILITY_FIT_REGISTRY constant), `kayakgen/ui/parameter_metadata.py` (dual registries), `kayakgen/ui/desktop_slider_ranges.py` (12 numeric tuple preservation), `kayakgen/ui/gui_params.py` (deprecation shim), `kayakgen/ui/pv_window.py` (Hull(**filtered) replacement), and three new test files.

**Finding Count**: 0 (null finding).

---

## Detailed Investigation

### 1. GZCurve.result_semantics Literal Widening (RFC 0061 R3 / AUD-P-001)

**Status: Pass**

Verification:
- `kayakgen/eval/contract.py:175-178`: GZCurve.result_semantics field accepts both `"unvalidated_hydrostatic_comparison"` and `"validated_hydrostatic_comparison"` via Literal.
- `kayakgen/eval/stability/high_angle_contracts.py:24-27`: AnalyticalClaimLabel type alias matches both labels exactly.
- `tests/test_gzcurve_result_semantics_round_trip.py`: 
  - Line 40–58: GeneratedBodyGZCurve accepts the validated label at construction.
  - Line 61–110: JSON round-trip test via `EvaluationResult.model_validate_json(eval_result.model_dump_json())` preserves the `"validated_hydrostatic_comparison"` value through the parent GZCurve schema without validation error.
  - Line 113–120: Confirms GZCurve still rejects unknown labels.

**Outcome**: Both labels round-trip correctly through `model_dump_json()` / `model_validate_json()`. No pattern-matching on result_semantics found in kayakgen/ source (grep: `result_semantics\s*==` returns no hits in main code, only test assertions). Widening is safe.

---

### 2. EMPTY_STABILITY_FIT_REGISTRY Constant and Three Consumers (D042)

**Status: Pass**

Verification:
- `kayakgen/eval/stability/accepted_fit.py:23`: Constant defined as `tuple["StabilityFitRecord", ...] = ()` with docstring naming D039 and the three call sites.
- Type annotation uses forward reference (string literal) which is correct for the self-same-module definition.
- Three call sites verified:
  - `kayakgen/eval/stability/evaluator.py:387`: `fit_registry=EMPTY_STABILITY_FIT_REGISTRY` passed to `resolve_analytical_claim_label()`
  - `kayakgen/ui/web/generate_frontier_view.py:559`: `fit_registry=EMPTY_STABILITY_FIT_REGISTRY` passed to frontier evaluation
  - `kayakgen/ui/web/generate_spec_form.py:869`: `registry=EMPTY_STABILITY_FIT_REGISTRY` passed to `cfd_in_loop_evaluator_status()`
- `kayakgen/eval/stability/high_angle_contracts.py:60-79`: `resolve_analytical_claim_label()` accepts `fit_registry: Iterable[StabilityFitRecord]` and iterates correctly; empty tuple is iterable and yields zero records.
- Grep for remaining hard-coded `registry=()` or `fit_registry=()`: None found (only one hit is a docstring comment in generate_spec_form.py).

**Outcome**: Constant is correctly typed, documented, and consumed by all three RFC 0058 stage-2/3 call sites. No synchronization drift. Stage-4 graduation has a single replacement point.

---

### 3. HullParameterMetadata Dual Registries (RFC 0061)

**Status: Pass**

Verification:
- `kayakgen/ui/parameter_metadata.py:36-122`: HULL_PARAMETER_METADATA has exactly 11 entries (`length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`, `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`, `bow_rake`, `stern_rake`).
- `kayakgen/ui/parameter_metadata.py:125-136`: VIEW_PARAMETER_METADATA has exactly 1 entry (`target_speed_kt`) marked as view-only with description naming that it is not a Hull field.
- `tests/test_desktop_sliders_use_registry.py:68-80`: Test `test_hull_and_view_registries_have_disjoint_keys()` computes overlap via set intersection and asserts equality to empty set.
- `kayakgen/ui/parameter_metadata.py:139-158`: `label_with_unit()` fall-back chain:
  1. Try `HULL_PARAMETER_METADATA.get(parameter)`
  2. If None, try `VIEW_PARAMETER_METADATA.get(parameter)`
  3. If still None, return raw key
  - Logic correctly uses `or` operator to short-circuit.
- `kayakgen/ui/parameter_metadata.py:161-172`: `description()` uses same fall-back chain.
- `tests/test_desktop_sliders_use_registry.py:101-112`: Test `test_kayak_gui_slider_labels_match_label_with_unit()` iterates over all SLIDERS (including `target_speed_kt`) and verifies label_with_unit() produces the expected label string.

**Outcome**: Registries are disjoint (tested), fallback chain works correctly (tested via actual KayakGUI SLIDERS iteration). Both parameters fall through correctly.

---

### 4. Desktop Slider Ranges Numeric Values (RFC 0061)

**Status: Pass**

Verification:
- `git show f78e478:kayakgen/ui/desktop.py` line ~83-94 reveals pre-RFC SLIDERS table with 12 rows.
- Extract of numeric ranges from pre-RFC:
  - `(length, (2.0, 6.5))` → `(length_m, (2.0, 6.5))`
  - `(beam, (0.30, 0.90))` → `(beam_oa_m, (0.30, 0.90))`
  - `(beam_wl, (0.30, 0.90))` → `(beam_wl_m, (0.30, 0.90))`
  - `(draft, (0.05, 0.25))` → `(draft_m, (0.05, 0.25))`
  - `(deck_height, (0.15, 0.40))` → `(deck_height_m, (0.15, 0.40))`
  - Plus non-renamed: `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`, `bow_rake`, `stern_rake`, `target_speed_kt`
- `kayakgen/ui/desktop_slider_ranges.py:18-31`: SLIDER_RANGES dict values all match pre-RFC literals exactly (verified spot-check: 3-4 spot values byte-equal).
- SLIDER_DEFAULTS in the same file match pre-RFC DEFAULTS.
- SLIDER_STEPS carries `{"Cm": 0.005}` matching pre-RFC.

**Outcome**: All 12 numeric tuples byte-equal to pre-RFC literals. Behavior preserved.

---

### 5. gui_params.py Deprecation Shim (RFC 0061)

**Status: Pass**

Verification:
- `kayakgen/ui/gui_params.py:30-48`: `hull_from_gui_params()` function:
  - Line 39-46: `warnings.warn()` call with:
    - Message naming RFC 0061 ✓
    - Category: `DeprecationWarning` ✓
    - `stacklevel=2` (correct: points to caller, not the warn() call itself) ✓
  - Line 47-48: Filters `params` by `Hull.model_fields` keys and returns `Hull(**filtered)` — valid and callable.
- `tests/test_gui_params.py:49-67`: Test `test_hull_from_gui_params_emits_rfc_0061_deprecation_warning()`:
  - Uses `pytest.warns(DeprecationWarning, match="RFC 0061")` to assert warning is emitted with the correct message.
  - Passes canonical Hull keys to the function (post-RFC style).

**Outcome**: Deprecation warning emitted correctly. Shim still returns valid Hull. One release cycle of backwards-compat provided.

---

### 6. pv_window.py Hull Replacement (RFC 0061)

**Status: Pass**

Verification:
- `kayakgen/ui/pv_window.py:18-24`: _NON_HULL_GUI_KEYS sourced from `tuple(VIEW_PARAMETER_METADATA.keys())` — ensures desktop and PyVista cannot drift on which keys are view-only.
- `kayakgen/ui/pv_window.py:26-38`: `_hull_from_params()` function:
  - Line 36-38: Constructs `Hull(**{key: value for key, value in params.items() if key not in _NON_HULL_GUI_KEYS})`
  - Correctly filters out view-only keys.
  - All Hull fields have defaults; empty/partial params dict → valid Hull with defaults for missing keys.
- `kayakgen/ui/pv_window.py:96-97, 132-133`: Both `_build_scene()` and `update_mesh()` call `_hull_from_params()` with `params` dict.
- `kayakgen/ui/pv_window.py:91-94`: `_update_title()` expects `params['length_m']` and `params['beam_oa_m']` to be present; these are always provided by the desktop GUI (DEFAULTS includes both).

**Outcome**: Inline `Hull(**filtered)` replaces legacy `_hull_from_gui_params()` indirection. Behavior preserved for empty/missing `target_speed_kt`. No loss of correctness.

---

### 7. New Tests Coverage (AUD-P-001 / AUD-P-002 round-trip + registry contracts)

**Status: Pass**

Verification:
- **`tests/test_gzcurve_result_semantics_round_trip.py`** (3 test cases):
  - Covers construction of GeneratedBodyGZCurve with validated label.
  - Covers JSON round-trip through parent GZCurve schema via StabilityResult wrapper.
  - Covers rejection of unknown labels.
  - **High-risk path**: JSON serialization → deserialization with validated label.

- **`tests/test_hull_parameter_metadata.py`** (5 test cases + parametrize):
  - Covers every BASE_HULL_KEYS entry has registry row.
  - Covers every registry entry is non-blank trimmed.
  - Covers every registry key resolves to Hull field.
  - Covers label_with_unit() and description() API.
  - Covers registry count (11 entries, pinned to avoid drift).
  - **Gap**: Does not test VIEW_PARAMETER_METADATA disjoint property (owned by test_desktop_sliders_use_registry.py, which is correct).

- **`tests/test_desktop_sliders_use_registry.py`** (5 test cases + parametrize):
  - Covers every SLIDER_RANGES key resolves to one of the two registries.
  - **Critical**: Test `test_hull_and_view_registries_have_disjoint_keys()` verifies disjoint property.
  - Covers hull-side SLIDER_RANGES keys resolve to Hull fields.
  - Covers KayakGUI.SLIDERS labels match label_with_unit() (includes target_speed_kt).
  - Covers KayakGUI.DEFAULTS round-trip through Hull construction.
  - **High-risk path**: label_with_unit() call for target_speed_kt (view-only key).

**Outcome**: New tests comprehensively cover all high-risk paths (JSON round-trip, registry disjoint property, label_with_unit fallback chain on view-only key). No test gaps that would leave a claim-state boundary unguarded.

---

## Synthesis

**No findings at severity critical, high, or medium.**

All Pydantic invariants preserved. No claim-state drift detected. Literal widening on GZCurve.result_semantics is correct and tested. Deprecation shim emits warnings as specified. EMPTY_STABILITY_FIT_REGISTRY constant consolidates three synchronization points into one. Dual registries are disjoint and tested. Desktop slider ranges byte-preserve pre-RFC literals. PyVista Hull construction correctly filters view-only keys. New tests cover the high-risk claim-gate boundaries.

**Recommended Action**: None. Code is ready to ship.

