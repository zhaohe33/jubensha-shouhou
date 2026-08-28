# -*- coding: utf-8 -*-
"""Copy site assets into dist/ for Cloudflare Pages (25 MiB upload limit)."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

SKIP_DIRS = {
    ".git",
    ".git.bak-hub",
    ".github",
    ".wrangler",
    "__pycache__",
    "dist",
    "functions",
    "scripts",
    "media/refs",
    "media/covers/_candidates",
}

SKIP_FILE_SUFFIXES = {".mp4"}
SKIP_REL_PREFIXES = (
    "暗夜降至/",
    "空山/",
    "流氓叙事/",
)


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("."):
        return True
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    if path.suffix.lower() in SKIP_FILE_SUFFIXES and any(
        rel.startswith(prefix) for prefix in SKIP_REL_PREFIXES
    ):
        return True
    return False


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    for src in ROOT.rglob("*"):
        if src.is_dir():
            continue
        if should_skip(src):
            continue
        dest = DIST / src.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    count = sum(1 for _ in DIST.rglob("*") if _.is_file())
    print(f"Prepared deploy bundle ({count} files)")


if __name__ == "__main__":
    main()
