# -*- coding: utf-8 -*-
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "media" / "covers" / "_candidates"
OUT.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0"}

CANDIDATES = {
    "ruguy": [
        "https://treasure.qiandaocdn.com/treasure/images/ffyDozfSs5y.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/ffjeh1BPDTP.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/ff4uMMM0OHT.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/ffJvCO6pcvd.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/ffwtVs3FlcF.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/ff0EwWXN6Gn.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/ffY2SL3s9dB.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/ffQqXAYa0hi.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/ffK0Ote7TNP.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fi7PdMS8Yqg.jpg",
    ],
    "kongshan": [
        "https://treasure.qiandaocdn.com/treasure/images/EBIudlQfj4.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/EBIuGMYnG4.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/EBIuZJidrp.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/EBIuVYcZ0L.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/EBICy9czNr.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/EBIChZZWha.jpg",
    ],
    "liumang": [
        "https://treasure.qiandaocdn.com/treasure/images/gAdRF52lsJ.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/gAdR7v2478.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/gAdRCsltEB.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/gAdRKPoTXM.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/gAdtgiwJCE.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/gAdtbCw7qT.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/foTAkuMPBOH.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/foTAkK9YkNF.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/foTAkn3ioH1.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/foTAhfTfD1p.jpg",
    ],
    "lundun": [
        "https://treasure.qiandaocdn.com/treasure/images/e61d8959f1bd9565105c7055c9e30503.0b7f309ffd7d73061af5097343151193",
        "https://treasure.qiandaocdn.com/treasure/images/9f1cd635d89b08201cbad66417ac993e.3369272f021917c96a0f5d38fb5b345a",
        "https://treasure.qiandaocdn.com/treasure/images/e6eb7cf40db4653d99913acb260b0bf9.4ece5c7e8ce5b76256758521ef3a0657",
        "https://treasure.qiandaocdn.com/treasure/images/e2b1672dcd1f69c8ba88bb621d41f175.png",
        "https://treasure.qiandaocdn.com/treasure/images/42052112d31bf588fa88248489725a3f.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/02b628c9796a25ef84f215284de2caa8.png",
    ],
    "luoma": [
        "https://treasure.qiandaocdn.com/treasure/images/fi5gfTlz17n.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fi5gf7aKtXT.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fi5gfzN6uT8.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fi5gfEm5qeh.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fi5giv95KRd.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fi5giwsG8Zx.jpg",
    ],
    "tanhuan": [
        "https://treasure.qiandaocdn.com/treasure/images/fraJ6rudxDD.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fraJ6vTg6qa.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fraJ6vTg6qw.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fraJ6vTg6q7.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fraJ68Yg5W6.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fraJ6rudxDI.jpg",
    ],
    "qingbai": [
        "https://treasure.qiandaocdn.com/treasure/images/fBZrj0sDhLR.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fBZrjYjDXVY.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fBYtEnXGE8O.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fBmhZVNCugT.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/fBIdFDLjBTx.jpg",
        "https://treasure.qiandaocdn.com/treasure/images/frU7hAlvWZN.jpg",
    ],
}

for group, urls in CANDIDATES.items():
    for i, url in enumerate(urls, 1):
        data = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60).read()
        ext = ".png" if url.endswith(".png") or data[:4] == b"\x89PNG" else ".jpg"
        path = OUT / f"{group}-{i:02d}{ext}"
        path.write_bytes(data)
        print(path.name, len(data))
