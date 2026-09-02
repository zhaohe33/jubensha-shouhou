import { normalizeTheme, themeCss, themeFontLink } from "../_lib/theme.js";
import {
  getUnmarkedImageIndices,
  parseMarkerIndex,
  splitContentParts,
} from "../_lib/content.js";
import {
  audioStorageKey,
  bilibiliBvid,
  getMusicPlayMode,
  getMusicUrl,
  hasUploadedBgm,
  youtubeVideoId,
} from "../_lib/music.js";
import { getImageCount } from "../_lib/images.js";
import { recordShareView } from "../_lib/analytics.js";

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderTextSegment(text) {
  const trimmed = String(text || "")
    .replace(/\r\n/g, "\n")
    .trim();
  if (!trimmed) return "";

  return trimmed
    .split(/\n\s*\n/)
    .map((block) => {
      const lines = block
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .map((l) => esc(l))
        .join("<br />\n");
      return lines ? `        <p>${lines}</p>\n` : "";
    })
    .join("");
}

function renderFigure(pageId, index) {
  return `        <figure class="inline-fig"><img src="/api/img/${esc(pageId)}?i=${index}" alt="" loading="lazy" /></figure>\n`;
}

function renderProse(content, pageId, imageCount) {
  const text = String(content || "").replace(/\r\n/g, "\n").trim();
  if (!text) return '        <p class="empty">（暂无文字）</p>';

  const parts = splitContentParts(text);
  let html = "";
  for (const part of parts) {
    const idx = parseMarkerIndex(part);
    if (idx >= 0) {
      if (idx < imageCount) html += renderFigure(pageId, idx);
      continue;
    }
    html += renderTextSegment(part);
  }

  return html.trim() || '        <p class="empty">（暂无文字）</p>';
}

function renderBottomGallery(pageId, indices) {
  if (!indices.length) return "";
  return `\n        <div class="letter-gallery" aria-label="配图">\n${indices.map((i) => renderFigure(pageId, i)).join("")}        </div>\n`;
}

