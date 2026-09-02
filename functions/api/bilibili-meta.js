import { bilibiliBvid } from "../_lib/music.js";
import { getBilibiliMeta } from "../_lib/bilibili.js";

export async function onRequestGet(context) {
  const bvid = bilibiliBvid(
    new URL(context.request.url).searchParams.get("bvid") || "",
  );
  if (!bvid) {
    return Response.json({ error: "无效的 B 站链接" }, { status: 400 });
  }

  try {
    const meta = await getBilibiliMeta(bvid);
    return Response.json(meta);
  } catch (err) {
    return Response.json(
      { error: err.message || "读取 B 站信息失败" },
      { status: 502 },
    );
  }
}
