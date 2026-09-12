import json
from pathlib import Path

from graphify_postpass.merge import merge


def test_merge_replaces_previous_origin(tmp_path: Path):
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "ast_a", "_origin": "ast"},
                    {"id": "old_twig", "_origin": "twig_extractor"},
                ],
                "links": [
                    {"source": "ast_a", "target": "old_twig", "_origin": "twig_extractor"},
                ],
            }
        ),
        encoding="utf-8",
    )
    stats = merge(
        graph_path,
        [{"id": "new_twig", "label": "page.html.twig"}],
        [{"source": "ast_a", "target": "new_twig", "_origin": "twig_extractor"}],
        origin="twig_extractor",
        community_name="Twig templates",
    )
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    ids = {n["id"] for n in graph["nodes"]}
    assert ids == {"ast_a", "new_twig"}
    assert stats.removed_nodes == 1
    assert stats.added_nodes == 1
    assert stats.added_edges == 1


def test_merge_keeps_ast_on_id_collision(tmp_path: Path):
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [{"id": "same", "label": "PHP", "_origin": "ast"}],
                "links": [],
            }
        ),
        encoding="utf-8",
    )
    stats = merge(
        graph_path,
        [{"id": "same", "label": "page.html.twig"}],
        [],
        origin="twig_extractor",
        community_name="Twig templates",
    )
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    assert graph["nodes"][0]["label"] == "PHP"
    assert stats.collisions == ["same"]
