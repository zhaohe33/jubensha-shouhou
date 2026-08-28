function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

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
  const ogImage = data.img ? `${origin}/api/img/${params.id}` : `${origin}/media/duos/qingbai-suwuyang-axi.jpg`;
  const pageUrl = `${origin}/p/${params.id}`;

  const imgBlock = data.img
    ? `      <div class="media"><img src="/api/img/${esc(params.id)}" alt="${esc(title)}" /></div>\n`
    : "";

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
  <link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root { --ink:#100e0c; --paper:#efe6d6; --paper-soft:#cfc3ae; --fade:rgba(239,230,214,.55); --seal:#9c2f2a; --line:rgba(239,230,214,.16); }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { font-family:"Noto Serif SC","Songti SC",serif; color:var(--paper); background:var(--ink); line-height:1.95; min-height:100vh; }
    body::before { content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
      background: radial-gradient(ellipse 80% 55% at 12% 8%, rgba(120,48,40,.18), transparent 55%),
        linear-gradient(180deg,#0c0a09 0%,#14110e 50%,#0f0d0b 100%); }
    .wrap { position:relative; z-index:2; max-width:720px; margin:0 auto; padding:2.5rem 1.35rem 4rem; }
    .back { display:inline-flex; color:var(--fade); text-decoration:none; font-size:.82rem; letter-spacing:.22em; margin-bottom:2.2rem; }
    .back:hover { color:var(--paper); }
    .meta { font-size:.78rem; letter-spacing:.28em; color:rgba(156,47,42,.85); margin-bottom:.85rem; }
    h1 { font-family:"Ma Shan Zheng",cursive; font-size:clamp(2.4rem,8vw,3.4rem); letter-spacing:.16em; line-height:1.15; margin-bottom:.4rem; }
    .sub { color:var(--paper-soft); letter-spacing:.12em; font-size:.95rem; margin-bottom:2rem; }
    .line { width:2.2rem; height:1px; background:var(--seal); margin:0 0 2rem; }
    .prose p { margin-bottom:1.15rem; letter-spacing:.04em; }
    .media { margin:1.6rem 0 0; }
    .media img { width:100%; display:block; border:1px solid var(--line); }
    .cta { margin-top:2.5rem; padding-top:1.5rem; border-top:1px solid var(--line); }
    .cta a { display:inline-block; margin-right:.75rem; margin-bottom:.5rem; padding:.65rem 1rem; border:1px solid rgba(239,230,214,.35); color:var(--paper); text-decoration:none; font-size:.82rem; letter-spacing:.18em; }
    .cta a:hover { border-color:rgba(239,230,214,.7); }
  </style>
</head>
<body>
  <div class="wrap">
    <a class="back" href="/">← 返回首页</a>
    ${meta ? `<p class="meta">${esc(meta)}</p>` : ""}
    <h1>${esc(title)}</h1>
    ${me && target ? `<p class="sub">${esc(me)} → ${esc(target)}</p>` : ""}
    <div class="line" aria-hidden="true"></div>
    <article class="prose">
${paragraphs(data.c) || "        <p class=\"empty\">（暂无文字）</p>"}
    </article>
${imgBlock}    <div class="cta">
      <a href="/browse/">浏览公开售后</a>
      <a href="/create/">我也要写一封</a>
    </div>
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
