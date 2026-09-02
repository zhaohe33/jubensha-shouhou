import {
  buildPayload,
  corsJson,
  newId,
  saveShare,
  syncPublicCatalog,
} from "../_lib/share-store.js";

export async function onRequestOptions() {
  return corsJson({ ok: true });
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.SHARES) return corsJson({ error: "KV not configured" }, 500);

  let body;
  try {
    body = await request.json();
  } catch {
    return corsJson({ error: "Invalid JSON" }, 400);
  }

  const preview = buildPayload({ ...body, _hasBgmUpload: Boolean(body.audio) });
  if (!preview.t && !preview.c) {
    return corsJson({ error: "请填写标题或正文" }, 400);
  }

  let id = newId();
  for (let attempt = 0; attempt < 5; attempt++) {
    if (!(await env.SHARES.get(id))) break;
    id = newId();
  }

  let payload;
  try {
    payload = await saveShare(env, id, body);
  } catch (err) {
    if (err.message === "BODY_TOO_LARGE") {
      return corsJson({ error: "内容过大，请减少图片数量或压缩后再试" }, 413);
    }
    if (err.message?.includes("配乐")) {
      return corsJson({ error: err.message }, 413);
    }
    throw err;
  }

  if (payload.p) await syncPublicCatalog(env, id, payload);

  const origin = new URL(request.url).origin;
  return corsJson({
    id,
    url: `${origin}/p/${id}`,
    editToken: payload.e,
    editUrl: `${origin}/create/?id=${id}`,
    imageUrl: (payload.imgc || payload.imgs?.length) ? `${origin}/api/img/${id}` : "",
    imageCount: payload.imgc || payload.imgs?.length || 0,
    hasBgm: Boolean(payload.bgm),
    musicUrl: payload.bgmu || "",
    public: Boolean(payload.p),
  });
}
