# -*- coding: utf-8 -*-
"""Scan 剧本/我的角色/售后角色 and generate hub + letter pages."""
from __future__ import annotations

import base64
import html
import json
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {".git", ".git.bak-hub", "__pycache__", "pages", "media", "scripts", ".github", "functions", "create", "browse", "dist", ".wrangler"}
# GitHub Pages is often slow/blocked in CN; serve media via jsDelivr
CDN_BASE = "https://cdn.jsdelivr.net/gh/zhaohe33/jubensha-shouhou@main/"
PAGES_BASE = "https://zhaohe33.github.io/jubensha-shouhou/"

# Map original video paths -> ASCII media/*.mp4 for reliable web playback
VIDEO_ALIASES = {
    "暗夜降至/车允智/金在秀/6a51b0d719effa4cabff8b7776fe4f2d.mp4": "media/anye-jinzaixiu.mp4",
    "空山/李逸/花想容/bc5c6664746526f8eee4b9f1b1915346.mp4": "media/kongshan-huaxiangrong.mp4",
    "空山/李逸/阿绿姑娘/ee9c7ad14a3dd9ddaffa0000c26286aa.mp4": "media/kongshan-aluniang.mp4",
    "流氓叙事/蒋伯驾/程走柳/视频.mp4": "media/liumang-chengzouliu.mp4",
}

PDF_ALIASES = {
    "流氓叙事/程聿怀/程走柳/经典程家菜.pdf": "media/liumang-chengjia-cai.pdf",
}

IMAGE_ALIASES = {
    "流氓叙事/蒋伯驾/缪宏谟/0c007671bb0e112e1da943bb431d99f5.jpg": "media/liumang-miaohongmo.jpg",
    "贪欢/林江/武宁/images/spring.jpg": "media/tan-huan-spring.jpg",
    "贪欢/林江/武宁/images/summer.jpg": "media/tan-huan-summer.jpg",
    "贪欢/林江/武宁/images/autumn.jpg": "media/tan-huan-autumn.jpg",
    "贪欢/林江/武宁/images/winter.jpg": "media/tan-huan-winter.jpg",
    "青白/苏无恙/阿喜/images/ChatGPT-Image-Jun-22--20-1782112485554.jpg": "media/qingbai-axi.jpg",
}

AUDIO_ALIASES = {
    "贪欢/林江/武宁/music/bgm-soft.mp3": "media/tan-huan-bgm.mp3",
}

# Hub card covers sourced from Qiandao script pages (treasure.qiandaocdn.com).
COVER_ALIASES: dict[tuple[str, str, str], str] = {
    ("如故", "李文瑙", "卫子谣"): "media/covers/ruguy-weiziyao.jpg",
    ("如故", "李文瑙", "连世疆"): "media/covers/ruguy-lianshijiang.jpg",
    ("暗夜降至", "车允智", "金在秀"): "media/covers/anye-jinzaixiu-poster.jpg",
    ("洗劫伦敦所有的玫瑰", "阿尔芒", "斯黛拉"): "media/covers/lundun-sidaila.png",
    ("洗劫罗马所有的情书", "维托", "黛琳"): "media/covers/luoma-dailin.jpg",
    ("流氓叙事", "程聿怀", "黛利拉"): "media/covers/liumang-dailila.jpg",
    ("流氓叙事", "程聿怀", "程走柳"): "media/covers/liumang-chengzouliu-cover.jpg",
    ("流氓叙事", "蒋伯驾", "程走柳"): "media/covers/liumang-chengzouliu-cover.jpg",
    ("流氓叙事", "蒋伯驾", "缪宏谟"): "media/covers/liumang-miaohongmo-cover.jpg",
    ("空山", "李逸", "花想容"): "media/covers/kongshan-huaxiangrong-cover.jpg",
    ("空山", "李逸", "阿绿姑娘"): "media/covers/kongshan-aluniang-cover.jpg",
    ("青白", "苏无恙", "阿喜"): "media/covers/qingbai-axi-cover.jpg",
}

# AI duo portraits (player character + letter recipient) for hub cards.
DUO_COVER_ALIASES: dict[tuple[str, str, str], str] = {
    ("如故", "李文瑙", "卫子谣"): "media/duos/ruguy-liwennao-weiziyao.jpg",
    ("如故", "李文瑙", "连世疆"): "media/duos/ruguy-liwennao-lianshijiang.jpg",
    ("暗夜降至", "车允智", "金在秀"): "media/duos/anye-cheyunzhi-jinzaixiu.jpg",
    ("洗劫伦敦所有的玫瑰", "阿尔芒", "斯黛拉"): "media/duos/lundun-aermang-sidaila.jpg",
    ("洗劫罗马所有的情书", "维托", "黛琳"): "media/duos/luoma-weituo-dailin.jpg",
    ("流氓叙事", "程聿怀", "黛利拉"): "media/duos/liumang-chengyuhuai-dailila.jpg",
    ("流氓叙事", "程聿怀", "程走柳"): "media/duos/liumang-chengyuhuai-chengzouliu.jpg",
    ("流氓叙事", "蒋伯驾", "程走柳"): "media/duos/liumang-jiangbojia-chengzouliu.jpg",
    ("流氓叙事", "蒋伯驾", "缪宏谟"): "media/duos/liumang-jiangbojia-miaohongmo.jpg",
    ("空山", "李逸", "花想容"): "media/duos/kongshan-liyi-huaxiangrong.jpg",
    ("空山", "李逸", "阿绿姑娘"): "media/duos/kongshan-liyi-aluniang.jpg",
    ("贪欢", "林江", "武宁"): "media/duos/tanhuan-linjiang-wuning.jpg",
    ("青白", "苏无恙", "阿喜"): "media/duos/qingbai-suwuyang-axi.jpg",
}


