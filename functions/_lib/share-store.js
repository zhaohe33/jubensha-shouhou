import { normalizeBilibiliMusicUrl } from "./bilibili.js";
import {
  getInlineImages,
  imageUrlsForForm,
  persistImages,
} from "./images.js";
import {
  applyBgmFlags,
  getMusicUrl,
  hasUploadedBgm,
  persistBgm,
} from "./music.js";
import { normalizeTheme } from "./theme.js";

export const CATALOG_KEY = "public:catalog";
export const MAX_BODY = 200_000;
export const MAX_IMAGES = 8;

const ID_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789";

export function newId() {
  let id = "";
  const bytes = crypto.getRandomValues(new Uint8Array(8));
  for (let i = 0; i < 8; i++) id += ID_CHARS[bytes[i] % ID_CHARS.length];
  return id;
}

export function newEditToken() {
  let token = "";
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  for (let i = 0; i < 16; i++) token += ID_CHARS[bytes[i] % ID_CHARS.length];
  return token;
}

export function corsJson(data, status = 200, methods = "GET, POST, PUT, OPTIONS") {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": methods,
      "Access-Control-Allow-Headers": "Content-Type, X-Edit-Token, Authorization",
    },
  });
}

export function normalizeImages(body) {
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

export function getAuthor(data) {
  return String(data?.a || "").trim();
}

export function buildPayload(body, existing = null) {
  const title = String(body.title || "").trim().slice(0, 120);
  const content = String(body.content || "").trim().slice(0, 20000);
  const script = String(body.script || "").trim().slice(0, 60);
  const me = String(body.me || "").trim().slice(0, 40);
  const target = String(body.target || "").trim().slice(0, 40);
  const author = String(body.author || "").trim().slice(0, 40);
  const imgs = normalizeImages(body);
  const isPublic = Boolean(body.public);
  const now = Date.now();
  const hasUpload = Boolean(body._hasBgmUpload);
  const useExternalImages = body._imgCount !== undefined;
  const imgc = useExternalImages ? Number(body._imgCount || 0) : imgs.length;

  const payload = {
    t: title || (target ? `致${target}` : "剧本杀售后"),
    c: content,
    s: script,
    m: me,
    r: target,
    a: author,
    imgc,
    imgs: useExternalImages ? [] : imgs,
    img: useExternalImages ? "" : imgs[0] || "",
    p: isPublic ? 1 : 0,
    th: normalizeTheme(body.theme),
    e: existing?.e || newEditToken(),
    created: existing?.created || now,
    updated: now,
    bgmu: "",
    bgm: 0,
  };

  return applyBgmFlags(payload, body, existing, hasUpload);
}

export function getEditToken(request) {
  const auth = request.headers.get("Authorization") || "";
  if (auth.startsWith("Bearer ")) return auth.slice(7).trim();
  return (request.headers.get("X-Edit-Token") || "").trim();
}

export function verifyEditToken(data, token) {
  return Boolean(data?.e && token && data.e === token);
}

export async function syncPublicCatalog(env, id, payload) {
  let catalog = [];
  try {
    const raw = await env.SHARES.get(CATALOG_KEY);
    catalog = raw ? JSON.parse(raw) : [];
  } catch {
    catalog = [];
  }

  catalog = catalog.filter((item) => item.id !== id);

  if (payload.p) {
    catalog.unshift({
      id,
      t: payload.t,
      s: payload.s,
      m: payload.m,
      r: payload.r,
      a: payload.a,
      created: payload.created,
    });
  }

  await env.SHARES.put(CATALOG_KEY, JSON.stringify(catalog.slice(0, 200)));
}

export function payloadToForm(data) {
  const imgs = getInlineImages(data);
  const externalCount = Number(data.imgc || 0);

  return {
    title: data.t || "",
    content: data.c || "",
    script: data.s || "",
    me: data.m || "",
    target: data.r || "",
    author: getAuthor(data),
    images: imgs,
    imageCount: externalCount || imgs.length,
    public: Boolean(data.p),
    theme: data.th || null,
    musicUrl: getMusicUrl(data),
    hasBgm: hasUploadedBgm(data),
    created: data.created || null,
    updated: data.updated || null,
  };
}

export async function saveShare(env, id, body, existing = null) {
  if (body.musicUrl !== undefined && String(body.musicUrl || "").trim()) {
    body.musicUrl = await normalizeBilibiliMusicUrl(String(body.musicUrl).trim());
  }
  body._hasBgmUpload = await persistBgm(env, id, body, existing);
  body._imgCount = await persistImages(env, id, normalizeImages(body));
  const payload = buildPayload(body, existing);
  const serialized = JSON.stringify(payload);
  if (serialized.length > MAX_BODY) {
    throw new Error("BODY_TOO_LARGE");
  }
  await env.SHARES.put(id, serialized);
  return payload;
}

export async function formWithImages(env, id, data, origin = "") {
  const form = payloadToForm(data);
  if (Number(data.imgc || 0) > 0 && !form.images.length) {
    form.images = imageUrlsForForm(id, data.imgc, origin);
  }
  return form;
}
