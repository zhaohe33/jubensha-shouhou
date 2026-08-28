function parseImage(data) {
  if (!data?.img || !data.img.startsWith("data:image/")) return null;
  const m = data.img.match(/^data:(image\/[a-z+]+);base64,(.+)$/i);
  if (!m) return null;
  const binary = atob(m[2]);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return { type: m[1], bytes };
}

export async function onRequestGet(context) {
  const { env, params } = context;
  const raw = await env.SHARES.get(params.id);
  if (!raw) return new Response("Not found", { status: 404 });

  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return new Response("Invalid", { status: 500 });
  }

  const image = parseImage(data);
  if (!image) return new Response("No image", { status: 404 });

  return new Response(image.bytes, {
    headers: {
      "Content-Type": image.type,
      "Cache-Control": "public, max-age=86400",
    },
  });
}
