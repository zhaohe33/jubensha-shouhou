import { normalizeTheme } from "../_lib/theme.js";

const ID_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789";
const MAX_BODY = 900_000;
const MAX_IMAGES = 8;

function newId() {
  let id = "";
  const bytes = crypto.getRandomValues(new Uint8Array(8));
  for (let i = 0; i < 8; i++) {
    id += ID_CHARS[bytes[i] % ID_CHARS.length];
  }
  return id;
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}

function normalizeImages(body) {
  const fromArray = Array.isArray(body.images) ? body.images : [];
  const legacy = body.image ? [body.image] : [];
  const merged = [...fromArray, ...legacy];
  const imgs = [];
  for (const item of merged) {
    const img = String(item || "");
    if (!img.startsWith("data:image/")) continue;
    if (imgs.length >= MAX_IMAGES) break;
    imgs.push(img);
  }
  return imgs;
}

export async function onRequestOptions() {
  return json({ ok: true });
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.SHARES) {
    return json({ error: "KV not configured" }, 500);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON" }, 400);
  }

  const title = String(body.title || "").trim().slice(0, 120);
  const content = String(body.content || "").trim().slice(0, 20000);
  const script = String(body.script || "").trim().slice(0, 60);
  const me = String(body.me || "").trim().slice(0, 40);
  const target = String(body.target || "").trim().slice(0, 40);
  const imgs = normalizeImages(body);
  const isPublic = Boolean(body.public);

  if (!title && !content) {
    return json({ error: "请填写标题或正文" }, 400);
  }

  const payload = {
    t: title || (target ? `致${target}` : "剧本杀售后"),
    c: content,
    s: script,
    m: me,
    r: target,
    imgs,
    img: imgs[0] || "",
    p: isPublic ? 1 : 0,
    th: normalizeTheme(body.theme),
    created: Date.now(),
  };

  const serialized = JSON.stringify(payload);
  if (serialized.length > MAX_BODY) {
    return json({ error: "内容过大，请减少图片数量或压缩后再试" }, 413);
  }

  let id = newId();
  for (let attempt = 0; attempt < 5; attempt++) {
    const existing = await env.SHARES.get(id);
    if (!existing) break;
    id = newId();
  }

  await env.SHARES.put(id, serialized);

  if (isPublic) {
    const catalogKey = "public:catalog";
    let catalog = [];
    try {
      const catalogRaw = await env.SHARES.get(catalogKey);
      catalog = catalogRaw ? JSON.parse(catalogRaw) : [];
    } catch {
      catalog = [];
    }
    catalog = catalog.filter((item) => item.id !== id);
    catalog.unshift({
      id,
      t: payload.t,
      s: script,
      m: me,
      r: target,
      created: payload.created,
    });
    await env.SHARES.put(catalogKey, JSON.stringify(catalog.slice(0, 200)));
  }

  const origin = new URL(request.url).origin;
  return json({
    id,
    url: `${origin}/p/${id}`,
    imageUrl: imgs.length ? `${origin}/api/img/${id}` : "",
    imageCount: imgs.length,
    public: isPublic,
  });
}