function renderMusicBlock(pageId, data, preferUpload) {
  const musicUrl = getMusicUrl(data);
  if (!preferUpload && !musicUrl) return "";

  const mode = getMusicPlayMode(musicUrl, preferUpload);
  const ytId = mode === "youtube" ? youtubeVideoId(musicUrl) : "";
  const bvid = mode === "bilibili" ? bilibiliBvid(musicUrl) : "";
  let audioSrc = "";
  if (mode === "upload") {
    audioSrc = `/api/audio/${esc(pageId)}`;
  } else if (mode === "audio" && musicUrl) {
    audioSrc = `/api/music-proxy?url=${encodeURIComponent(musicUrl)}`;
  }

  const musicConfig = JSON.stringify({
    mode,
    ytId,
    bvid,
    audioSrc,
    fallbackUrl: musicUrl,
  });

  const audioTag = audioSrc
    ? `<audio id="bgm" loop preload="auto" playsinline src="${audioSrc}"></audio>`
    : "";
  const ytEmbed = ytId || bvid
    ? `<div class="music-dock" id="musicDock" hidden>
        <iframe id="ytBgm" class="yt-bgm" title="背景音乐" allow="autoplay; encrypted-media; fullscreen" src=""></iframe>
      </div>`
    : "";

  return `
  <button class="music-btn is-off" id="musicBtn" type="button" aria-label="播放背景音乐" title="点击播放音乐">♪</button>
  <p class="music-tip" id="musicTip"></p>
  ${audioTag}
  ${ytEmbed}
  <script>
    (function () {
      const btn = document.getElementById("musicBtn");
      const audio = document.getElementById("bgm");
      const dock = document.getElementById("musicDock");
      const yt = document.getElementById("ytBgm");
      const tip = document.getElementById("musicTip");
      const cfg = ${musicConfig};
      const storageKey = "shouhou-bgm:" + ${JSON.stringify(pageId)};
      const isTouch = matchMedia("(hover: none)").matches || "ontouchstart" in window;
      const isWeChat = /MicroMessenger/i.test(navigator.userAgent);

      function setPlaying(on) {
        btn.classList.toggle("is-off", !on);
        btn.classList.toggle("is-playing", on);
        btn.textContent = on ? "❚❚" : "♪";
      }

      function showTip(msg) {
        if (!tip) return;
        tip.textContent = msg || "";
        tip.classList.toggle("visible", Boolean(msg));
      }

      function openDock() {
        if (dock) dock.hidden = false;
        if (dock) dock.classList.add("is-open");
      }

      function closeDock() {
        if (dock) dock.classList.remove("is-open");
        if (dock) dock.hidden = true;
      }

      function ensureAudio() {
        let el = document.getElementById("bgm");
        if (el) return el;
        el = document.createElement("audio");
        el.id = "bgm";
        el.loop = true;
        el.preload = "auto";
        el.setAttribute("playsinline", "");
        document.body.appendChild(el);
        el.addEventListener("error", () => {
          if (btn.classList.contains("is-playing")) {
            setPlaying(false);
            showTip("音频加载失败，请检查链接或改用上传配乐");
          }
        });
        return el;
      }

      function ensureEmbedFrame() {
        if (yt) return yt;
        const wrap = document.createElement("div");
        wrap.className = "music-dock is-open";
        wrap.id = "musicDock";
        const frame = document.createElement("iframe");
        frame.id = "ytBgm";
        frame.className = "yt-bgm";
        frame.title = "背景音乐";
        frame.allow = "autoplay; encrypted-media; fullscreen";
        frame.referrerPolicy = "origin";
        wrap.appendChild(frame);
        document.body.appendChild(wrap);
        return frame;
      }

      function nudgeEmbed(frame) {
        if (!frame) return;
        const play = () => {
          try { frame.contentWindow?.postMessage({ command: "play" }, "*"); } catch {}
          try { frame.contentWindow?.postMessage({ event: "command", func: "play", data: "" }, "*"); } catch {}
        };
        frame.addEventListener("load", () => setTimeout(play, 300));
        setTimeout(play, 800);
      }

      async function resolveBvid() {
        if (cfg.bvid) return cfg.bvid;
        if (!cfg.fallbackUrl) return "";
        const res = await fetch(
          "/api/bilibili-resolve?url=" + encodeURIComponent(cfg.fallbackUrl),
        );
        const data = await res.json().catch(() => ({}));
        return res.ok && data.bvid ? data.bvid : "";
      }

      async function fetchBiliMeta(bvid) {
        const res = await fetch("/api/bilibili-meta?bvid=" + encodeURIComponent(bvid));
        const data = await res.json().catch(() => ({}));
        return res.ok ? data : { bvid };
      }

      function biliPlayerSrc(meta) {
        if (isTouch) {
          return "https://www.bilibili.com/blackboard/html5mobileplayer.html?bvid="
            + encodeURIComponent(meta.bvid) + "&page=1&autoplay=1";
        }
        const qs = new URLSearchParams({
          bvid: meta.bvid,
          page: "1",
          autoplay: "1",
          high_quality: "1",
          danmaku: "0",
        });
        if (meta.cid) qs.set("cid", String(meta.cid));
        if (meta.aid) qs.set("aid", String(meta.aid));
        return "https://player.bilibili.com/player.html?" + qs.toString();
      }

      function biliOpenUrl(bvid) {
        return cfg.fallbackUrl || ("https://www.bilibili.com/video/" + bvid);
      }

      async function playBilibili() {
        const bvid = await resolveBvid();
        if (!bvid) throw new Error("无法识别 B 站链接");

        if (isWeChat) {
          const url = biliOpenUrl(bvid);
          showTip("微信内无法嵌入 B 站，点此前往哔哩哔哩播放");
          tip.style.cursor = "pointer";
          tip.onclick = () => { window.location.href = url; };
          throw new Error("wechat");
        }

        try {
          const res = await fetch("/api/bilibili-audio?bvid=" + encodeURIComponent(bvid));
          const data = await res.json().catch(() => ({}));
          if (res.ok && data.url) {
            const el = ensureAudio();
            el.volume = 0.4;
            if (el.src !== data.url) {
              el.src = data.url;
              el.load();
            }
            await el.play();
            closeDock();
            return;
          }
        } catch {}

        const meta = await fetchBiliMeta(bvid);
        const frame = ensureEmbedFrame();
        openDock();
        frame.src = biliPlayerSrc(meta);
        nudgeEmbed(frame);
        if (isTouch) {
          showTip("B 站链接在手机可能无声，建议上传 mp3 配乐");
        }
      }

      function loadIframe() {
        const frame = yt || ensureEmbedFrame();
        if (!frame || !cfg.ytId) return;
        openDock();
        frame.src = "https://www.youtube-nocookie.com/embed/" + cfg.ytId
          + "?autoplay=1&loop=1&playlist=" + cfg.ytId
          + "&controls=0&playsinline=1&rel=0";
        nudgeEmbed(frame);
      }

      async function playMusic() {
        showTip("");
        try {
          if (audio) {
            audio.volume = 0.4;
            if (audio.error) audio.load();
            await audio.play();
            closeDock();
            setPlaying(true);
            localStorage.setItem(storageKey, "on");
            return;
          }
          if (cfg.bvid || cfg.mode === "bilibili") {
            await playBilibili();
            setPlaying(true);
            localStorage.setItem(storageKey, "on");
            return;
          }
          if (cfg.ytId) {
            loadIframe();
            setPlaying(true);
            localStorage.setItem(storageKey, "on");
            return;
          }
          showTip("无法识别此音乐链接，请改用 mp3 直链、YouTube 或 B 站链接");
        } catch (err) {
          setPlaying(false);
          closeDock();
          if (err && err.message === "wechat") return;
          if (cfg.mode === "upload" && cfg.fallbackUrl && audio) {
            showTip("上传配乐不可用，请重新编辑");
          } else if (cfg.mode === "audio") {
            showTip("无法播放，请确认链接是可直接打开的 mp3/m4a 音频");
          } else if (cfg.mode === "bilibili") {
            showTip("B 站播放失败，建议上传配乐或 mp3 直链");
          } else {
            showTip("播放失败，国内网络可能无法访问 YouTube");
          }
        }
      }

      function pauseMusic() {
        const activeAudio = document.getElementById("bgm");
        if (activeAudio) {
          activeAudio.pause();
          try { activeAudio.currentTime = 0; } catch {}
        }
        const frame = document.getElementById("ytBgm");
        if (frame) frame.src = "";
        closeDock();
        setPlaying(false);
        localStorage.setItem(storageKey, "off");
        showTip("");
      }

      if (audio) {
        audio.addEventListener("error", () => {
          if (btn.classList.contains("is-playing")) {
            setPlaying(false);
            showTip("音频加载失败，请检查链接或改用上传配乐");
          }
        });
      }

      btn.addEventListener("click", () => {
        if (btn.classList.contains("is-playing")) pauseMusic();
        else playMusic();
      });

      if (!isTouch && localStorage.getItem(storageKey) === "on") playMusic();
    })();
  </script>`;
}

