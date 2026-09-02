import { audioStorageKey } from "../../_lib/music.js";

function parseAudioDataUrl(dataUrl) {
  if (!dataUrl || !dataUrl.startsWith("data:audio/")) return null;
  const m = dataUrl.match(/^data:(audio\/[a-z0-9+.-]+);base64,(.+)$/i);
  if (!m) return null;
  const binary = atob(m[2]);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return { type: m[1], bytes };
}

export async function onRequestGet(context) {
  const { env, params } = context;
  const raw = await env.SHARES.get(audioStorageKey(params.id));
  if (!raw) return new Response("Not found", { status: 404 });

  const audio = parseAudioDataUrl(raw);
  if (!audio) return new Response("Invalid", { status: 500 });

  return new Response(audio.bytes, {
    headers: {
      "Content-Type": audio.type,
      "Cache-Control": "public, max-age=86400",
    },
  });
}
