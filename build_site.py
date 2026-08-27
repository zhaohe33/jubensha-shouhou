# -*- coding: utf-8 -*-
"""Scan 剧本/我的角色/售后角色 and generate hub + letter pages."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {".git", ".git.bak-hub", "__pycache__", "pages"}

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

    external = read_url_file(url_files[0]) if url_files else None
    existing_page = rel_posix(html_files[0]) if html_files else None

    text_body = ""
    text_path = None
    # Prefer named letter files
    preferred = None
    for p in txt_files:
        if "给" in p.stem or p.stem == "文字" or p.stem == target:
            preferred = p
            break
    if not preferred and txt_files:
        preferred = txt_files[0]
    if preferred:
        text_path = preferred
        text_body = preferred.read_text(encoding="utf-8")

    title = f"致{target}" if target != "售后" else f"{me} · 售后"
    blurb = first_line_blurb(text_body, f"{me} → {target}") if text_body.strip() else (
        "视频售后" if videos else ("图文售后" if images else ("附件售后" if pdfs else "售后"))
    )

    slug = f"{script}/{me}/{target}"
    view_rel = f"pages/{script}/{me}/{target}/index.html"

    return {
        "script": script,
        "me": me,
        "target": target,
        "title": title,
        "blurb": blurb,
        "cover": cover,
        "external": external,
        "existing_page": existing_page,
        "view_rel": view_rel,
        "text": text_body,
        "videos": [rel_posix(p) for p in videos],
        "images": [rel_posix(p) for p in images if "images" not in rel_posix(p) or True],
        "images_only": [rel_posix(p) for p in images],
        "pdfs": [rel_posix(p) for p in pdfs],
        "folder": rel_posix(folder) if folder.is_dir() else rel_posix(folder.parent),
    }


def href_for(entry: dict) -> str:
    if entry["external"]:
        return entry["external"]
    if entry["existing_page"]:
        return entry["existing_page"]
    return entry["view_rel"]


def depth_prefix(rel_path: str) -> str:
    return "../" * (len(Path(rel_path).parts))


def write_letter_page(entry: dict) -> None:
    if entry["external"] or entry["existing_page"]:
        return

    out = ROOT / entry["view_rel"]
    out.parent.mkdir(parents=True, exist_ok=True)
    prefix = depth_prefix(entry["view_rel"])

    paras = text_to_paragraphs(entry["text"])
    prose = "\n".join(f"        <p>{p}</p>" for p in paras) if paras else '        <p class="empty">（暂无文字）</p>'

    media_blocks = []
    for v in entry["videos"]:
        media_blocks.append(
            f'        <video controls playsinline src="{html.escape(prefix + v)}"></video>'
        )
    for img in entry["images_only"]:
        # skip if it's under a generated path weirdness; show leaf images
        media_blocks.append(
            f'        <img src="{html.escape(prefix + img)}" alt="{html.escape(entry["title"])}" />'
        )
    for pdf in entry["pdfs"]:
        media_blocks.append(
            f'        <a class="pdf" href="{html.escape(prefix + pdf)}" target="_blank" rel="noopener">打开附件 PDF</a>'
        )
    media_html = ""
    if media_blocks:
        media_html = '      <div class="media">\n' + "\n".join(media_blocks) + "\n      </div>"

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(entry['title'])} · {html.escape(entry['script'])}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>{LETTER_CSS}</style>
</head>
<body>
  <div class="wrap">
    <a class="back" href="{prefix}index.html">← 返回合集</a>
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


def render_hub(entries: list[dict]) -> str:
    # group by script, preserve discovery order by script name
    scripts: dict[str, list[dict]] = {}
    for e in entries:
        scripts.setdefault(e["script"], []).append(e)

    sections = []
    for script, items in scripts.items():
        cards = []
        for e in items:
            href = html.escape(href_for(e), quote=True)
            cover = e["cover"]
            visual = (
                f'<div class="entry-visual"><img src="{html.escape(cover)}" alt="" /></div>'
                if cover
                else '<div class="entry-visual entry-visual--plain"><span>信</span></div>'
            )
            ext_note = ' target="_blank" rel="noopener"' if e["external"] else ""
            cards.append(f"""
        <a class="entry reveal" href="{href}"{ext_note}>
          {visual}
          <div class="entry-body">
            <p class="entry-script">我方 · {html.escape(e['me'])}</p>
            <h3 class="entry-name">{html.escape(e['title'])}</h3>
            <p class="entry-blurb">{html.escape(e['blurb'])}</p>
            <p class="entry-go">阅读售后 <span aria-hidden="true">→</span></p>
          </div>
          <div class="entry-seal" aria-hidden="true">{html.escape(script[:2])}</div>
        </a>""")
        sections.append(f"""
      <section class="script-block reveal">
        <div class="script-head">
          <p class="section-kicker">SCRIPT</p>
          <h2 class="section-title">{html.escape(script)}</h2>
          <p class="section-desc">{len(items)} 封售后</p>
        </div>
        <div class="entries">
          {''.join(cards)}
        </div>
      </section>""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>剧本杀售后</title>
  <meta name="description" content="所有剧本杀售后，写在这里。" />
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
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: "Noto Serif SC", "Songti SC", serif;
      color: var(--paper);
      background: var(--ink);
      line-height: 1.8;
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
    .hero {{
      min-height: 100vh; min-height: 100dvh;
      display: grid; place-items: center; text-align: center;
      padding: 4rem 1.4rem 3rem; position: relative;
    }}
    .hero-brand {{
      font-family: "Ma Shan Zheng", cursive;
      font-size: clamp(3.6rem, 14vw, 6.2rem);
      letter-spacing: 0.22em; line-height: 1; margin-left: 0.22em;
      opacity: 0; animation: rise 1.3s ease 0.15s forwards;
    }}
    .hero-line {{
      width: 2.4rem; height: 1px; margin: 1.7rem auto 1.5rem; background: var(--seal);
      opacity: 0; animation: fadeIn 1s ease 0.65s forwards;
    }}
    .hero-lead {{
      font-size: clamp(1rem, 2.8vw, 1.15rem);
      letter-spacing: 0.28em; color: var(--paper-soft);
      opacity: 0; animation: rise 1.2s ease 0.85s forwards;
    }}
    .hero-cta {{
      margin-top: 2.4rem; display: inline-flex; align-items: center; gap: 0.7rem;
      padding: 0.85rem 1.45rem; border: 1px solid rgba(239, 230, 214, 0.35);
      background: rgba(239, 230, 214, 0.04); color: var(--paper);
      text-decoration: none; font-size: 0.92rem; letter-spacing: 0.32em;
      transition: border-color 0.3s ease, background 0.3s ease, transform 0.3s ease;
      opacity: 0; animation: rise 1.1s ease 1.2s forwards;
    }}
    .hero-cta:hover {{
      border-color: rgba(239, 230, 214, 0.7);
      background: rgba(239, 230, 214, 0.09);
      transform: translateY(-2px);
    }}
    .scroll-hint {{
      position: absolute; bottom: 1.8rem; left: 50%; transform: translateX(-50%);
      font-size: 0.78rem; letter-spacing: 0.35em; color: var(--fade);
      opacity: 0; animation: pulseHint 2.4s ease 2s infinite;
    }}
    .collection {{ max-width: 920px; margin: 0 auto; padding: 1rem 1.4rem 5.5rem; }}
    .script-block {{ margin-bottom: 3.4rem; }}
    .script-head {{ text-align: center; margin-bottom: 1.6rem; }}
    .section-kicker {{
      font-size: 0.78rem; letter-spacing: 0.42em; color: var(--seal-soft); margin-bottom: 0.55rem;
    }}
    .section-title {{
      font-family: "Ma Shan Zheng", cursive;
      font-size: clamp(1.9rem, 5.5vw, 2.6rem);
      letter-spacing: 0.18em; margin-left: 0.18em;
    }}
    .section-desc {{ margin-top: 0.55rem; color: var(--fade); letter-spacing: 0.12em; font-size: 0.9rem; }}
    .entries {{ display: flex; flex-direction: column; gap: 1.1rem; }}
    .entry {{
      position: relative; display: grid;
      grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.3fr);
      min-height: 188px; text-decoration: none; color: inherit; overflow: hidden;
      border: 1px solid var(--line); background: rgba(28, 24, 20, 0.55);
      opacity: 0; transform: translateY(22px);
      transition: opacity 0.9s ease, transform 0.9s ease, border-color 0.35s ease, background 0.35s ease;
    }}
    .entry.is-in, .script-block.is-in .entry {{ opacity: 1; transform: none; }}
    .script-block.reveal {{ opacity: 0; transform: translateY(18px); transition: opacity .9s ease, transform .9s ease; }}
    .script-block.is-in {{ opacity: 1; transform: none; }}
    .entry:hover {{ border-color: rgba(239, 230, 214, 0.38); background: rgba(36, 30, 24, 0.72); }}
    .entry-visual {{ position: relative; min-height: 170px; overflow: hidden; background: #1a1612; }}
    .entry-visual img {{
      width: 100%; height: 100%; object-fit: cover; display: block;
      transform: scale(1.04); transition: transform 1.1s ease; filter: saturate(0.85) contrast(1.05);
    }}
    .entry:hover .entry-visual img {{ transform: scale(1.1); }}
    .entry-visual--plain {{
      display: grid; place-items: center;
      font-family: "Ma Shan Zheng", cursive; font-size: 2.4rem; color: rgba(239,230,214,.28);
      letter-spacing: 0.2em;
    }}
    .entry-body {{
      display: flex; flex-direction: column; justify-content: center;
      padding: 1.35rem 1.4rem 1.35rem 1.25rem; gap: 0.4rem;
    }}
    .entry-script {{ font-size: 0.74rem; letter-spacing: 0.28em; color: var(--seal); }}
    .entry-name {{
      font-family: "Ma Shan Zheng", cursive;
      font-size: clamp(1.7rem, 4.2vw, 2.2rem);
      letter-spacing: 0.14em; margin-left: 0.1em; line-height: 1.15;
    }}
    .entry-blurb {{ color: var(--paper-soft); font-size: 0.92rem; letter-spacing: 0.05em; }}
    .entry-go {{
      margin-top: 0.65rem; display: inline-flex; align-items: center; gap: 0.45rem;
      font-size: 0.8rem; letter-spacing: 0.28em; color: var(--fade);
      transition: color 0.3s ease, gap 0.3s ease;
    }}
    .entry:hover .entry-go {{ color: var(--paper); gap: 0.7rem; }}
    .entry-seal {{
      position: absolute; top: 0.9rem; right: 0.9rem; width: 2.6rem; height: 2.6rem;
      border: 1.5px solid var(--seal-soft); color: var(--seal);
      display: grid; place-items: center; font-family: "Ma Shan Zheng", cursive;
      font-size: 0.95rem; transform: rotate(12deg); opacity: 0.7; pointer-events: none;
    }}
    footer {{
      text-align: center; padding: 0 1.4rem 3.2rem;
      color: rgba(239, 230, 214, 0.35); font-size: 0.78rem; letter-spacing: 0.22em;
    }}
    @keyframes rise {{
      from {{ opacity: 0; transform: translateY(22px); }}
      to {{ opacity: 1; transform: none; }}
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @keyframes pulseHint {{
      0%, 100% {{ opacity: 0.22; transform: translateX(-50%) translateY(0); }}
      50% {{ opacity: 0.55; transform: translateX(-50%) translateY(5px); }}
    }}
    @media (max-width: 720px) {{
      .entry {{ grid-template-columns: 1fr; min-height: 0; }}
      .entry-visual {{ min-height: 150px; }}
      .entry-body {{ padding: 1.15rem 1.15rem 1.35rem; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="hero">
      <div class="hero-inner">
        <h1 class="hero-brand">售后</h1>
        <div class="hero-line" aria-hidden="true"></div>
        <p class="hero-lead">局终之后，信仍未完</p>
        <a class="hero-cta" href="#collection">进入合集 <span aria-hidden="true">↓</span></a>
      </div>
      <p class="scroll-hint">下滑浏览</p>
    </header>

    <main class="collection" id="collection">
      {''.join(sections)}
    </main>

    <footer>剧本杀售后合集 · 共 {len(entries)} 封</footer>
  </div>
  <script>
    const reveals = document.querySelectorAll(".reveal");
    const io = new IntersectionObserver((entries) => {{
      entries.forEach((entry) => {{
        if (entry.isIntersecting) {{
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        }}
      }});
    }}, {{ threshold: 0.12, rootMargin: "0px 0px -6% 0px" }});
    reveals.forEach((el, i) => {{
      el.style.transitionDelay = `${{Math.min(i * 0.06, 0.3)}}s`;
      io.observe(el);
    }});
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
    (ROOT / "index.html").write_text(hub, encoding="utf-8")

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
