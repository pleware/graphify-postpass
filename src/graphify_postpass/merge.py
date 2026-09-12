"""Idempotent merge of one extractor's nodes and edges into graph.json."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

UNCLUSTERED_COMMUNITY = -1


@dataclass
class MergeStats:
    removed_nodes: int = 0
    removed_edges: int = 0
    added_nodes: int = 0
    added_edges: int = 0
    collisions: list[str] = field(default_factory=list)
    dangling_edges: int = 0


def merge(
    graph_path: Path,
    nodes: list[dict],
    edges: list[dict],
    *,
    origin: str,
    community_name: str,
) -> MergeStats:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    stats = MergeStats()

    kept_nodes = [n for n in graph["nodes"] if n.get("_origin") != origin]
    kept_edges = [e for e in graph["links"] if e.get("_origin") != origin]
    stats.removed_nodes = len(graph["nodes"]) - len(kept_nodes)
    stats.removed_edges = len(graph["links"]) - len(kept_edges)

    existing_ids = {n["id"] for n in kept_nodes}

    for node in nodes:
        if node["id"] in existing_ids:
            # Graphify's _file_stem strips one suffix, so a.html.twig and
            # a.html.php collide. Keep the AST node.
            stats.collisions.append(node["id"])
            continue
        enriched = dict(node)
        enriched.setdefault("norm_label", (node.get("label") or "").casefold())
        enriched.setdefault("community", UNCLUSTERED_COMMUNITY)
        enriched.setdefault("community_name", community_name)
        kept_nodes.append(enriched)
        existing_ids.add(node["id"])
        stats.added_nodes += 1

    for edge in edges:
        if edge["source"] not in existing_ids or edge["target"] not in existing_ids:
            stats.dangling_edges += 1
            continue
        kept_edges.append(edge)
        stats.added_edges += 1

    graph["nodes"] = kept_nodes
    graph["links"] = kept_edges
    _write_atomic(graph_path, graph)
    return stats


def _write_atomic(path: Path, graph: dict) -> None:
    handle, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(graph, stream, ensure_ascii=False)
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
