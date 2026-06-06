"""Cross-surface presentation registries with no UI / CLI dependencies.

Workflow 0062 (P0-BOUNDARY-FIX): registries that both ``kayakgen.services``
and ``kayakgen.ui`` consume live here, below the services layer, so the
``services -> ui`` dependency direction enforced by
``tests/test_services_boundaries.py`` holds. Modules in this package are
pure data (pydantic records + dict registries); they must not import from
``kayakgen.services``, ``kayakgen.ui``, or ``kayakgen.cli``.
"""
