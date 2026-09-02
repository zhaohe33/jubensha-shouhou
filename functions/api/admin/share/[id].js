import { json, requireAdmin, summarizeShare } from "../../../_lib/admin.js";
import { deleteImages } from "../../../_lib/images.js";
import { audioStorageKey } from "../../../_lib/music.js";

const catalogKey = "public:catalog";

async function removeFromCatalog(env, id) {
  const raw = await env.SHARES.get(catalogKey);
  if (!raw) return;
  try {
    const catalog = JSON.parse(raw).filter((item) => item.id !== id);
    await env.SHARES.put(catalogKey, JSON.stringify(catalog));
  } catch {
    /* ignore */
  }
}

export async function onRequestGet(context) {
  const auth = requireAdmin(context.request, context.env);
  if (auth.error) return auth.error;

  const { env, params, request } = context;
  const raw = await env.SHARES.get(params.id);
  if (!raw) return json({ error: "不存在" }, 404);

  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return json({ error: "数据损坏" }, 500);
  }

  const origin = new URL(request.url).origin;
  const summary = await summarizeShare(params.id, data, origin, env);
  const imgs = Array.isArray(data.imgs) ? data.imgs : data.img ? [data.img] : [];

  return json({
    ...summary,
    content: data.c || "",
    theme: data.th || null,
    images: imgs.map((_, i) => `${origin}/api/img/${params.id}?i=${i}`),
    payloadSize: raw.length,
  });
}

export async function onRequestDelete(context) {
  const auth = requireAdmin(context.request, context.env);
  if (auth.error) return auth.error;

  const { env, params } = context;
  await env.SHARES.delete(params.id);
  await env.SHARES.delete(audioStorageKey(params.id));
  await deleteImages(env, params.id);
  await removeFromCatalog(env, params.id);
  return json({ ok: true, id: params.id });
}
