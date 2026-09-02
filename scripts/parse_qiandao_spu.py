# -*- coding: utf-8 -*-
import json
import re
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0"}

IDS = {
    "如故": "829151290914294958",
    "暗夜降至": "914146012568751008",
    "洗劫伦敦所有的玫瑰": "599834651523163179",
    "洗劫罗马所有的情书": "865555922267699333",
    "流氓叙事": "766433918231567641",
    "空山": None,  # find from search
    "贪欢": "913964331157200678",
    "青白": "911622777264466588",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_spu(html: str) -> dict:
    title_m = re.search(r"<title>([^<]+)</title>", html)
    title = title_m.group(1) if title_m else ""

    # Try embedded JSON payloads
    roles = []
    for pat in [
        r'"roleName":"([^"]+)".*?"image":"([^"]+)"',
        r'"name":"([^"]+)".*?"cover":"([^"]+)"',
        r'"characterName":"([^"]+)".*?"avatar":"([^"]+)"',
    ]:
        for name, img in re.findall(pat, html, re.S):
            if re.search(r"[\u4e00-\u9fff]", name):
                roles.append({"name": name, "image": img})

    # ld+json Product
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
        try:
            data = json.loads(m.group(1))
            if isinstance(data, dict):
                print("  ld+json keys:", list(data.keys())[:10])
        except json.JSONDecodeError:
            pass

    imgs = sorted(set(re.findall(r"https://cdn\.qiandaoapp\.com/[^\"'\s<>]+", html)))
    names = sorted(set(re.findall(r'"name":"([\u4e00-\u9fff·]{2,8})"', html)))
    return {"title": title, "roles": roles, "names": names, "imgs": imgs}


def find_spu_id(script: str) -> str | None:
    import urllib.parse

    q = urllib.parse.quote(script)
    html = fetch(f"https://qiandao.com/search?q={q}")
    for m in re.finditer(r"/spu\?id=(\d+)", html):
        return m.group(1)
    return None


if IDS["空山"] is None:
    IDS["空山"] = find_spu_id("空山")

for script, sid in IDS.items():
    if not sid:
        print(script, "NO ID")
        continue
    url = f"https://qiandao.com/spu?id={sid}"
    print(f"\n=== {script} ({sid}) ===")
    html = fetch(url)
    info = parse_spu(html)
    print("title:", info["title"])
    print("roles:", info["roles"][:12])
    print("names:", info["names"][:20])
    print("imgs:", len(info["imgs"]))
    for img in info["imgs"][:5]:
        print(" ", img)
