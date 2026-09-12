"""CLI: run every extractor that finds files, then merge into graph.json."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from graphify_postpass.extractors.twig import ORIGIN as TWIG_ORIGIN
from graphify_postpass.extractors.twig.build import build
from graphify_postpass.extractors.twig.extract import extract
from graphify_postpass.extractors.twig.index import TwigIndex
from graphify_postpass.merge import merge


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="graphify-postpass",
        description="Write house extractors onto a Graphify graph.json.",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    parser.add_argument(
        "--graph",
        type=Path,
        default=None,
        help="path to graph.json (default: ROOT/graphify-out/graph.json)",
    )
    parser.add_argument("--dry-run", action="store_true", help="count only; do not write")
    parser.add_argument("--quiet", action="store_true", help="errors only")
    parser.add_argument(
        "--show-unresolved",
        type=int,
        default=10,
        help="how many unresolved refs to print (0 = none)",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    graph_path = args.graph or root / "graphify-out" / "graph.json"
    if not graph_path.is_file():
        print(
            f"error: missing {graph_path} — build the graph first (`graphify .`)",
            file=sys.stderr,
        )
        return 1

    started = time.perf_counter()
    index = TwigIndex.from_git(root)
    if not index.templates:
        if not args.quiet:
            print("graphify-postpass: no .twig files in git ls-files — nothing to do")
        return 0

    facts_by_path = {}
    for rel_path in index.templates:
        try:
            source = (root / rel_path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"  skip {rel_path}: {exc}", file=sys.stderr)
            continue
        facts_by_path[rel_path] = extract(rel_path, source)

    nodes, edges, stats = build(facts_by_path, index)
    elapsed = time.perf_counter() - started

    if not args.quiet:
        _report(stats, elapsed, args.show_unresolved)

    if args.dry_run:
        if not args.quiet:
            print("\n--dry-run: graph unchanged")
        return 0

    merge_stats = merge(
        graph_path,
        nodes,
        edges,
        origin=TWIG_ORIGIN,
        community_name="Twig templates",
    )
    if not args.quiet:
        print(
            f"\ngraph: -{merge_stats.removed_nodes} nodes / "
            f"-{merge_stats.removed_edges} edges (previous pass), "
            f"+{merge_stats.added_nodes} nodes / +{merge_stats.added_edges} edges"
        )
        if merge_stats.dangling_edges:
            print(f"  skipped {merge_stats.dangling_edges} edges with a missing endpoint")
        if merge_stats.collisions:
            print(
                f"  id collisions with AST nodes: {len(merge_stats.collisions)} "
                f"(e.g. {', '.join(merge_stats.collisions[:3])})"
            )
    return 0


def _report(stats, elapsed: float, show_unresolved: int) -> None:
    print(f"templates:     {stats.templates}")
    print(f"nodes:         {stats.nodes}  (templates + blocks)")
    print(f"edges:         {stats.edges}")
    print(
        f"  resolved:    {stats.resolved} "
        f"({stats.ambiguous} via path heuristic)"
    )
    print(f"  blocks:      {stats.blocks}")
    print(
        f"skipped:       {stats.dynamic} dynamic, {stats.self_refs} _self, "
        f"{len(stats.unresolved)} unresolved"
    )
    print(f"time:          {elapsed:.2f} s")
    if show_unresolved and stats.unresolved:
        print(f"\nunresolved refs (first {show_unresolved}):")
        for rel_path, raw, line in stats.unresolved[:show_unresolved]:
            print(f"  {rel_path}:{line}  ->  {raw[:70]}")
