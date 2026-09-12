from graphify_postpass.extractors.twig.extract import extract


def test_tags_and_blocks():
    source = (
        "{% extends 'base.html.twig' %}\n"
        "{% block content %}\n"
        "{% include 'p/a.html.twig' %}\n"
        "{% import 'macros.html.twig' as m %}\n"
        "{% from 'f.html.twig' import x %}\n"
        "{% endblock %}\n"
    )
    facts = extract("a.html.twig", source)
    assert [r.tag for r in facts.refs] == ["extends", "include", "import", "from"]
    assert [b.name for b in facts.blocks] == ["content"]
    assert facts.refs[0].line == 1
    assert facts.refs[1].line == 3


def test_whitespace_control_variants():
    facts = extract("a.html.twig", "{%- extends 'b.html.twig' -%}")
    assert [r.tag for r in facts.refs] == ["extends"]


def test_comments_are_ignored():
    source = "{# {% include 'old.html.twig' %} #}\n{% include 'new.html.twig' %}\n"
    facts = extract("a.html.twig", source)
    assert len(facts.refs) == 1
    assert "new" in facts.refs[0].argument
    assert facts.refs[0].line == 2


def test_line_numbers_survive_multiline_comment():
    source = "{#\n\n#}\n{% extends 'b.html.twig' %}\n"
    facts = extract("a.html.twig", source)
    assert facts.refs[0].line == 4


def test_include_function_form():
    facts = extract("a.html.twig", "{{ include('p/a.html.twig') }}")
    assert [r.tag for r in facts.refs] == ["include"]


def test_masking_removes_html_and_js():
    source = "<script>$('#x').val();</script>\n{{ obj.method() }}\n"
    facts = extract("a.html.twig", source)
    assert "val" not in facts.twig_only
    assert "obj.method()" in facts.twig_only
    assert len(facts.twig_only) == len(facts.source)
    assert facts.twig_only.count("\n") == facts.source.count("\n")
