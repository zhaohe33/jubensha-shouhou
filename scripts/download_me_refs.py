# -*- coding: utf-8 -*-
"""Download Qiandao立绘 for the player's own characters (me)."""
from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "media" / "refs"
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

ME_URLS = {
    "李文瑙": "https://treasure.qiandaocdn.com/treasure/images/ffyDozfSs5y.jpg",
    "车允智": "https://treasure.qiandaocdn.com/treasure/images/ffFDmuv9fm7.png",
    "阿尔芒": "https://treasure.qiandaocdn.com/treasure/images/42052112d31bf588fa88248489725a3f.jpg",
    "维托": "https://treasure.qiandaocdn.com/treasure/images/fi5giwsG8Zx.jpg",
    "程聿怀": "https://treasure.qiandaocdn.com/treasure/images/foTAkK9YkNF.jpg",
    "蒋伯驾": "https://treasure.qiandaocdn.com/treasure/images/foTAkn3ioH1.jpg",
    "李逸": "https://treasure.qiandaocdn.com/treasure/images/EBICy9czNr.jpg",
    "林江": "https://treasure.qiandaocdn.com/treasure/images/fraJ6rudxDD.jpg",
    "苏无恙": "https://treasure.qiandaocdn.com/treasure/images/fBIdFDLjBTx.jpg",
}

SLUG = {
    "李文瑙": "liwennao",
    "车允智": "cheyunzhi",
    "阿尔芒": "aermang",
    "维托": "weituo",
    "程聿怀": "chengyuhuai",
    "蒋伯驾": "jiangbojia",
    "李逸": "liyi",
    "林江": "linjiang",
    "苏无恙": "suwuyang",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def main() -> None:
    for name, url in ME_URLS.items():
        data = fetch(url)
        ext = ".png" if url.endswith(".png") or data[:4] == b"\x89PNG" else ".jpg"
        path = OUT / f"{SLUG[name]}{ext}"
        path.write_bytes(data)
        print(path.name, len(data))


if __name__ == "__main__":
    main()
