import {
  corsJson,
  formWithImages,
  getEditToken,
  saveShare,
  syncPublicCatalog,
  verifyEditToken,
} from "../../_lib/share-store.js";

export async function onRequestOptions() {
  return corsJson({ ok: true });
}

async function loadShare(env, id) {
  const raw = await env.SHARES.get(id);
  if (!raw) return { error: corsJson({ error: "链接不存在" }, 404) };
  try {
    return { data: JSON.parse(raw) };
  } catch {
    return { error: corsJson({ error: "数据损坏" }, 500) };
  }
}

export async function onRequestGet(context) {
  const { env, params } = context;
  const token = getEditToken(context.request);
  const loaded = await loadShare(env, params.id);
  if (loaded.error) return loaded.error;

  const data = loaded.data;
  if (!data.e) {
    return corsJson({ error: "此售后创建于编辑功能上线之前，无法在线编辑" }, 403);
  }
  if (!verifyEditToken(data, token)) {
    return corsJson({ error: "编辑码不正确" }, 401);
  }

  return corsJson({
    id: params.id,
    ...(await formWithImages(env, params.id, data, new URL(context.request.url).origin)),
  });
}

export async function onRequestPut(context) {
  const { env, params, request } = context;
  const token = getEditToken(request);
  const loaded = await loadShare(env, params.id);
  if (loaded.error) return loaded.error;

  const existing = loaded.data;
  if (!existing.e) {
    return corsJson({ error: "此售后无法在线编辑" }, 403);
  }
  if (!verifyEditToken(existing, token)) {
    return corsJson({ error: "编辑码不正确" }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return corsJson({ error: "Invalid JSON" }, 400);
  }

  if (!String(body.title || "").trim() && !String(body.content || "").trim()) {
    return corsJson({ error: "请填写标题或正文" }, 400);
  }

  let payload;
  try {
    payload = await saveShare(env, params.id, body, existing);
  } catch (err) {
    if (err.message === "BODY_TOO_LARGE") {
      return corsJson({ error: "内容过大，请减少图片数量或压缩后再试" }, 413);
    }
    if (err.message?.includes("配乐")) {
      return corsJson({ error: err.message }, 413);
    }
    throw err;
  }

  await syncPublicCatalog(env, params.id, payload);

  const origin = new URL(request.url).origin;
  return corsJson({
    id: params.id,
    url: `${origin}/p/${params.id}`,
    editToken: payload.e,
    hasBgm: Boolean(payload.bgm),
    musicUrl: payload.bgmu || "",
    public: Boolean(payload.p),
    updated: payload.updated,
  });
}
