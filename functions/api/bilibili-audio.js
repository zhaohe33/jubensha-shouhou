import { bilibiliBvid } from "../_lib/music.js";
import { resolveBilibiliAudioProxyUrl } from "../_lib/bilibili.js";

export async function onRequestGet(context) {
  const bvid = bilibiliBvid(
    new URL(context.request.url).searchParams.get("bvid") || "",
  );
  if (!bvid) {
    return Response.json({ error: "无效的 B 站链接" }, { status: 400 });
  }

  try {
    const url = await resolveBilibiliAudioProxyUrl(
      bvid,
      new URL(context.request.url).origin,
    );
    return Response.json({ url });
  } catch (err) {
    return Response.json(
      { error: err.message || "解析 B 站音频失败" },
      { status: 502 },
    );
  }
}