def cdn_url(rel_posix_path: str) -> str:
    """Build a jsDelivr URL for a repo-relative posix path."""
    parts = rel_posix_path.replace("\\", "/").split("/")
    return CDN_BASE + "/".join(urllib.parse.quote(p) for p in parts if p)


def pages_url(rel_posix_path: str) -> str:
    parts = rel_posix_path.replace("\\", "/").split("/")
    return PAGES_BASE + "/".join(urllib.parse.quote(p) for p in parts if p)


def alias_for(rel_posix_path: str) -> str:
    key = rel_posix_path.replace("\\", "/")
    for table in (VIDEO_ALIASES, PDF_ALIASES, IMAGE_ALIASES, AUDIO_ALIASES):
        alias = table.get(key)
        if alias and (ROOT / alias).exists():
            return alias
    return key


def asset_url(rel_posix_path: str, from_rel: str = "index.html") -> str:
    """Repo-relative asset URL from a generated HTML file path."""
    path = alias_for(rel_posix_path)
    prefix = depth_prefix(from_rel)
    parts = path.replace("\\", "/").split("/")
    return prefix + "/".join(urllib.parse.quote(p) for p in parts if p)


def video_play_url(rel_posix_path: str) -> str:
    """Prefer ASCII media/ alias; fall back to Pages URL."""
    alias = VIDEO_ALIASES.get(rel_posix_path.replace("\\", "/"))
    if alias and (ROOT / alias).exists():
        return pages_url(alias)
    return pages_url(rel_posix_path)

LETTER_CSS = """
:root {
  --ink: #100e0c;
  --paper: #efe6d6;
  --paper-soft: #cfc3ae;
  --fade: rgba(239, 230, 214, 0.55);
  --seal: #9c2f2a;
  --line: rgba(239, 230, 214, 0.16);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Noto Serif SC", "Songti SC", serif;
  color: var(--paper);
  background: var(--ink);
  line-height: 1.95;
  min-height: 100vh;
}
body::before {
  content: "";
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 80% 55% at 12% 8%, rgba(120, 48, 40, 0.18), transparent 55%),
    radial-gradient(ellipse 70% 50% at 88% 18%, rgba(70, 58, 40, 0.16), transparent 50%),
    linear-gradient(180deg, #0c0a09 0%, #14110e 50%, #0f0d0b 100%);
}
.wrap { position: relative; z-index: 2; max-width: 720px; margin: 0 auto; padding: 2.5rem 1.35rem 4rem; }
.back {
  display: inline-flex; align-items: center; gap: 0.4rem;
  color: var(--fade); text-decoration: none; font-size: 0.82rem; letter-spacing: 0.22em;
  margin-bottom: 2.2rem; transition: color .25s;
}
.back:hover { color: var(--paper); }
.meta { font-size: 0.78rem; letter-spacing: 0.28em; color: rgba(156,47,42,.85); margin-bottom: 0.85rem; }
h1 {
  font-family: "Ma Shan Zheng", cursive;
  font-size: clamp(2.4rem, 8vw, 3.4rem);
  letter-spacing: 0.16em; line-height: 1.15; margin-bottom: 0.4rem;
}
.sub { color: var(--paper-soft); letter-spacing: 0.12em; font-size: 0.95rem; margin-bottom: 2rem; }
.line { width: 2.2rem; height: 1px; background: var(--seal); margin: 0 0 2rem; }
.prose p { margin-bottom: 1.15rem; letter-spacing: 0.04em; }
.prose p:last-child { margin-bottom: 0; }
.media { margin: 1.6rem 0 0; }
.media video, .media img {
  width: 100%; display: block; border: 1px solid var(--line);
  background: #000;
}
.media a.pdf {
  display: inline-flex; margin-top: 1rem; padding: 0.7rem 1.1rem;
  border: 1px solid rgba(239,230,214,.35); color: var(--paper);
  text-decoration: none; letter-spacing: 0.2em; font-size: 0.88rem;
}
.media a.pdf:hover { border-color: rgba(239,230,214,.7); }
.empty { color: var(--fade); letter-spacing: 0.08em; }
"""


