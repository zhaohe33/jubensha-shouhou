export const SITE_VIEWS_KEY = "stats:site:views";

export function shareViewsKey(id) {
  return `stats:share:${id}:views`;
}

export async function deleteShareViews(env, id) {
  if (!env?.SHARES || !id) return;
  await env.SHARES.delete(shareViewsKey(id));
}

export function staticViewsKey(path) {
  const normalized = String(path || "")
    .replace(/\\/g, "/")
    .replace(/\/index\.html$/i, "")
    .replace(/^\/+/, "")
    .slice(0, 240);
  return `stats:static:${normalized}:views`;
}

async function readCount(env, key) {
  const raw = await env.SHARES.get(key);
  const n = parseInt(String(raw || "0"), 10);
  return Number.isFinite(n) && n > 0 ? n : 0;
}

async function increment(env, key) {
  const next = (await readCount(env, key)) + 1;
  await env.SHARES.put(key, String(next));
  return next;
}

export async function getSiteViews(env) {
  if (!env?.SHARES) return 0;
  return readCount(env, SITE_VIEWS_KEY);
}

export async function getShareViews(env, id) {
  if (!env?.SHARES || !id) return 0;
  return readCount(env, shareViewsKey(id));
}

export async function getStaticViews(env, path) {
  if (!env?.SHARES || !path) return 0;
  return readCount(env, staticViewsKey(path));
}

export async function listStaticViews(env) {
  if (!env?.SHARES) return {};
  const out = {};
  let cursor;
  do {
    const page = await env.SHARES.list({ prefix: "stats:static:", cursor, limit: 100 });
    for (const key of page.keys) {
      const m = key.name.match(/^stats:static:(.+):views$/);
      if (m) out[m[1]] = await readCount(env, key.name);
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return out;
}

export async function recordShareView(env, id) {
  if (!env?.SHARES || !id) return;
  await increment(env, SITE_VIEWS_KEY);
  await increment(env, shareViewsKey(id));
}

export async function recordStaticView(env, path) {
  if (!env?.SHARES || !path) return;
  await increment(env, SITE_VIEWS_KEY);
  await increment(env, staticViewsKey(path));
}

export async function recordHomeView(env) {
  if (!env?.SHARES) return;
  await increment(env, SITE_VIEWS_KEY);
}

export function isStatsKey(name) {
  return String(name || "").startsWith("stats:");
}
