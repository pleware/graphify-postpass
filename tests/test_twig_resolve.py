from pathlib import Path

from graphify_postpass.extractors.twig.index import TwigIndex
from graphify_postpass.extractors.twig.resolve import Outcome, TwigResolver

ROOT = Path("/repo")


def make_index(paths: list[str]) -> TwigIndex:
    return TwigIndex(ROOT, paths)


def test_exact_path():
    result = TwigResolver(make_index(["views/a/b.html.twig"])).resolve(
        "views/x.html.twig", "'views/a/b.html.twig'"
    )
    assert result.outcome == Outcome.RESOLVED
    assert result.target == "views/a/b.html.twig"
    assert result.ambiguous is False


def test_suffix_match_unique():
    result = TwigResolver(make_index(["ext/app/view/partials/nav.html.twig"])).resolve(
        "ext/app/view/page.html.twig", "'partials/nav.html.twig'"
    )
    assert result.target == "ext/app/view/partials/nav.html.twig"


def test_prefers_nearest_loader_root():
    index = make_index(
        [
            "ext/app_one/view/partials/nav.html.twig",
            "ext/app_two/view/partials/nav.html.twig",
        ]
    )
    result = TwigResolver(index).resolve(
        "ext/app_one/view/cart.html.twig", "'partials/nav.html.twig'"
    )
    assert result.target == "ext/app_one/view/partials/nav.html.twig"
    assert result.ambiguous is True


def test_self_reference():
    result = TwigResolver(make_index(["a.html.twig"])).resolve("a.html.twig", "_self as macros")
    assert result.outcome == Outcome.SELF


def test_variable_is_dynamic():
    result = TwigResolver(make_index(["a.html.twig"])).resolve("a.html.twig", "template")
    assert result.outcome == Outcome.DYNAMIC


def test_concatenation_is_dynamic_not_unresolved():
    result = TwigResolver(make_index(["a.html.twig"])).resolve(
        "a.html.twig", "'agreements/' ~ type ~ '.twig'"
    )
    assert result.outcome == Outcome.DYNAMIC


def test_leading_slash_normalized():
    result = TwigResolver(make_index(["views/sel.html.twig"])).resolve(
        "views/x.html.twig", "'/views/sel.html.twig'"
    )
    assert result.target == "views/sel.html.twig"


def test_non_twig_target_resolves():
    result = TwigResolver(
        make_index(["assets/mails/apps/style.css", "assets/mails/a.html.twig"])
    ).resolve("assets/mails/a.html.twig", "'apps/style.css'")
    assert result.target == "assets/mails/apps/style.css"


def test_unknown_target_unresolved():
    result = TwigResolver(make_index(["a.html.twig"])).resolve("a.html.twig", "'missing.html.twig'")
    assert result.outcome == Outcome.UNRESOLVED


def test_suffix_match_respects_segment_boundary():
    result = TwigResolver(make_index(["x/nav.html.twig"])).resolve("a.html.twig", "'av.html.twig'")
    assert result.outcome == Outcome.UNRESOLVED


def test_tie_break_is_deterministic():
    paths = ["b/x/n.html.twig", "a/x/n.html.twig", "c/x/n.html.twig"]
    first = TwigResolver(make_index(paths)).resolve("z.html.twig", "'x/n.html.twig'")
    second = TwigResolver(make_index(list(reversed(paths)))).resolve(
        "z.html.twig", "'x/n.html.twig'"
    )
    assert first.target == second.target