def rel_posix(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_url_file(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"URL=(.+)", text)
    return m.group(1).strip() if m else None


def decode_share_payload(url: str) -> dict:
    """Decode jubensha-aftersale share link (?s=...) into title/text/image/youtube."""
    try:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        s = qs.get("s", [""])[0]
        if not s:
            return {}
        pad = "=" * (-len(s) % 4)
        data = json.loads(base64.urlsafe_b64decode(s + pad))
        return {
            "title": data.get("t") or "",
            "text": data.get("c") or "",
            "image": data.get("u") or "",
            "youtube": data.get("y") or "",
        }
    except Exception:
        return {}


def is_rich_page(path: Path | None) -> bool:
    if not path or not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return ("hero-brand" in text) or ('class="season"' in text)


def text_to_paragraphs(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []
    parts = re.split(r"\n\s*\n", text)
    out = []
    for part in parts:
        lines = [ln.strip() for ln in part.split("\n") if ln.strip()]
        if lines:
            out.append("<br />\n".join(html.escape(ln) for ln in lines))
    return out


def plain_paragraphs(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []
    parts = re.split(r"\n\s*\n", text)
    out = []
    for part in parts:
        lines = [ln.strip() for ln in part.split("\n") if ln.strip()]
        if lines:
            out.append("\n".join(lines))
    return out


VIDEO_PLACEHOLDER_RE = re.compile(r"^——?\s*[（(]\s*视频\s*[）)]\s*$")


def video_embed_html(v: str, prefix: str) -> str:
    alias = VIDEO_ALIASES.get(v.replace("\\", "/"))
    if alias and (ROOT / alias).exists():
        rel_src = prefix + alias
        return (
            "        <div class=\"media inline-video\">\n"
            "        <video controls playsinline preload=\"metadata\">\n"
            f'          <source src="{html.escape(rel_src)}" type="video/mp4" />\n'
            "        </video>\n"
            f'        <a class="pdf" href="{html.escape(rel_src)}" target="_blank" rel="noopener">若无法播放，点此打开/下载视频</a>\n'
            "        </div>"
        )
    src = prefix + v.replace("\\", "/")
    return (
        "        <div class=\"media inline-video\">\n"
        f'        <video controls playsinline preload="metadata" src="{html.escape(src)}"></video>\n'
        f'        <a class="pdf" href="{html.escape(src)}" target="_blank" rel="noopener">若无法播放，点此打开/下载视频</a>\n'
        "        </div>"
    )


def first_line_blurb(text: str, fallback: str) -> str:
    for line in text.replace("\r\n", "\n").split("\n"):
        s = line.strip().strip("：:，,")
        if s and not s.startswith("致") and len(s) > 4:
            return s[:42] + ("…" if len(s) > 42 else "")
        if s.startswith("致") and "，" in s:
            return s
    return fallback


def collect_entries() -> list[dict]:
    entries: list[dict] = []

    for script_dir in sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP_DIRS and not p.name.startswith(".")], key=lambda p: p.name):
        # skip if only contains .git somehow
        for me_dir in sorted([p for p in script_dir.iterdir() if p.is_dir() and p.name not in SKIP_DIRS], key=lambda p: p.name):
            # files directly under me_dir (e.g. 黛利拉.txt or loose video)
            loose_files = [p for p in me_dir.iterdir() if p.is_file()]
            loose_txt = [p for p in loose_files if p.suffix.lower() == ".txt"]
            loose_media = [p for p in loose_files if p.suffix.lower() in {".mp4", ".webm", ".jpg", ".jpeg", ".png", ".pdf", ".mp3"}]

            for txt in loose_txt:
                target = txt.stem
                entries.append(make_entry(script_dir.name, me_dir.name, target, me_dir, extra_files=[txt]))

            # if only media at me level (暗夜降至)
            if loose_media and not any(p.is_dir() and p.name not in SKIP_DIRS for p in me_dir.iterdir()) and not loose_txt:
                entries.append(make_entry(script_dir.name, me_dir.name, "售后", me_dir, extra_files=loose_media))

            for target_dir in sorted([p for p in me_dir.iterdir() if p.is_dir() and p.name not in SKIP_DIRS], key=lambda p: p.name):
                entries.append(make_entry(script_dir.name, me_dir.name, target_dir.name, target_dir))

    return entries


def make_entry(script: str, me: str, target: str, folder: Path, extra_files: list[Path] | None = None) -> dict:
    if extra_files is not None:
        files = list(extra_files)
    elif folder.is_dir():
        files = [p for p in folder.iterdir() if p.is_file()]
    else:
        files = []

    url_files = [p for p in files if p.suffix.lower() == ".url"]
    html_files = [p for p in files if p.name.lower() == "index.html"]
    txt_files = [p for p in files if p.suffix.lower() == ".txt"]
    videos = [p for p in files if p.suffix.lower() in {".mp4", ".webm"}]
    images = [p for p in files if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}]
    pdfs = [p for p in files if p.suffix.lower() == ".pdf"]

    # Prefer nested images folder covers for hub
    cover = None
    images_dir = folder / "images" if folder.is_dir() else None
    if images_dir and images_dir.is_dir():
        for name in ("spring.jpg", "ChatGPT-Image-Jun-22--20-1782112485554.jpg"):
            cand = images_dir / name
            if cand.exists():
                cover = rel_posix(cand)
                break
        if not cover:
            imgs = sorted(images_dir.glob("*"))
            imgs = [p for p in imgs if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
            if imgs:
                cover = rel_posix(imgs[0])
    if not cover and images:
        cover = rel_posix(images[0])

    hub_cover = DUO_COVER_ALIASES.get((script, me, target))
    if not hub_cover:
        hub_cover = COVER_ALIASES.get((script, me, target))
    if hub_cover and (ROOT / hub_cover).exists():
        cover = hub_cover

    existing_src = html_files[0] if html_files else None
    share_url = read_url_file(url_files[0]) if url_files else None
    share = decode_share_payload(share_url) if share_url else {}

    # gallery: leaf images + images/ folder
    gallery: list[str] = [rel_posix(p) for p in images]
    if images_dir and images_dir.is_dir():
        for p in sorted(images_dir.iterdir()):
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                gallery.append(rel_posix(p))
    # de-dupe preserve order
    seen = set()
    gallery_unique = []
    for g in gallery:
        if g not in seen:
            seen.add(g)
            gallery_unique.append(g)
    gallery = gallery_unique

    audios = []
    music_dir = folder / "music" if folder.is_dir() else None
    if music_dir and music_dir.is_dir():
        for p in sorted(music_dir.iterdir()):
            if p.suffix.lower() in {".mp3", ".m4a", ".ogg", ".wav"}:
                audios.append(rel_posix(p))

    text_body = ""
    preferred = None
    for p in txt_files:
        if "给" in p.stem or p.stem == "文字" or p.stem == target:
            preferred = p
            break
    if not preferred and txt_files:
        preferred = txt_files[0]
    if preferred:
        text_body = preferred.read_text(encoding="utf-8")
    elif share.get("text"):
        text_body = share["text"]

    remote_image = share.get("image") or ""
    youtube = share.get("youtube") or ""
    if cover and not str(cover).startswith("http"):
        cover = asset_url(cover, "index.html")
    elif not cover and remote_image:
        cover = remote_image

    title = share.get("title") or (f"致{target}" if target != "售后" else f"{me} · 售后")
    blurb = first_line_blurb(text_body, f"{me} → {target}") if text_body.strip() else (
        "视频售后" if videos else ("图文售后" if gallery else ("附件售后" if pdfs else "售后"))
    )

    view_rel = f"pages/{script}/{me}/{target}/index.html"
    folder_rel = rel_posix(folder) if folder.is_dir() else rel_posix(folder.parent)

    return {
        "script": script,
        "me": me,
        "target": target,
        "title": title,
        "blurb": blurb,
        "cover": cover,
        "rich_src": rel_posix(existing_src) if is_rich_page(existing_src) else None,
        "view_rel": view_rel,
        "text": text_body,
        "videos": [rel_posix(p) for p in videos],
        "images_only": gallery,
        "remote_image": remote_image,
        "audios": audios,
        "youtube": youtube,
        "pdfs": [rel_posix(p) for p in pdfs],
        "folder": folder_rel,
    }


def href_for(entry: dict) -> str:
    return entry["view_rel"]


def depth_prefix(rel_path: str) -> str:
    # parts include the filename; climb from the file's directory to repo root
    return "../" * (len(Path(rel_path).parts) - 1)


def youtube_id(url: str) -> str | None:
    if not url:
        return None
    m = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{6,})", url)
    return m.group(1) if m else None


