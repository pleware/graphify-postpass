from pathlib import Path, PurePosixPath

from graphify_postpass.extractors.twig.build import build
from graphify_postpass.extractors.twig.extract import extract
from graphify_postpass.extractors.twig.index import TwigIndex


def _stem(path: PurePosixPath) -> str:
    text = path.as_posix()
    if text.endswith(".twig"):
        return text[: -len(".twig")]
    return text


def _make_id(*parts: object) -> str:
    return "_".join(str(p).replace("/", "_").replace(".", "_") for p in parts)


def test_extends_and_block():
    index = TwigIndex(Path("/repo"), ["page.html.twig", "base.html.twig"])
    facts = {
        "page.html.twig": extract(
            "page.html.twig",
            "{% extends 'base.html.twig' %}\n{% block body %}{% endblock %}\n",
        ),
        "base.html.twig": extract("base.html.twig", "{% block body %}{% endblock %}\n"),
    }
    nodes, edges, stats = build(facts, index, make_id=_make_id, file_stem=_stem)
    relations = {(e["source"], e["target"], e["relation"]) for e in edges}
    page = _make_id(_stem(PurePosixPath("page.html.twig")))
    base = _make_id(_stem(PurePosixPath("base.html.twig")))
    assert (page, base, "extends") in relations
    assert stats.blocks == 2
    assert stats.resolved == 1
    assert {n["_origin"] for n in nodes} == {"twig_extractor"}
