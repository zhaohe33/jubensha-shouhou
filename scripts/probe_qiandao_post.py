# -*- coding: utf-8 -*-
import json
import urllib.request

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://qiandao.com",
    "Referer": "https://qiandao.com/spu?id=829151290914294958",
}

sid = "829151290914294958"
payload = json.dumps({"spuId": sid}).encode()

for url in [
    "https://api.qiandao.com/spu/detail",
    "https://api.qiandao.com/treasure/spu/detail",
    "https://api.qiandao.com/gactus/spu/detail",
    "https://api.qiandao.com/gactus-web/spu/detail",
    "https://api.qiandao.com/gactus-web/spu/get-detail",
]:
    req = urllib.request.Request(url, data=payload, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", "replace")
            print("OK", url, body[:800])
    except Exception as e:
        print("ERR", url, e)
