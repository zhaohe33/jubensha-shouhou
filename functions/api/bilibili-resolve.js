import { normalizeMusicUrl } from "../_lib/music.js";
import { resolveBilibiliBvid } from "../_lib/bilibili.js";

export async function onRequestGet(context) {
  const raw = new URL(context.request.url).searchParams.get("url") || "";
  const url = normalizeMusicUrl(raw);
  if (!url) {
    return Response.json({ error: "无效的链接" }, { status: 400 });
  }

  const bvid = await resolveBilibiliBvid(url);
  if (!bvid) {
    return Response.json({ error: "无法识别 B 站链接" }, { status: 400 });
  }

  return Response.json({
    bvid,
    url: `https://www.bilibili.com/video/${bvid}`,
  });
}
