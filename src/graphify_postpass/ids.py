"""Node ids must match Graphify's recipe. Import it; do not copy it."""

from __future__ import annotations

from pathlib import PurePosixPath


def require_graphify_ids() -> tuple[object, object]:
    """Return ``(make_id, file_stem)`` from the host Graphify install."""
    try:
        from graphify.extractors.base import _file_stem
        from graphify.ids import make_id
    except ImportError as exc:
        raise RuntimeError(
            "graphify-postpass must run in the graphifyy interpreter "
            "(graphify-out/.graphify_python). Graphify is not on this Python."
        ) from exc
    return make_id, _file_stem


def template_node_id(rel_path: str, make_id=None, file_stem=None) -> str:
    """Id of a file node. Graphify's ``_file_stem`` strips one suffix only."""
    if make_id is None or file_stem is None:
        make_id, file_stem = require_graphify_ids()
    return make_id(file_stem(PurePosixPath(rel_path)))
