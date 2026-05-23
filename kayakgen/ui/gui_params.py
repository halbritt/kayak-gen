"""Deprecated GUI → Hull parameter translation shim.

RFC 0061 retired the desktop GUI's short-key parameter form
(``length``, ``beam``, ``beam_wl``, ``draft``, ...) in favor of the
canonical Hull JSON field names (``length_m``, ``beam_oa_m``,
``beam_wl_m``, ``draft_m``, ...). The desktop GUI's ``params`` dict
is now Hull-shaped and goes straight into ``Hull(**...)`` after a
small ``_NON_HULL_GUI_KEYS`` filter.

This module is kept as a deprecation shim for one release cycle so
external callers that import :func:`hull_from_gui_params` keep working
while they migrate. The :data:`GUI_TO_HULL` mapping is now empty; the
helper emits a :class:`DeprecationWarning` naming RFC 0061 and falls
back to filtering ``params`` against :attr:`Hull.model_fields`.
"""

from __future__ import annotations

import warnings
from typing import Any

from kayakgen.model.hull import Hull

# Emptied by RFC 0061; no remaining consumer should rely on this dict.
# Kept as an empty mapping to avoid hard-import breakage for any
# straggler caller that imports the symbol but does not iterate it.
GUI_TO_HULL: dict[str, str] = {}


def hull_from_gui_params(params: dict[str, Any]) -> Hull:
    """Build a :class:`Hull` from a desktop/PyVista GUI ``params`` dict.

    Deprecated by RFC 0061: the desktop GUI now uses canonical Hull
    field names directly. New code should pass ``params`` straight to
    ``Hull(**params)`` after filtering view-only keys (see
    :data:`kayakgen.ui.parameter_metadata.VIEW_PARAMETER_METADATA`).
    """

    warnings.warn(
        "kayakgen.ui.gui_params.hull_from_gui_params is deprecated by RFC "
        "0061; the desktop GUI now uses canonical Hull field names "
        "directly. Pass `params` straight to `Hull(**params)` after "
        "filtering view-only keys. See "
        "`docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`.",
        DeprecationWarning,
        stacklevel=2,
    )
    hull_keys = set(Hull.model_fields.keys())
    return Hull(**{key: value for key, value in params.items() if key in hull_keys})