def write_rich_page(entry: dict) -> None:
    """Adapt an existing immersive page into pages/ with reliable asset URLs."""
    src = ROOT / entry["rich_src"]
    out = ROOT / entry["view_rel"]
    out.parent.mkdir(parents=True, exist_ok=True)
    prefix = depth_prefix(entry["view_rel"])
    folder = entry["folder"]
    text = src.read_text(encoding="utf-8")

    # Map known local relative assets to ASCII media URLs / Pages URLs
    folder_path = ROOT / folder
    for sub in ("images", "music"):
        d = folder_path / sub
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if not f.is_file():
                continue
            rel = rel_posix(f)
            url = asset_url(rel, entry["view_rel"])
            text = re.sub(
                rf'src=(["\']){re.escape(sub + "/" + f.name)}(?:\?[^"\']*)?\1',
                lambda m, u=url: f"src={m.group(1)}{u}{m.group(1)}",
                text,
            )

    back = (
        f'<a href="{prefix}browse/" style="position:fixed;top:1rem;left:1rem;z-index:50;'
        f'color:rgba(239,230,214,.7);text-decoration:none;font-size:.82rem;letter-spacing:.22em;'
        f'font-family:Noto Serif SC,Songti SC,serif;padding:.45rem .75rem;'
        f'border:1px solid rgba(239,230,214,.18);background:rgba(16,14,12,.55);'
        f'backdrop-filter:blur(8px)">← 返回合集</a>\n'
    )
    if "<body>" in text:
        text = text.replace("<body>", "<body>\n" + back, 1)
    else:
        text = back + text
    out.write_text(text, encoding="utf-8")


def write_letter_page(entry: dict) -> None:
    if entry.get("rich_src"):
        write_rich_page(entry)
        return

    out = ROOT / entry["view_rel"]
    out.parent.mkdir(parents=True, exist_ok=True)
    prefix = depth_prefix(entry["view_rel"])

    videos = list(entry["videos"])
    video_i = 0
    prose_parts: list[str] = []
    for para in plain_paragraphs(entry["text"]):
        if VIDEO_PLACEHOLDER_RE.match(para.strip()) and video_i < len(videos):
            prose_parts.append(video_embed_html(videos[video_i], prefix))
            video_i += 1
        else:
            escaped = "<br />\n".join(html.escape(ln) for ln in para.split("\n"))
            prose_parts.append(f"        <p>{escaped}</p>")
    prose = "\n".join(prose_parts) if prose_parts else '        <p class="empty">（暂无文字）</p>'

    media_blocks = []
    # Prefer local gallery; else remote share image
    shown_images = list(entry["images_only"])
    if not shown_images and entry.get("remote_image"):
        shown_images = [entry["remote_image"]]

    # Only leftover videos (not placed inline) go to the bottom
    for v in videos[video_i:]:
        media_blocks.append(video_embed_html(v, prefix))
    for img in shown_images:
        if img.startswith("http"):
            src = img
        else:
            src = asset_url(img, entry["view_rel"])
        media_blocks.append(
            f'        <img src="{html.escape(src)}" alt="{html.escape(entry["title"])}" />'
        )
    for audio in entry.get("audios") or []:
        src = asset_url(audio, entry["view_rel"])
        media_blocks.append(
            f'        <audio controls preload="metadata" src="{html.escape(src)}"></audio>'
        )
    yt = youtube_id(entry.get("youtube") or "")
    if yt:
        media_blocks.append(
            '        <div class="music-embed">\n'
            '          <p class="music-label">背景音乐</p>\n'
            f'          <iframe src="https://www.youtube.com/embed/{html.escape(yt)}?rel=0&loop=1&playlist={html.escape(yt)}" '
            'title="背景音乐" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            'allowfullscreen loading="lazy"></iframe>\n'
            f'          <a class="pdf" href="{html.escape(entry["youtube"])}" target="_blank" rel="noopener">在 YouTube 打开</a>\n'
            "        </div>"
        )
    elif entry.get("youtube"):
        media_blocks.append(
            f'        <a class="pdf" href="{html.escape(entry["youtube"])}" target="_blank" rel="noopener">打开背景音乐</a>'
        )
    for pdf in entry["pdfs"]:
        key = pdf.replace("\\", "/")
        alias = PDF_ALIASES.get(key)
        src = asset_url(alias if alias and (ROOT / alias).exists() else pdf, entry["view_rel"])
        media_blocks.append(
            f'        <a class="pdf" href="{html.escape(src)}" target="_blank" rel="noopener">打开附件 PDF</a>'
        )
    media_html = ""
    if media_blocks:
        media_html = '      <div class="media">\n' + "\n".join(media_blocks) + "\n      </div>"

    # For letter-with-image pages, show image after first paragraph feel: image first if only image+text
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(entry['title'])} · {html.escape(entry['script'])}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>{LETTER_CSS}
.media audio {{ width: 100%; margin-top: 1rem; }}
.inline-video {{ margin: 1.6rem 0 1.8rem; }}
.music-embed {{ margin-top: 1.4rem; }}
.music-embed .music-label {{
  font-size: 0.82rem; letter-spacing: 0.28em; color: var(--fade); margin-bottom: 0.7rem;
}}
.music-embed iframe {{
  width: 100%; aspect-ratio: 16 / 9; border: 1px solid var(--line); background: #000;
}}
  </style>
