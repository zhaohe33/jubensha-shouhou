import { getAuthor } from "../_lib/share-store.js";
import { getImageCount } from "../_lib/images.js";

const CATALOG_KEY = "public:catalog";
const MAX_CATALOG = 200;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "public, max-age=60",
    },
  });
}

export async function onRequestGet(context) {
  const { env } = context;
  if (!env.SHARES) return json([], 500);

  const raw = await env.SHARES.get(CATALOG_KEY);
  let catalog = [];
  try {
    catalog = raw ? JSON.parse(raw) : [];
  } catch {
    catalog = [];
  }

  const items = [];
  const kept = [];

  for (const item of catalog) {
    if (!item?.id) continue;
    const shareRaw = await env.SHARES.get(item.id);
    if (!shareRaw) continue;

    let data;
    try {
      data = JSON.parse(shareRaw);
    } catch {
      continue;
    }
    if (!data.p) continue;

    const blurb = String(data.c || "").replace(/\s+/g, " ").trim();
    const hasImage = getImageCount(data) > 0;

    items.push({
      id: item.id,
      title: data.t || item.t || "剧本杀售后",
      script: data.s || "",
      me: data.m || "",
      target: data.r || "",
      author: getAuthor(data),
      blurb: blurb.length > 28 ? `${blurb.slice(0, 28)}…` : blurb,
      hasImage,
      user: true,
    });
    kept.push({
      id: item.id,
      t: data.t,
      s: data.s,
      m: data.m,
      r: data.r,
      a: getAuthor(data),
      created: data.created || item.created || 0,
    });
  }

  if (kept.length !== catalog.length) {
    await env.SHARES.put(CATALOG_KEY, JSON.stringify(kept.slice(0, MAX_CATALOG)));
  }

  return json(items);
}
