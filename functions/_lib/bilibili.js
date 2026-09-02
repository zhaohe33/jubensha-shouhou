import { bilibiliBvid, isBilibiliLink, normalizeMusicUrl } from "./music.js";

const BILI_HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  Referer: "https://www.bilibili.com",
  Origin: "https://www.bilibili.com",
  Accept: "application/json, text/plain, */*",
};

async function readBiliJson(res, label) {
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`${label}失败（B 站接口无响应）`);
  }
}

export async function resolveBilibiliBvid(url) {
  const normalized = normalizeMusicUrl(url);
  if (!normalized || !isBilibiliLink(normalized)) return "";

  const direct = bilibiliBvid(normalized);
  if (direct) return direct;

  let current = normalized;
  for (let i = 0; i < 6; i++) {
    const found = bilibiliBvid(current);
    if (found) return found;

    let res;
    try {
      res = await fetch(current, { redirect: "manual", headers: BILI_HEADERS });
    } catch {
      break;
    }

    if (res.status >= 300 && res.status < 400) {
      const location = res.headers.get("Location");
      if (!location) break;
      current = new URL(location, current).toString();
      continue;
    }

    if (res.ok) {
      const finalUrl = res.url || current;
      const fromUrl = bilibiliBvid(finalUrl);
      if (fromUrl) return fromUrl;
      const html = await res.text();
      const fromHtml = bilibiliBvid(html);
      if (fromHtml) return fromHtml;
    }
    break;
  }

  return "";
}

export async function normalizeBilibiliMusicUrl(url) {
  const normalized = normalizeMusicUrl(url);
  if (!normalized || !isBilibiliLink(normalized)) return normalized;
  const bvid = bilibiliBvid(normalized) || (await resolveBilibiliBvid(normalized));
  return bvid ? `https://www.bilibili.com/video/${bvid}` : normalized;
}

export async function getBilibiliMeta(bvid) {
  const res = await fetch(
    `https://api.bilibili.com/x/web-interface/view?bvid=${encodeURIComponent(bvid)}`,
    { headers: BILI_HEADERS },
  );
  const data = await readBiliJson(res, "读取 B 站视频信息");
  if (data.code !== 0) {
    throw new Error(data.message || "无法读取 B 站视频信息");
  }
  const info = data.data || {};
  const cid = info.cid || info.pages?.[0]?.cid;
  if (!cid) throw new Error("无法获取 B 站分 P 信息");
  return {
    bvid: info.bvid || bvid,
    aid: info.aid || "",
    cid,
  };
}

export async function getBilibiliCid(bvid) {
  const meta = await getBilibiliMeta(bvid);
  return meta.cid;
}

export async function getBilibiliAudioUrl(bvid, cid) {
  const qs = new URLSearchParams({
    bvid,
    cid: String(cid),
    qn: "16",
    fnval: "16",
  });
  const res = await fetch(
    `https://api.bilibili.com/x/player/playurl?${qs}`,
    { headers: BILI_HEADERS },
  );
  const data = await readBiliJson(res, "获取 B 站播放地址");
  if (data.code !== 0) {
    throw new Error(data.message || "无法获取 B 站播放地址");
  }
  const tracks = data.data?.dash?.audio;
  if (!tracks?.length) {
    throw new Error("该视频没有可用音轨");
  }
  const track = tracks.reduce((a, b) => (a.bandwidth < b.bandwidth ? a : b));
  return track.baseUrl || track.base_url || "";
}

export async function resolveBilibiliAudioProxyUrl(bvid, origin) {
  const cid = await getBilibiliCid(bvid);
  const audioUrl = await getBilibiliAudioUrl(bvid, cid);
  if (!audioUrl) throw new Error("无法解析 B 站音频");
  const proxy = new URL("/api/music-proxy", origin);
  proxy.searchParams.set("url", audioUrl);
  return proxy.toString();
}