</head>
<body>
  <div class="wrap">
    <a class="back" href="{prefix}browse/">← 返回合集</a>
    <p class="meta">剧本 · {html.escape(entry['script'])}　/　我方 · {html.escape(entry['me'])}</p>
    <h1>{html.escape(entry['title'])}</h1>
    <p class="sub">{html.escape(entry['me'])} → {html.escape(entry['target'])}</p>
    <div class="line" aria-hidden="true"></div>
    <article class="prose">
{prose}
    </article>
{media_html}
  </div>
</body>
</html>
"""
    out.write_text(page, encoding="utf-8")


def site_nav(active: str, depth: str = "") -> str:
    """Shared top nav: active is 'home' | 'browse' | 'create'."""
    home = f"{depth}index.html"
    browse = f"{depth}browse/"
    create = f"{depth}create/"
    def cls(name: str) -> str:
        return "site-nav__link is-active" if active == name else "site-nav__link"
    return f"""
    <nav class="site-nav" aria-label="站点导航">
      <a class="{cls('home')}" href="{home}">首页</a>
      <a class="{cls('browse')}" href="{browse}">公开售后</a>
      <a class="{cls('create')}" href="{create}">创作售后</a>
    </nav>"""


SITE_BASE_CSS = """
    .site-nav {
      display: flex; justify-content: center; flex-wrap: wrap; gap: 0.45rem;
      margin-top: 1.1rem;
    }
    .site-nav__link {
      display: inline-block;
      padding: 0.45rem 0.95rem;
      border: 1px solid rgba(239, 230, 214, 0.22);
      color: var(--fade);
      text-decoration: none;
      font-size: 0.76rem;
      letter-spacing: 0.18em;
      transition: border-color .25s, color .25s, background .25s;
    }
    .site-nav__link:hover {
      color: var(--paper);
      border-color: rgba(239, 230, 214, 0.5);
    }
    .site-nav__link.is-active {
      color: var(--paper);
      border-color: rgba(156, 47, 42, 0.65);
      background: rgba(156, 47, 42, 0.22);
    }
"""


def render_portal(entry_count: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>剧本杀售后</title>
  <meta name="description" content="浏览公开售后合集，或为玩家生成可分享的售后网页。" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --ink: #100e0c;
      --paper: #efe6d6;
      --paper-soft: #cfc3ae;
      --fade: rgba(239, 230, 214, 0.55);
      --seal: #9c2f2a;
      --line: rgba(239, 230, 214, 0.16);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Noto Serif SC", "Songti SC", serif;
      color: var(--paper);
      background: var(--ink);
      line-height: 1.55;
      min-height: 100vh;
    }}
    body::before {{
      content: "";
      position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background:
        radial-gradient(ellipse 80% 55% at 12% 8%, rgba(120, 48, 40, 0.22), transparent 55%),
        radial-gradient(ellipse 70% 50% at 88% 18%, rgba(70, 58, 40, 0.2), transparent 50%),
        linear-gradient(180deg, #0c0a09 0%, #14110e 45%, #0f0d0b 100%);
    }}
    .page {{ position: relative; z-index: 2; max-width: 920px; margin: 0 auto; padding: 1.6rem 1rem 3rem; }}
    .top {{ text-align: center; }}
    .top-brand {{
      font-family: "Ma Shan Zheng", cursive;
      font-size: clamp(2.4rem, 9vw, 3.6rem);
      letter-spacing: 0.2em; line-height: 1; margin-left: 0.2em;
    }}
    .top-line {{ width: 1.8rem; height: 1px; margin: 0.75rem auto 0.65rem; background: var(--seal); }}
    .top-lead {{ font-size: 0.88rem; letter-spacing: 0.18em; color: var(--paper-soft); }}
    {SITE_BASE_CSS}
    .features {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.85rem;
      margin-top: 2rem;
    }}
    .feature {{
      display: flex;
      flex-direction: column;
      text-decoration: none;
      color: inherit;
      border: 1px solid var(--line);
      background: rgba(28, 24, 20, 0.55);
      padding: 1.35rem 1.1rem 1.2rem;
      min-height: 220px;
      transition: border-color .25s, transform .25s, background .25s;
    }}
    .feature:hover {{
      border-color: rgba(239, 230, 214, 0.35);
      background: rgba(36, 30, 26, 0.72);
      transform: translateY(-2px);
    }}
    .feature-tag {{
      font-size: 0.68rem;
      letter-spacing: 0.24em;
      color: rgba(156, 47, 42, 0.9);
      margin-bottom: 0.65rem;
    }}
    .feature h2 {{
      font-family: "Ma Shan Zheng", cursive;
      font-size: clamp(1.6rem, 5vw, 2rem);
      letter-spacing: 0.14em;
      margin-bottom: 0.55rem;
      margin-left: 0.08em;
    }}
    .feature p {{
      color: var(--paper-soft);
      font-size: 0.86rem;
      letter-spacing: 0.06em;
      line-height: 1.7;
      flex: 1;
    }}
    .feature-cta {{
      margin-top: 1rem;
      font-size: 0.78rem;
      letter-spacing: 0.2em;
      color: var(--fade);
    }}
    .feature:hover .feature-cta {{ color: var(--paper); }}
    footer {{
      text-align: center; margin-top: 2rem;
      color: rgba(239, 230, 214, 0.35); font-size: 0.72rem; letter-spacing: 0.2em;
    }}
    @media (max-width: 640px) {{
      .features {{ grid-template-columns: 1fr; }}
      .feature {{ min-height: 0; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="top">
      <h1 class="top-brand">售后</h1>
      <div class="top-line" aria-hidden="true"></div>
      <p class="top-lead">局终之后，信仍未完</p>
      {site_nav("home")}
    </header>

    <main class="features">
      <a class="feature" href="browse/">
        <p class="feature-tag">功能一</p>
        <h2>公开售后</h2>
        <p>浏览目前已公开的 {entry_count} 封售后信。按剧本与角色整理，点击进入沉浸式阅读。玩家公开投稿也会显示在此。</p>
        <span class="feature-cta">进入合集 →</span>
      </a>
      <a class="feature" href="create/">
        <p class="feature-tag">功能二</p>
        <h2>创作售后</h2>
        <p>上传文字与配图，一键生成你的售后网页，并分享至微信、抖音、小红书。</p>
        <span class="feature-cta">开始创作 →</span>
      </a>
    </main>

    <footer>剧本杀售后</footer>
  </div>
</body>
</html>
"""


