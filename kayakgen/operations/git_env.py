"""Keep Git's repository-local environment out of gate and test processes.

Git exports variables such as ``GIT_DIR`` and ``GIT_INDEX_FILE`` to hooks.
A child ``git`` command that inherits them acts on the invoking repository
regardless of its working directory or ``-C`` argument. Tests that build
throwaway repositories then initialize, stage and commit into the real one.
"""

from __future__ import annotations

from collections.abc import MutableMapping
import os

# ``git rev-parse --local-env-vars`` (Git 2.4x), fixed here so the scrub
# does not itself depend on running Git inside the inherited environment.
GIT_LOCAL_ENV_VARS = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "GIT_OBJECT_DIRECTORY",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_GRAFT_FILE",
    "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_REPLACE_REF_BASE",
    "GIT_PREFIX",
    "GIT_SHALLOW_FILE",
    "GIT_COMMON_DIR",
)


def scrub_git_local_env(environ: MutableMapping[str, str] | None = None) -> list[str]:
    """Remove repository-local Git variables; return the names removed."""

    target = os.environ if environ is None else environ
    removed = [name for name in GIT_LOCAL_ENV_VARS if name in target]
    for name in removed:
        del target[name]
    indexed = [
        name
        for name in list(target)
        if name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))
    ]
    for name in indexed:
        del target[name]
    return removed + indexed
