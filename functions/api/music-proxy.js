function isAllowedUrl(url) {
  try {
    const parsed = new URL(url);
    if (!["http:", "https:"].includes(parsed.protocol)) return false;
    const host = parsed.hostname.toLowerCase();
    if (host === "localhost" || host.endsWith(".local")) return false;
    if (/^(10\.|127\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)/.test(host)) return false;
    return true;
  } catch {
    return false;
  }
}

function upstreamHeaders(target) {
  const headers = { "User-Agent": "jubensha-shouhou/1.0" };
  try {
    const host = new URL(target).hostname.toLowerCase();
    if (
      host.includes("bilivideo") ||
      host.includes("akamaized") ||
      host.includes("hdslb.com") ||
      host.includes("bilibili.com")
    ) {
      headers.Referer = "https://www.bilibili.com";
    }
  } catch {}
  return headers;
}

export async function onRequestGet(context) {
  const target = new URL(context.request.url).searchParams.get("url");
  if (!target || !isAllowedUrl(target)) {
    return new Response("Invalid url", { status: 400 });
  }

  let upstream;
  try {
    upstream = await fetch(target, {
      redirect: "follow",
      headers: upstreamHeaders(target),
    });
  } catch {
    return new Response("Fetch failed", { status: 502 });
  }

  if (!upstream.ok) {
    return new Response("Upstream error", { status: upstream.status });
  }

  const contentType = upstream.headers.get("content-type") || "application/octet-stream";
  const looksLikeAudio =
    contentType.startsWith("audio/") ||
    contentType.includes("octet-stream") ||
    /\.(mp3|m4a|ogg|wav|aac|flac)(\?.*)?$/i.test(target);

  if (!looksLikeAudio) {
    return new Response("Not an audio resource", { status: 415 });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": contentType.split(";")[0],
      "Cache-Control": "public, max-age=3600",
      "Access-Control-Allow-Origin": "*",
    },
  });
}
