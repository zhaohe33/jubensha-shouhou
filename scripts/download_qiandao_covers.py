# -*- coding: utf-8 -*-
"""Download Qiandao character posters into media/covers/."""
from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "media" / "covers"
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# (output filename) -> treasure.qiandaocdn.com URL
DOWNLOADS: dict[str, str] = {
    "ruguy-weiziyao.jpg": "https://treasure.qiandaocdn.com/treasure/images/ff0EwWXN6Gn.jpg",
    "ruguy-lianshijiang.jpg": "https://treasure.qiandaocdn.com/treasure/images/ffjeh1BPDTP.jpg",
    "anye-jinzaixiu-poster.jpg": "https://treasure.qiandaocdn.com/treasure/images/fyLFKcbnXa4.jpg",
    "lundun-sidaila.png": "https://treasure.qiandaocdn.com/treasure/images/e2b1672dcd1f69c8ba88bb621d41f175.png",
    "luoma-dailin.jpg": "https://treasure.qiandaocdn.com/treasure/images/fi5gfTlz17n.jpg",
    "liumang-dailila.jpg": "https://treasure.qiandaocdn.com/treasure/images/foTAhfTfD1p.jpg",
    "liumang-chengzouliu-cover.jpg": "https://treasure.qiandaocdn.com/treasure/images/gAdRKPoTXM.jpg",
    "liumang-miaohongmo-cover.jpg": "https://treasure.qiandaocdn.com/treasure/images/gAdRF52lsJ.jpg",
    "kongshan-huaxiangrong-cover.jpg": "https://treasure.qiandaocdn.com/treasure/images/EBIuGMYnG4.jpg",
    "kongshan-aluniang-cover.jpg": "https://treasure.qiandaocdn.com/treasure/images/EBIudlQfj4.jpg",
    "qingbai-axi-cover.jpg": "https://treasure.qiandaocdn.com/treasure/images/fBYtEnXGE8O.jpg",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def main() -> None:
    for name, url in DOWNLOADS.items():
        data = fetch(url)
        path = OUT / name
        path.write_bytes(data)
        print(f"ok {name} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
