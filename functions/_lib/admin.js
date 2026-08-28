const CATALOG_KEY = "public:catalog";

export function unauthorized() {
  return new Response(JSON.stringify({ error: "未授权" }), {
    status: 401,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

export function requireAdmin(request, env) {
  const token = env.ADMIN_TOKEN;
  if (!token) {
    return { error: new Response(JSON.stringify({ error: "后台未配置 ADMIN_TOKEN" }), { status: 503, headers: { "Content-Type": "application/json" } }) };
  }
  const auth = request.headers.get("Authorization") || "";
  const bearer = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  const header = request.headers.get("X-Admin-Token") || "";
  if (bearer !== token && header !== token) {
    return { error: unauthorized() };
  }
  return { ok: true };
}

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

export function summarizeShare(id, data, origin) {
  const imgs = Array.isArray(data.imgs) ? data.imgs : data.img ? [data.img] : [];
  const text = String(data.c || "");
  return {
    id,
    title: data.t || "",
    script: data.s || "",
    me: data.m || "",
    target: data.r || "",
    public: Boolean(data.p),
    created: data.created || null,
    imageCount: imgs.length,
    textLength: text.length,
    blurb: text.replace(/\s+/g, " ").trim().slice(0, 80),
    theme: data.th?.preset || "ink",
    url: `${origin}/p/${id}`,
  };
}

export async function listAllShares(env, origin) {
  const items = [];
  let cursor;
  do {
    const page = await env.SHARES.list({ cursor, limit: 100 });
    for (const key of page.keys) {
      if (key.name === CATALOG_KEY) continue;
      const raw = await env.SHARES.get(key.name);
      if (!raw) continue;
      try {
        items.push(summarizeShare(key.name, JSON.parse(raw), origin));
      } catch {
        /* skip */
      }
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);

  items.sort((a, b) => (b.created || 0) - (a.created || 0));
  return items;
}