export async function onRequestGet(context) {
  const { env, params, request } = context;
  const raw = await env.SHARES.get(params.id);
  if (!raw) {
    return new Response("链接不存在或已过期", {
      status: 404,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return new Response("数据损坏", { status: 500 });
  }

  const origin = new URL(request.url).origin;
  const title = data.t || "剧本杀售后";
  const script = data.s || "";
  const me = data.m || "";
  const target = data.r || "";
  const author = String(data.a || "").trim();
  const meta = [script, me].filter(Boolean).join(" · ");
  const roleLine = me && target ? `${me} → ${target}` : (me || target || "");
  const subLine = [author, roleLine].filter(Boolean).join(" · ");
  const desc = (data.c || "").replace(/\s+/g, " ").trim().slice(0, 120);
  const imageCount = getImageCount(data);
  const ogImage = imageCount
    ? `${origin}/api/img/${params.id}`
    : `${origin}/media/duos/qingbai-suwuyang-axi.jpg`;
  const pageUrl = `${origin}/p/${params.id}`;
  const bottomIndices = getUnmarkedImageIndices(data.c || "", imageCount);
  const musicBlock = renderMusicBlock(
    params.id,
    data,
    hasUploadedBgm(data) && Boolean(await env.SHARES.get(audioStorageKey(params.id))),
  );

  context.waitUntil(recordShareView(env, params.id));

  const theme = normalizeTheme(data.th);
  const fontHref = themeFontLink(theme);
  const themeStyles = themeCss(theme);

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${esc(title)}${script ? ` · ${esc(script)}` : ""}</title>
  <meta name="description" content="${esc(desc)}" />
  <meta property="og:type" content="article" />
  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(desc)}" />
  <meta property="og:image" content="${esc(ogImage)}" />
  <meta property="og:url" content="${esc(pageUrl)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${esc(title)}" />
  <meta name="twitter:description" content="${esc(desc)}" />
  <meta name="twitter:image" content="${esc(ogImage)}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="${esc(fontHref)}" rel="stylesheet" />
  <style>
    * { box-sizing:border-box; margin:0; padding:0; }
    body { line-height:1.95; min-height:100vh; }
    body::before { content:""; position:fixed; inset:0; z-index:0; pointer-events:none; }
    ${themeStyles}
    .wrap { position:relative; z-index:2; max-width:720px; margin:0 auto; padding:2.5rem 1.35rem 4rem; }
    .back { display:inline-flex; text-decoration:none; font-size:.82rem; letter-spacing:.22em; margin-bottom:2.2rem; }
    .meta { font-size:.78rem; letter-spacing:.28em; margin-bottom:.85rem; }
    h1 { letter-spacing:.16em; line-height:1.15; margin-bottom:.4rem; }
    .sub { color:var(--paper-soft); letter-spacing:.12em; font-size:.95em; margin-bottom:2rem; }
    .line { width:2.2rem; height:1px; margin:0 0 2rem; }
    .prose p { margin-bottom:1.15rem; letter-spacing:.04em; }
    .prose .inline-fig { margin:1.1rem 0 1.35rem; }
    .prose .inline-fig img { width:100%; display:block; border:1px solid var(--line); object-fit:cover; }
    .letter-gallery { margin-top:1.5rem; display:flex; flex-direction:column; gap:.75rem; }
    .cta { margin-top:2.5rem; padding-top:1.5rem; border-top:1px solid var(--line); }
    .cta a { display:inline-block; margin-right:.75rem; margin-bottom:.5rem; padding:.65rem 1rem; text-decoration:none; font-size:.82rem; letter-spacing:.18em; }
    .music-btn {
      position:fixed; right:1rem; bottom:1rem; z-index:30;
      width:3rem; height:3rem; border-radius:50%;
      border:1px solid var(--line); background:rgba(16,14,12,.82);
      color:var(--paper); font-size:1.1rem; cursor:pointer;
      backdrop-filter:blur(8px);
    }
    .music-btn.is-playing { border-color:rgba(156,47,42,.65); color:var(--seal); }
    .music-tip {
      position:fixed; right:1rem; bottom:4.5rem; z-index:30; max-width:min(16rem, 72vw);
      padding:.45rem .65rem; font-size:.72rem; letter-spacing:.06em; line-height:1.5;
      color:var(--paper-soft); background:rgba(16,14,12,.88); border:1px solid var(--line);
      display:none;
    }
    .music-tip.visible { display:block; }
    .music-dock {
      position:fixed; left:0; bottom:0; width:1px; height:1px;
      overflow:hidden; opacity:0; pointer-events:none; z-index:-1;
    }
    .music-dock[hidden] { display:none !important; }
    .music-dock .yt-bgm {
      width:1px; height:1px; border:0; opacity:0;
      position:static; pointer-events:none;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <a class="back" href="/">← 返回首页</a>
    ${meta ? `<p class="meta">${esc(meta)}</p>` : ""}
    <h1>${esc(title)}</h1>
    ${subLine ? `<p class="sub">${esc(subLine)}</p>` : ""}
    <div class="line" aria-hidden="true"></div>
    <article class="prose">
${renderProse(data.c, params.id, imageCount)}${renderBottomGallery(params.id, bottomIndices)}    </article>
    <div class="cta">
      <a href="/">浏览公开售后</a>
      <a href="/create/?id=${esc(params.id)}">编辑此信</a>
      <a href="/create/">我也要写一封</a>
    </div>
  </div>
${musicBlock}
</body>
</html>`;

  return new Response(html, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "public, max-age=60",
    },
  });
}
