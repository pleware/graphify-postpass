"""Resolve a Twig include path against the repo index (suffix + shared prefix)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from posixpath import normpath

from graphify_postpass.extractors.twig.index import TwigIndex

RE_LITERAL = re.compile(r"""^\(?\s*['"]([^'"]+)['"]""")
RE_CONCAT = re.compile(r"""^\(?\s*['"][^'"]*['"]\s*~""")
RE_SELF = re.compile(r"^\(?\s*_self\b")


class Outcome:
    RESOLVED = "resolved"
    SELF = "self"
    DYNAMIC = "dynamic"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class Resolution:
    outcome: str
    target: str | None = None
    raw: str = ""
    ambiguous: bool = False


class TwigResolver:
    def __init__(self, index: TwigIndex) -> None:
        self.index = index
        self._cache: dict[tuple[str, str], Resolution] = {}

    def resolve(self, source_rel: str, argument: str) -> Resolution:
        argument = argument.strip()
        key = (source_rel, argument)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        resolution = self._resolve_uncached(source_rel, argument)
        self._cache[key] = resolution
        return resolution

    def _resolve_uncached(self, source_rel: str, argument: str) -> Resolution:
        if RE_SELF.match(argument):
            return Resolution(Outcome.SELF, raw=argument)
        if RE_CONCAT.match(argument):
            return Resolution(Outcome.DYNAMIC, raw=argument)
        literal = RE_LITERAL.match(argument)
        if not literal:
            return Resolution(Outcome.DYNAMIC, raw=argument)
        target = _normalize(literal.group(1))
        if not target:
            return Resolution(Outcome.UNRESOLVED, raw=argument)
        if self.index.has(target):
            return Resolution(Outcome.RESOLVED, target=target, raw=argument)
        candidates = self.index.candidates(target)
        if not candidates:
            return Resolution(Outcome.UNRESOLVED, raw=argument)
        if len(candidates) == 1:
            return Resolution(Outcome.RESOLVED, target=candidates[0], raw=argument)
        best = max(candidates, key=lambda c: (_shared_depth(source_rel, c), -_depth(c)))
        return Resolution(Outcome.RESOLVED, target=best, raw=argument, ambiguous=True)


def _normalize(target: str) -> str:
    target = target.replace("\\", "/").strip()
    target = normpath(target).lstrip("/")
    return "" if target in (".", "..") else target


def _depth(rel: str) -> int:
    return rel.count("/")


def _shared_depth(a: str, b: str) -> int:
    a_parts = a.split("/")[:-1]
    b_parts = b.split("/")[:-1]
    shared = 0
    for x, y in zip(a_parts, b_parts):
        if x != y:
            break
        shared += 1
    return shared
