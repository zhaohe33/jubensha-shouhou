import { normalizeTheme, themeCss, themeFontLink } from "../_lib/theme.js";

function paragraphs(text) {
  return String(text || "")
    .replace(/\r\n/g, "\n")
    .trim()
    .split(/\n\s*\n/)
    .map((p) => {
      const lines = p
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .map((l) => esc(l))
        .join("<br />\n");
      return `        <p>${lines}</p>`;
    })
    .join("\n");
}

function getImages(data) {
  if (Array.isArray(data.imgs)) {
    return data.imgs.filter((img) => typeof img === "string" && img.startsWith("data:image/"));
  }
  if (data.img && data.img.startsWith("data:image/")) return [data.img];
  return [];
}

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export async function onRequestGet(context) {
  const { env, params, request } = context;
  const raw = await env.SHARES.get(params.id);
  if (!raw) {
    return new Response("链接不存在或已过期", {
      status: 404,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return new Response("数据损坏", { status: 500 });
  }

  const origin = new URL(request.url).origin;
  const title = data.t || "剧本杀售后";
  const script = data.s || "";
  const me = data.m || "";
  const target = data.r || "";
  const meta = [script, me].filter(Boolean).join(" · ");
  const desc = (data.c || "").replace(/\s+/g, " ").trim().slice(0, 120);
  const images = getImages(data);
  const ogImage = images.length
    ? `${origin}/api/img/${params.id}`
    : `${origin}/media/duos/qingbai-suwuyang-axi.jpg`;
  const pageUrl = `${origin}/p/${params.id}`;

  const sideImgs = images
    .map(
      (_, i) =>
        `          <img src="/api/img/${esc(params.id)}?i=${i}" alt="${esc(title)}" loading="lazy" />`,
    )
    .join("\n");

  const sideBlock = images.length
    ? `      <aside class="letter-side" aria-label="配图">
${sideImgs}
      </aside>\n`
    : "";

  const theme = normalizeTheme(data.th);
  const fontHref = themeFontLink(theme);
  const themeStyles = themeCss(theme);

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${esc(title)}${script ? ` · ${esc(script)}` : ""}</title>
  <meta name="description" content="${esc(desc)}" />
  <meta property="og:type" content="article" />
  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(desc)}" />
  <meta property="og:image" content="${esc(ogImage)}" />
  <meta property="og:url" content="${esc(pageUrl)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${esc(title)}" />
  <meta name="twitter:description" content="${esc(desc)}" />
  <meta name="twitter:image" content="${esc(ogImage)}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="${esc(fontHref)}" rel="stylesheet" />
  <style>
    * { box-sizing:border-box; margin:0; padding:0; }
    body { line-height:1.95; min-height:100vh; }
    body::before { content:""; position:fixed; inset:0; z-index:0; pointer-events:none; }
    ${themeStyles}
    .wrap { position:relative; z-index:2; max-width:960px; margin:0 auto; padding:2.5rem 1.35rem 4rem; }
    .letter-layout { display:grid; grid-template-columns:minmax(0,1fr) min(300px,36%); gap:1.5rem; align-items:start; }
    .letter-main { min-width:0; }
    .letter-side { display:flex; flex-direction:column; gap:.75rem; position:sticky; top:1.25rem; }
    .letter-side img { width:100%; display:block; border:1px solid var(--line); object-fit:cover; }
    .back { display:inline-flex; text-decoration:none; font-size:.82rem; letter-spacing:.22em; margin-bottom:2.2rem; }
    .meta { font-size:.78rem; letter-spacing:.28em; margin-bottom:.85rem; }
    h1 { font-size:clamp(2.4rem,8vw,3.4rem); letter-spacing:.16em; line-height:1.15; margin-bottom:.4rem; }
    .sub { color:var(--paper-soft); letter-spacing:.12em; font-size:.95rem; margin-bottom:2rem; }
    .line { width:2.2rem; height:1px; margin:0 0 2rem; }
    .prose p { margin-bottom:1.15rem; letter-spacing:.04em; }
    .cta { margin-top:2.5rem; padding-top:1.5rem; border-top:1px solid var(--line); }
    .cta a { display:inline-block; margin-right:.75rem; margin-bottom:.5rem; padding:.65rem 1rem; text-decoration:none; font-size:.82rem; letter-spacing:.18em; }
    @media (max-width:760px) {
      .letter-layout { grid-template-columns:1fr; }
      .letter-side { position:static; flex-direction:row; overflow-x:auto; gap:.55rem; padding-bottom:.25rem; }
      .letter-side img { width:42vw; max-width:200px; flex:0 0 auto; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <a class="back" href="/">← 返回首页</a>
    ${meta ? `<p class="meta">${esc(meta)}</p>` : ""}
    <h1>${esc(title)}</h1>
    ${me && target ? `<p class="sub">${esc(me)} → ${esc(target)}</p>` : ""}
    <div class="line" aria-hidden="true"></div>
    <div class="letter-layout">
      <div class="letter-main">
        <article class="prose">
${paragraphs(data.c) || "        <p class=\"empty\">（暂无文字）</p>"}
        </article>
        <div class="cta">
          <a href="/browse/">浏览公开售后</a>
          <a href="/create/">我也要写一封</a>
        </div>
      </div>
${sideBlock}    </div>
  </div>
</body>
</html>`;

  return new Response(html, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "public, max-age=60",
    },
  });
}
