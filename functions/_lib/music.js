export const MAX_AUDIO = 400_000;

export function audioStorageKey(id) {
  return `audio:${id}`;
}

export function normalizeMusicUrl(raw) {
  const url = String(raw || "").trim();
  if (!url) return "";
  if (!/^https?:\/\//i.test(url)) return "";
  return url.slice(0, 500);
}

export function youtubeVideoId(url) {
  if (!url) return "";
  const m = String(url).match(/(?:v=|youtu\.be\/|embed\/|shorts\/)([A-Za-z0-9_-]{6,})/);
  return m ? m[1] : "";
}

export function bilibiliBvid(url) {
  if (!url) return "";
  const m = String(url).match(/(BV[0-9A-Za-z]+)/i);
  return m ? m[1] : "";
}

export function isBilibiliLink(url) {
  if (!url) return false;
  if (bilibiliBvid(url)) return true;
  try {
    const host = new URL(url).hostname.toLowerCase();
    return (
      host === "b23.tv" ||
      host.endsWith(".b23.tv") ||
      host === "bilibili.com" ||
      host.endsWith(".bilibili.com")
    );
  } catch {
    return false;
  }
}

export function isDirectAudioUrl(url) {
  if (!url) return false;
  return /\.(mp3|m4a|ogg|wav|aac|flac)(\?.*)?$/i.test(url) || /\/audio\//i.test(url);
}

export function getMusicPlayMode(musicUrl, preferUpload) {
  if (preferUpload) return "upload";
  if (!musicUrl) return "";
  if (youtubeVideoId(musicUrl)) return "youtube";
  if (isBilibiliLink(musicUrl)) return "bilibili";
  return "audio";
}

export function isAudioDataUrl(value) {
  return typeof value === "string" && value.startsWith("data:audio/");
}

export function hasUploadedBgm(data) {
  return Boolean(data?.bgm);
}

export function getMusicUrl(data) {
  return normalizeMusicUrl(data?.bgmu);
}

export async function persistBgm(env, id, body, existing) {
  if (body.removeBgm) {
    await env.SHARES.delete(audioStorageKey(id));
    return false;
  }

  const audio = String(body.audio || "");
  if (isAudioDataUrl(audio)) {
    if (audio.length > MAX_AUDIO) {
      throw new Error("上传的配乐过大，请缩短时长或改用音乐链接");
    }
    await env.SHARES.put(audioStorageKey(id), audio);
    return true;
  }

  return hasUploadedBgm(existing) && !body.removeBgm;
}

export function applyBgmFlags(payload, body, existing, hasUpload) {
  if (body.removeBgm) {
    payload.bgm = 0;
    payload.bgmu = "";
    return payload;
  }

  if (body.musicUrl !== undefined) {
    payload.bgmu = normalizeMusicUrl(body.musicUrl);
  } else {
    payload.bgmu = getMusicUrl(existing);
  }

  if (hasUpload) {
    payload.bgm = 1;
  } else if (existing?.bgm) {
    payload.bgm = 1;
  } else {
    payload.bgm = 0;
  }

  return payload;
}
