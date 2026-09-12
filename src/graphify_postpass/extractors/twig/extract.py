"""Regex extraction of Twig composition (not language syntax)."""

from __future__ import annotations

import re
from bisect import bisect_right
from dataclasses import dataclass, field

RE_COMMENT = re.compile(r"{#.*?#}", re.DOTALL)
RE_TEMPLATE_TAG = re.compile(
    r"{%-?\s*(extends|include|embed|import|from|use)\s+(.+?)\s*-?%}",
    re.DOTALL,
)
RE_TEMPLATE_FUNC = re.compile(r"\b(include|source)\(\s*(['\"][^'\"]+['\"])")
RE_TWIG_EXPR = re.compile(r"{{.*?}}|{%.*?%}", re.DOTALL)
RE_BLOCK = re.compile(r"{%-?\s*block\s+([A-Za-z_]\w*)")

RELATION_BY_TAG = {
    "extends": "extends",
    "include": "includes",
    "embed": "includes",
    "import": "imports",
    "from": "imports",
    "use": "imports",
    "source": "includes",
}


@dataclass
class TemplateRef:
    tag: str
    argument: str
    line: int


@dataclass
class BlockDef:
    name: str
    line: int


@dataclass
class TemplateFacts:
    rel_path: str
    refs: list[TemplateRef] = field(default_factory=list)
    blocks: list[BlockDef] = field(default_factory=list)
    source: str = ""
    twig_only: str = ""


def _mask_non_twig(text: str) -> str:
    """Keep ``{{ }}`` / ``{% %}``; turn the rest into spaces (offsets stay)."""
    masked = [" " if char != "\n" else "\n" for char in text]
    for match in RE_TWIG_EXPR.finditer(text):
        for i in range(match.start(), match.end()):
            masked[i] = text[i]
    return "".join(masked)


def line_starts(text: str) -> list[int]:
    starts = [0]
    for index, char in enumerate(text):
        if char == "\n":
            starts.append(index + 1)
    return starts


def line_of(starts: list[int], offset: int) -> int:
    return bisect_right(starts, offset)


def extract(rel_path: str, source: str) -> TemplateFacts:
    clean = RE_COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), source)
    starts = line_starts(clean)
    facts = TemplateFacts(rel_path=rel_path, source=clean, twig_only=_mask_non_twig(clean))

    for match in RE_TEMPLATE_TAG.finditer(clean):
        facts.refs.append(
            TemplateRef(
                tag=match.group(1),
                argument=match.group(2),
                line=line_of(starts, match.start()),
            )
        )
    for match in RE_TEMPLATE_FUNC.finditer(clean):
        facts.refs.append(
            TemplateRef(
                tag=match.group(1),
                argument=match.group(2),
                line=line_of(starts, match.start()),
            )
        )
    for match in RE_BLOCK.finditer(clean):
        facts.blocks.append(BlockDef(name=match.group(1), line=line_of(starts, match.start())))
    return facts
