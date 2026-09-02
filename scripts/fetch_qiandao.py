# -*- coding: utf-8 -*-
"""Fetch Qiandao script pages and extract character portrait URLs."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/json",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def extract_json_blobs(html: str) -> list:
    blobs = []
    for m in re.finditer(r"<script[^>]*>(\{.*?\})</script>", html, re.S):
        text = m.group(1)
        if "qiandao" in text.lower() or "spu" in text.lower() or "larp" in text.lower():
            blobs.append(text[:500])
    # NUXT payload
    m = re.search(r"window\.__NUXT__\s*=\s*(.+?)</script>", html, re.S)
    if m:
        blobs.append("NUXT:" + m.group(1)[:1000])
    return blobs


def find_urls(html: str) -> list[str]:
    patterns = [
        r"https://cdn\.qiandaoapp\.com/[^\"'\s<>]+",
        r"https://post\.qiandaocdn\.com/[^\"'\s<>]+",
        r"/spu\?id=\d+",
        r"/larp\?id=\d+",
        r"spuId[\"']?\s*[:=]\s*[\"']?(\d+)",
        r"larpId[\"']?\s*[:=]\s*[\"']?(\d+)",
    ]
    found = []
    for pat in patterns:
        found.extend(re.findall(pat, html))
    return found


SCRIPTS = [
    "如故",
    "暗夜降至",
    "洗劫伦敦所有的玫瑰",
    "洗劫罗马所有的情书",
    "流氓叙事",
    "空山",
    "贪欢",
    "青白",
]


def main() -> None:
    for name in SCRIPTS:
        q = urllib.parse.quote(name)
        url = f"https://qiandao.com/search?q={q}"
        print(f"\n=== {name} ===")
        try:
            html = fetch(url)
        except Exception as e:
            print("fetch error", e)
            continue
        urls = find_urls(html)
        print("matches", urls[:20])
        blobs = extract_json_blobs(html)
        print("blobs", len(blobs))
        for b in blobs[:2]:
            print(b[:300])


if __name__ == "__main__":
    main()
