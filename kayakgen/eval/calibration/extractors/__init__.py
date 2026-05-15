"""Resistance source extractors.

Each module in this package converts a primary, externally hosted measurement
source into a kayakgen-internal normalized row schema. Extractors do not
perform any network I/O at import or call time; they only operate on local
files that have already been acquired by the operator and bound by checksum.

Until a source's checksum and extraction script are both bound and accepted
by an RFC 0042 review packet, the extractor must raise ``NotImplementedError``
with an explicit ``pending data acquisition`` reason.
"""

from __future__ import annotations

__all__: list[str] = []
