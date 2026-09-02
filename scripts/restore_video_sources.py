# -*- coding: utf-8 -*-
"""Restore missing 空山 / 暗夜降至 source folders for build_site.py."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RESTORES = [
    (
        ROOT / "暗夜降至" / "车允智" / "金在秀" / "6a51b0d719effa4cabff8b7776fe4f2d.mp4",
        ROOT / "media" / "anye-jinzaixiu.mp4",
    ),
    (
        ROOT / "空山" / "李逸" / "花想容" / "bc5c6664746526f8eee4b9f1b1915346.mp4",
        ROOT / "media" / "kongshan-huaxiangrong.mp4",
    ),
    (
        ROOT / "空山" / "李逸" / "阿绿姑娘" / "ee9c7ad14a3dd9ddaffa0000c26286aa.mp4",
        ROOT / "media" / "kongshan-aluniang.mp4",
    ),
]


def link_or_copy(dst: Path, src: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    if not src.exists():
        raise FileNotFoundError(src)
    try:
        dst.hardlink_to(src)
    except OSError:
        shutil.copy2(src, dst)


def main() -> None:
    for dst, src in RESTORES:
        link_or_copy(dst, src)
        print(f"restored {dst.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
