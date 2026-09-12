"""Turn Twig facts into Graphify nodes and edges."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from graphify_postpass.extractors.twig import ORIGIN
from graphify_postpass.extractors.twig.extract import RELATION_BY_TAG, TemplateFacts
from graphify_postpass.extractors.twig.index import TwigIndex
from graphify_postpass.extractors.twig.resolve import Outcome, TwigResolver
from graphify_postpass.ids import template_node_id

MakeId = Callable[..., str]
FileStem = Callable[[PurePosixPath], str]


@dataclass
class BuildStats:
    templates: int = 0
    nodes: int = 0
    edges: int = 0
    resolved: int = 0
    ambiguous: int = 0
    unresolved: list[tuple[str, str, int]] = field(default_factory=list)
    dynamic: int = 0
    self_refs: int = 0
    blocks: int = 0


def build(
    facts_by_path: dict[str, TemplateFacts],
    index: TwigIndex,
    *,
    make_id: MakeId | None = None,
    file_stem: FileStem | None = None,
) -> tuple[list[dict], list[dict], BuildStats]:
    resolver = TwigResolver(index)
    stats = BuildStats(templates=len(facts_by_path))
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    seen_edges: set[tuple[str, str, str]] = set()

    def nid(rel_path: str) -> str:
        return template_node_id(rel_path, make_id=make_id, file_stem=file_stem)

    def add_node(node_id: str, label: str, rel_path: str, location: str | None) -> None:
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "label": label,
                "file_type": "code",
                "source_file": rel_path,
                "source_location": location,
                "_origin": ORIGIN,
            }

    def add_edge(
        source: str,
        target: str,
        relation: str,
        rel_path: str,
        line: int,
        confidence: str = "EXTRACTED",
        context: str | None = None,
    ) -> None:
        key = (source, target, relation)
        if key in seen_edges:
            return
        seen_edges.add(key)
        edge = {
            "source": source,
            "target": target,
            "relation": relation,
            "confidence": confidence,
            "confidence_score": _score(confidence),
            "source_file": rel_path,
            "source_location": f"L{line}" if line else None,
            "weight": 1.0,
            "_origin": ORIGIN,
        }
        if context:
            edge["context"] = context
        edges.append(edge)

    for rel_path in facts_by_path:
        add_node(nid(rel_path), PurePosixPath(rel_path).name, rel_path, None)

    for rel_path, facts in facts_by_path.items():
        file_nid = nid(rel_path)
        for ref in facts.refs:
            resolution = resolver.resolve(rel_path, ref.argument)
            if resolution.outcome == Outcome.SELF:
                stats.self_refs += 1
                continue
            if resolution.outcome == Outcome.DYNAMIC:
                stats.dynamic += 1
                continue
            if resolution.outcome == Outcome.UNRESOLVED:
                stats.unresolved.append((rel_path, resolution.raw, ref.line))
                continue
            stats.resolved += 1
            if resolution.ambiguous:
                stats.ambiguous += 1
            target = resolution.target
            assert target is not None
            target_nid = nid(target)
            add_node(target_nid, PurePosixPath(target).name, target, None)
            add_edge(
                file_nid,
                target_nid,
                RELATION_BY_TAG[ref.tag],
                rel_path,
                ref.line,
                confidence="EXTRACTED" if not resolution.ambiguous else "INFERRED",
                context=ref.tag,
            )
        for block in facts.blocks:
            if make_id is None:
                from graphify_postpass.ids import require_graphify_ids

                real_make_id, _ = require_graphify_ids()
            else:
                real_make_id = make_id
            block_nid = real_make_id(file_nid, "block", block.name)
            add_node(block_nid, f"block {block.name}", rel_path, f"L{block.line}")
            add_edge(file_nid, block_nid, "defines", rel_path, block.line, context="block")
            stats.blocks += 1

    stats.nodes = len(nodes)
    stats.edges = len(edges)
    return list(nodes.values()), edges, stats


def _score(confidence: str) -> float:
    return {"EXTRACTED": 1.0, "INFERRED": 0.7, "AMBIGUOUS": 0.4}.get(confidence, 0.5)
