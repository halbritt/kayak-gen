"""kayakgen.ui.web — Trame-based portable web frontend (RFC 0008).

Lazy: import :func:`create_app` from :mod:`kayakgen.ui.web.app` only when
the web extras (``pip install kayakgen[web]``) are actually installed,
to keep ``import kayakgen`` cheap for headless use.
"""

from kayakgen.ui.web.state import (
    decode_hull_query,
    encode_hull_query,
    state_dict_from_hull,
    hull_from_state_dict,
)

__all__ = [
    "decode_hull_query",
    "encode_hull_query",
    "hull_from_state_dict",
    "state_dict_from_hull",
]
