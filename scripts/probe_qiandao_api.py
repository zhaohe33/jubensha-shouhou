# -*- coding: utf-8 -*-
import json
import re
import urllib.request

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://qiandao.com",
    "Referer": "https://qiandao.com/",
}

SPU_IDS = {
    "如故": "829151290914294958",
    "暗夜降至": "914146012568751008",
    "洗劫伦敦所有的玫瑰": "599834651523163179",
    "洗劫罗马所有的情书": "865555922267699333",
    "流氓叙事": "766433918231567641",
    "空山": "786950357455535393",
    "贪欢": "913964331157200678",
    "青白": "911622777264466588",
}

ENDPOINTS = [
    "https://api.qiandao.com/spu/detail?spuId={id}",
    "https://api.qiandao.com/spu/get?spuId={id}",
    "https://api.qiandao.com/treasure/spu/detail?spuId={id}",
    "https://api.qiandao.com/treasure/v1/spu/detail?spuId={id}",
    "https://api.qiandao.com/gactus/spu/detail?spuId={id}",
    "https://api.qiandao.com/gactus-web/spu/detail?spuId={id}",
]


def try_get(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, body[:2000]
    except Exception as e:
        return -1, str(e)


sid = SPU_IDS["如故"]
for ep in ENDPOINTS:
    url = ep.format(id=sid)
    status, body = try_get(url)
    print(status, url)
    print(body[:500])
    print()
