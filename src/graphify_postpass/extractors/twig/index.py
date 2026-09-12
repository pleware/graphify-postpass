"""One ``git ls-files`` index. Templates also include non-Twig assets."""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

TEMPLATE_SUFFIX = ".twig"


class TwigIndex:
    def __init__(self, root: Path, rel_paths: list[str]) -> None:
        self.root = root
        self.paths: list[str] = sorted(rel_paths)
        self._by_path: set[str] = set(self.paths)
        self.templates: list[str] = [p for p in self.paths if p.endswith(TEMPLATE_SUFFIX)]
        self._by_suffix: dict[str, list[str]] = {}
        for rel in self.paths:
            parts = rel.split("/")
            for i in range(len(parts)):
                self._by_suffix.setdefault("/".join(parts[i:]), []).append(rel)
        for bucket in self._by_suffix.values():
            bucket.sort(key=_specificity)

    @classmethod
    def from_git(cls, root: Path) -> TwigIndex:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        rel_paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return cls(root, rel_paths)

    def has(self, rel_path: str) -> bool:
        return rel_path in self._by_path

    def candidates(self, target: str) -> list[str]:
        return self._by_suffix.get(target, [])

    def __len__(self) -> int:
        return len(self.paths)


def _specificity(rel: str) -> tuple[int, str]:
    return (len(PurePosixPath(rel).parts), rel)