def filter_options(values: list[str]) -> str:
    opts = ['<option value="">全部</option>']
    for v in sorted(set(values), key=lambda x: x):
        opts.append(f'<option value="{html.escape(v, quote=True)}">{html.escape(v)}</option>')
    return "\n          ".join(opts)


def render_hub(entries: list[dict]) -> str:
    cards = []
    scripts, authors, targets = [], [], []
    for e in entries:
        scripts.append(e["script"])
        authors.append(e["me"])
        targets.append(e["target"])
        href = "../" + html.escape(href_for(e), quote=True)
        cover = e["cover"]
        if cover and not str(cover).startswith("http"):
            cover = "../" + str(cover).lstrip("/")
        visual = (
            f'<div class="entry-visual"><img src="{html.escape(cover)}" alt="" loading="lazy" /></div>'
            if cover
            else '<div class="entry-visual entry-visual--plain"><span>信</span></div>'
        )
        seal = html.escape(e["script"][:2])
        blurb = e["blurb"]
        if len(blurb) > 28:
            blurb = blurb[:28] + "…"
        cards.append(f"""
        <a class="entry" href="{href}" data-script="{html.escape(e['script'])}" data-me="{html.escape(e['me'])}" data-target="{html.escape(e['target'])}">
          {visual}
          <div class="entry-body">
            <p class="entry-script">{html.escape(e['script'])} · {html.escape(e['me'])}</p>
            <h3 class="entry-name">{html.escape(e['title'])}</h3>
            <p class="entry-blurb">{html.escape(blurb)}</p>
          </div>
          <div class="entry-seal" aria-hidden="true">{seal}</div>
        </a>""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>公开售后 · 剧本杀售后</title>
  <meta name="description" content="浏览目前已公开的剧本杀售后信合集。" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --ink: #100e0c;
      --paper: #efe6d6;
      --paper-soft: #cfc3ae;
      --fade: rgba(239, 230, 214, 0.55);
      --seal: #9c2f2a;
      --seal-soft: rgba(156, 47, 42, 0.55);
      --line: rgba(239, 230, 214, 0.16);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Noto Serif SC", "Songti SC", serif;
      color: var(--paper);
      background: var(--ink);
      line-height: 1.55;
      overflow-x: hidden;
    }}
    body::before {{
      content: "";
      position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background:
        radial-gradient(ellipse 80% 55% at 12% 8%, rgba(120, 48, 40, 0.22), transparent 55%),
        radial-gradient(ellipse 70% 50% at 88% 18%, rgba(70, 58, 40, 0.2), transparent 50%),
        radial-gradient(ellipse 90% 55% at 50% 100%, rgba(40, 34, 28, 0.55), transparent 60%),
        linear-gradient(180deg, #0c0a09 0%, #14110e 45%, #0f0d0b 100%);
    }}
    body::after {{
      content: "";
      position: fixed; inset: 0; z-index: 1; pointer-events: none; opacity: 0.055;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    }}
    .page {{ position: relative; z-index: 2; }}
    .top {{
      text-align: center;
      padding: 1.6rem 1rem 1rem;
    }}
    .top-brand {{
      font-family: "Ma Shan Zheng", cursive;
      font-size: clamp(2.2rem, 8vw, 3.2rem);
      letter-spacing: 0.2em; line-height: 1; margin-left: 0.2em;
    }}
    .top-line {{
      width: 1.8rem; height: 1px; margin: 0.75rem auto 0.65rem; background: var(--seal);
    }}
    .top-lead {{
      font-size: 0.85rem; letter-spacing: 0.2em; color: var(--paper-soft);
    }}
    .top-count {{
      margin-top: 0.35rem; font-size: 0.72rem; letter-spacing: 0.24em; color: var(--fade);
    }}
    {SITE_BASE_CSS}
    .filters {{
      max-width: 1100px;
      margin: 0 auto 0.75rem;
      padding: 0 1rem;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
      gap: 0.5rem;
      align-items: end;
    }}
    .filter label {{
      display: block;
      font-size: 0.68rem;
      letter-spacing: 0.16em;
      color: var(--fade);
      margin-bottom: 0.3rem;
    }}
    .filter select {{
      width: 100%;
      background: rgba(28, 24, 20, 0.72);
      border: 1px solid var(--line);
      color: var(--paper);
      padding: 0.5rem 0.55rem;
      font-family: inherit;
      font-size: 0.82rem;
      border-radius: 2px;
      appearance: none;
      background-image: linear-gradient(45deg, transparent 50%, var(--fade) 50%), linear-gradient(135deg, var(--fade) 50%, transparent 50%);
      background-position: calc(100% - 14px) 52%, calc(100% - 9px) 52%;
      background-size: 5px 5px, 5px 5px;
      background-repeat: no-repeat;
    }}
    .filter select:focus {{ outline: none; border-color: rgba(239, 230, 214, 0.45); }}
    .filter-reset {{
      border: 1px solid rgba(239, 230, 214, 0.22);
      background: transparent;
      color: var(--fade);
      padding: 0.5rem 0.75rem;
      font-family: inherit;
      font-size: 0.76rem;
      letter-spacing: 0.14em;
      cursor: pointer;
      white-space: nowrap;
    }}
    .filter-reset:hover {{ color: var(--paper); border-color: rgba(239, 230, 214, 0.5); }}
    .filter-empty {{
      display: none;
      grid-column: 1 / -1;
      text-align: center;
      padding: 2.5rem 1rem;
      color: var(--fade);
      letter-spacing: 0.12em;
      font-size: 0.88rem;
    }}
    .filter-empty.visible {{ display: block; }}
    .entry.is-hidden {{ display: none !important; }}
    .entry-user .entry-seal {{ border-color: rgba(239, 230, 214, 0.35); color: var(--paper-soft); }}
    .entry-badge {{
      position: absolute; left: 0.55rem; top: 0.55rem; z-index: 2;
      font-size: 0.62rem; letter-spacing: 0.12em; padding: 0.2rem 0.4rem;
      border: 1px solid rgba(239, 230, 214, 0.28); color: var(--fade);
      background: rgba(16, 14, 12, 0.65); pointer-events: none;
    }}
    .collection {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 0.2rem 1rem 3rem;
    }}
    .entries {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0.75rem;
    }}
    .entry {{
      position: relative;
      display: flex;
      flex-direction: column;
      text-decoration: none;
      color: inherit;
      overflow: hidden;
      border: 1px solid var(--line);
      background: rgba(28, 24, 20, 0.55);
      transition: border-color 0.25s ease, background 0.25s ease, transform 0.25s ease;
    }}
    .entry:hover {{
      border-color: rgba(239, 230, 214, 0.4);
      background: rgba(36, 30, 24, 0.78);
      transform: translateY(-2px);
    }}
    .entry-visual {{
      position: relative;
      aspect-ratio: 16 / 10;
      overflow: hidden;
      background: #1a1612;
    }}
    .entry-visual img {{
      width: 100%; height: 100%; object-fit: cover; display: block;
      transition: transform 0.8s ease; filter: saturate(0.88) contrast(1.04);
    }}
    .entry:hover .entry-visual img {{ transform: scale(1.06); }}
    .entry-visual--plain {{
      display: grid; place-items: center;
      font-family: "Ma Shan Zheng", cursive; font-size: 1.8rem; color: rgba(239,230,214,.28);
      letter-spacing: 0.18em;
    }}
    .entry-body {{
      display: flex; flex-direction: column; gap: 0.2rem;
      padding: 0.7rem 0.75rem 0.85rem;
    }}
    .entry-script {{
      font-size: 0.68rem; letter-spacing: 0.12em; color: var(--seal);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .entry-name {{
      font-family: "Ma Shan Zheng", cursive;
      font-size: clamp(1.25rem, 2.4vw, 1.55rem);
      letter-spacing: 0.1em; margin-left: 0.06em; line-height: 1.2;
    }}
    .entry-blurb {{
      color: var(--paper-soft); font-size: 0.78rem; letter-spacing: 0.02em;
      display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .entry-seal {{
      position: absolute; top: 0.55rem; right: 0.55rem; width: 1.9rem; height: 1.9rem;
      border: 1px solid var(--seal-soft); color: var(--seal);
      display: grid; place-items: center; font-family: "Ma Shan Zheng", cursive;
      font-size: 0.78rem; transform: rotate(12deg); opacity: 0.75; pointer-events: none;
      background: rgba(16,14,12,.35);
    }}
    footer {{
      text-align: center; padding: 0 1rem 2rem;
      color: rgba(239, 230, 214, 0.35); font-size: 0.72rem; letter-spacing: 0.2em;
    }}
    @media (max-width: 900px) {{
      .entries {{ grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem; }}
      .filters {{ grid-template-columns: 1fr 1fr; }}
      .filter-reset {{ grid-column: 1 / -1; }}
    }}
    @media (max-width: 520px) {{
      .entries {{ grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.5rem; }}
      .entry-body {{ padding: 0.55rem 0.55rem 0.7rem; }}
      .entry-blurb {{ -webkit-line-clamp: 1; }}
      .top {{ padding: 1.2rem 0.8rem 0.7rem; }}
      .collection {{ padding: 0.1rem 0.7rem 2.2rem; }}
      .filters {{ grid-template-columns: 1fr; padding: 0 0.7rem; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="top">
      <h1 class="top-brand">售后</h1>
      <div class="top-line" aria-hidden="true"></div>
      <p class="top-lead">公开售后合集</p>
      <p class="top-count" id="resultCount">共 {len(entries)} 封</p>
      {site_nav("browse", "../")}
    </header>

    <form class="filters" id="filters" aria-label="筛选售后">
      <div class="filter">
        <label for="filterScript">剧本</label>
        <select id="filterScript" name="script">
          {filter_options(scripts)}
        </select>
      </div>
      <div class="filter">
        <label for="filterMe">谁写的</label>
        <select id="filterMe" name="me">
          {filter_options(authors)}
        </select>
      </div>
      <div class="filter">
        <label for="filterTarget">送给谁</label>
        <select id="filterTarget" name="target">
          {filter_options(targets)}
        </select>
      </div>
      <button class="filter-reset" type="button" id="filterReset">重置</button>
    </form>

    <main class="collection" id="collection">
      <div class="entries" id="entries">
        {''.join(cards)}
      </div>
      <p class="filter-empty" id="filterEmpty">没有符合筛选条件的售后</p>
    </main>

    <footer>剧本杀售后合集</footer>
  </div>
  <script>
    (function () {{
      const builtinTotal = {len(entries)};
      let entries = Array.from(document.querySelectorAll(".entry"));
      const scriptEl = document.getElementById("filterScript");
      const meEl = document.getElementById("filterMe");
      const targetEl = document.getElementById("filterTarget");
      const resetEl = document.getElementById("filterReset");
      const countEl = document.getElementById("resultCount");
      const emptyEl = document.getElementById("filterEmpty");
      const entriesEl = document.getElementById("entries");

      function readParams() {{
        const p = new URLSearchParams(location.search);
        return {{
          script: p.get("script") || "",
          me: p.get("me") || "",
          target: p.get("target") || "",
        }};
      }}

      function writeParams(script, me, target) {{
        const p = new URLSearchParams();
        if (script) p.set("script", script);
        if (me) p.set("me", me);
        if (target) p.set("target", target);
        const qs = p.toString();
        history.replaceState(null, "", qs ? ("?" + qs) : location.pathname);
      }}

      function ensureOption(select, value) {{
        if (!value) return;
        for (const opt of select.options) {{
          if (opt.value === value) return;
        }}
        const opt = document.createElement("option");
        opt.value = value;
        opt.textContent = value;
        select.appendChild(opt);
        const options = Array.from(select.options).slice(1);
        options.sort((a, b) => a.value.localeCompare(b.value, "zh-CN"));
        select.innerHTML = '<option value="">全部</option>';
        options.forEach((o) => select.appendChild(o));
      }}

      function esc(s) {{
        return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
      }}

      function createUserCard(item) {{
        const script = item.script || "玩家创作";
        const me = item.me || "";
        const target = item.target || "";
        const seal = esc(script.slice(0, 2) || "信");
        const visual = item.hasImage
          ? `<div class="entry-visual"><img src="../api/img/${{esc(item.id)}}" alt="" loading="lazy" /></div>`
          : '<div class="entry-visual entry-visual--plain"><span>信</span></div>';
        const card = document.createElement("a");
        card.className = "entry entry-user";
        card.href = `../p/${{esc(item.id)}}`;
        card.dataset.script = script;
        card.dataset.me = me;
        card.dataset.target = target;
        card.innerHTML = `
          <span class="entry-badge">玩家</span>
          ${{visual}}
          <div class="entry-body">
            <p class="entry-script">${{esc(script)}}${{me ? ` · ${{esc(me)}}` : ""}}</p>
            <h3 class="entry-name">${{esc(item.title)}}</h3>
            <p class="entry-blurb">${{esc(item.blurb || "")}}</p>
          </div>
          <div class="entry-seal" aria-hidden="true">${{seal}}</div>`;
        return card;
      }}

      function applyFilters() {{
        const script = scriptEl.value;
        const me = meEl.value;
        const target = targetEl.value;
        let visible = 0;
        entries.forEach((el) => {{
          const ok =
            (!script || el.dataset.script === script) &&
            (!me || el.dataset.me === me) &&
            (!target || el.dataset.target === target);
          el.classList.toggle("is-hidden", !ok);
          if (ok) visible++;
        }});
        const total = entries.length;
        countEl.textContent = visible === total
          ? `共 ${{total}} 封`
          : `显示 ${{visible}} / ${{total}} 封`;
        emptyEl.classList.toggle("visible", visible === 0);
        writeParams(script, me, target);
      }}

      function setSelect(el, value) {{
        if (!value) return;
        ensureOption(el, value);
        el.value = value;
      }}

      async function loadPublicEntries() {{
        try {{
          const res = await fetch("/api/public");
          if (!res.ok) return;
          const items = await res.json();
          for (const item of items) {{
            ensureOption(scriptEl, item.script || "玩家创作");
            ensureOption(meEl, item.me);
            ensureOption(targetEl, item.target);
            const card = createUserCard(item);
            entriesEl.appendChild(card);
            entries.push(card);
          }}
        }} catch {{
          /* ignore */
        }}
        applyFilters();
      }}

      const initial = readParams();
      setSelect(scriptEl, initial.script);
      setSelect(meEl, initial.me);
      setSelect(targetEl, initial.target);

      scriptEl.addEventListener("change", applyFilters);
      meEl.addEventListener("change", applyFilters);
      targetEl.addEventListener("change", applyFilters);
      resetEl.addEventListener("click", () => {{
        scriptEl.value = "";
        meEl.value = "";
        targetEl.value = "";
        applyFilters();
      }});

      applyFilters();
      loadPublicEntries();
    }})();
  </script>
</body>
</html>
"""


def main() -> None:
    entries = collect_entries()
    # clean old generated pages
    pages = ROOT / "pages"
    if pages.exists():
        for p in sorted(pages.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                try:
                    p.rmdir()
                except OSError:
                    pass

    for e in entries:
        write_letter_page(e)

    hub = render_hub(entries)
    browse_dir = ROOT / "browse"
    browse_dir.mkdir(exist_ok=True)
    (browse_dir / "index.html").write_text(hub, encoding="utf-8")

    portal = render_portal(len(entries))
    (ROOT / "index.html").write_text(portal, encoding="utf-8")

    slim = [
        {
            "script": e["script"],
            "me": e["me"],
            "target": e["target"],
            "title": e["title"],
            "href": href_for(e),
        }
        for e in entries
    ]
    (ROOT / "catalog.json").write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built {len(entries)} entries")
    for e in slim:
        print(f"  - {e['script']} / {e['me']} / {e['target']} -> {e['href'][:80]}")


if __name__ == "__main__":
    main()
