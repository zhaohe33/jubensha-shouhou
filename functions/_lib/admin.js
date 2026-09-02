import { getAuthor } from "./share-store.js";
import { getImageCount } from "./images.js";
import { getShareViews, isStatsKey } from "./analytics.js";

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

export async function summarizeShare(id, data, origin, env) {
  const text = String(data.c || "");
  return {
    id,
    title: data.t || "",
    script: data.s || "",
    me: data.m || "",
    target: data.r || "",
    author: getAuthor(data),
    public: Boolean(data.p),
    created: data.created || null,
    imageCount: getImageCount(data),
    views: env ? await getShareViews(env, id) : 0,
    textLength: text.length,
    blurb: text.replace(/\s+/g, " ").trim().slice(0, 80),
    theme: data.th?.preset || "ink",
    hasEditToken: Boolean(data.e),
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
      if (isStatsKey(key.name)) continue;
      if (key.name.startsWith("image:")) continue;
      if (key.name.startsWith("audio:")) continue;
      const raw = await env.SHARES.get(key.name);
      if (!raw) continue;
      try {
        items.push(await summarizeShare(key.name, JSON.parse(raw), origin, env));
      } catch {
        /* skip */
      }
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);

  items.sort((a, b) => (b.created || 0) - (a.created || 0));
  return items;
}
