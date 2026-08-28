function parseImageDataUrl(dataUrl) {
  if (!dataUrl || !dataUrl.startsWith("data:image/")) return null;
  const m = dataUrl.match(/^data:(image\/[a-z+]+);base64,(.+)$/i);
  if (!m) return null;
  const binary = atob(m[2]);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return { type: m[1], bytes };
}

function getImages(data) {
  if (Array.isArray(data.imgs)) {
    return data.imgs.filter((img) => typeof img === "string" && img.startsWith("data:image/"));
  }
  if (data.img && data.img.startsWith("data:image/")) return [data.img];
  return [];
}

export async function onRequestGet(context) {
  const { env, params, request } = context;
  const raw = await env.SHARES.get(params.id);
  if (!raw) return new Response("Not found", { status: 404 });

  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return new Response("Invalid", { status: 500 });
  }

  const images = getImages(data);
  if (!images.length) return new Response("No image", { status: 404 });

  const index = Number(new URL(request.url).searchParams.get("i") || "0");
  const safeIndex = Number.isFinite(index) && index >= 0 ? Math.floor(index) : 0;
  const image = parseImageDataUrl(images[safeIndex] || images[0]);
  if (!image) return new Response("No image", { status: 404 });

  return new Response(image.bytes, {
    headers: {
      "Content-Type": image.type,
      "Cache-Control": "public, max-age=86400",
    },
  });
}
