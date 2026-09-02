export const MAX_IMAGE_BLOB = 600_000;
export const MAX_IMAGES = 8;

export function imageStorageKey(id, index) {
  return `image:${id}:${index}`;
}

export function getInlineImages(data) {
  if (Array.isArray(data?.imgs)) {
    return data.imgs.filter((img) => typeof img === "string" && img.startsWith("data:image/"));
  }
  if (data?.img && data.img.startsWith("data:image/")) return [data.img];
  return [];
}

export function getImageCount(data) {
  const external = Number(data?.imgc || 0);
  if (external > 0) return external;
  return getInlineImages(data).length;
}

export async function deleteImages(env, id) {
  for (let i = 0; i < MAX_IMAGES; i++) {
    await env.SHARES.delete(imageStorageKey(id, i));
  }
}

export async function loadImageData(env, id, data, index) {
  const external = await env.SHARES.get(imageStorageKey(id, index));
  if (external && external.startsWith("data:image/")) return external;

  const inline = getInlineImages(data);
  return inline[index] || inline[0] || "";
}

export async function persistImages(env, shareId, images) {
  const resolved = [];

  for (const item of images) {
    const img = String(item || "");
    if (img.startsWith("data:image/")) {
      if (img.length > MAX_IMAGE_BLOB) {
        throw new Error("某张图片过大，请减少数量或换更小的图");
      }
      resolved.push(img);
      continue;
    }

    if (img.includes("/api/img/")) {
      const m = img.match(/[?&]i=(\d+)/);
      const idx = m ? Number(m[1]) : -1;
      if (idx >= 0) {
        const existing = await env.SHARES.get(imageStorageKey(shareId, idx));
        if (existing) resolved.push(existing);
      }
    }
  }

  if (resolved.length > MAX_IMAGES) {
    resolved.length = MAX_IMAGES;
  }

  await deleteImages(env, shareId);
  for (let i = 0; i < resolved.length; i++) {
    await env.SHARES.put(imageStorageKey(shareId, i), resolved[i]);
  }

  return resolved.length;
}

export function imageUrlsForForm(id, count, origin = "") {
  const prefix = origin || "";
  return Array.from({ length: count }, (_, i) => `${prefix}/api/img/${id}?i=${i}`);
}
