export const PRESETS = {
  ink: {
    label: "墨信",
    bg: "#100e0c",
    text: "#efe6d6",
    textSoft: "#cfc3ae",
    accent: "#9c2f2a",
    glow: "rgba(120,48,40,0.18)",
  },
  paper: {
    label: "素笺",
    bg: "#f3ead8",
    text: "#2a221c",
    textSoft: "#5c5046",
    accent: "#8b3a34",
    glow: "rgba(139,58,52,0.12)",
  },
  night: {
    label: "夜雨",
    bg: "#0b1220",
    text: "#d9e4f5",
    textSoft: "#9eb0c9",
    accent: "#5b8def",
    glow: "rgba(91,141,239,0.15)",
  },
  rose: {
    label: "落樱",
    bg: "#1a1014",
    text: "#f5e3e8",
    textSoft: "#c9a3ad",
    accent: "#d45d79",
    glow: "rgba(212,93,121,0.16)",
  },
  bamboo: {
    label: "青松",
    bg: "#0f1612",
    text: "#e2efe6",
    textSoft: "#a8bfb0",
    accent: "#4f8a6b",
    glow: "rgba(79,138,107,0.16)",
  },
  candle: {
    label: "烛夜",
    bg: "#1a1408",
    text: "#f0e4cc",
    textSoft: "#c4b08a",
    accent: "#c9922e",
    glow: "rgba(201,146,46,0.14)",
  },
  mist: {
    label: "紫霭",
    bg: "#14101c",
    text: "#ebe4f8",
    textSoft: "#b5a8cc",
    accent: "#8b6cc4",
    glow: "rgba(139,108,196,0.16)",
  },
  snow: {
    label: "雪笺",
    bg: "#e8eef4",
    text: "#1e2832",
    textSoft: "#4a5a6a",
    accent: "#3d6d8c",
    glow: "rgba(61,109,140,0.1)",
  },
  tide: {
    label: "海潮",
    bg: "#0a1a1e",
    text: "#d8f0f0",
    textSoft: "#8eb8b8",
    accent: "#2a9d8f",
    glow: "rgba(42,157,143,0.15)",
  },
  wine: {
    label: "醇酒",
    bg: "#180c10",
    text: "#f2e0e4",
    textSoft: "#c49aa6",
    accent: "#9e3b4f",
    glow: "rgba(158,59,79,0.14)",
  },
};

export const FONTS = {
  serif: {
    label: "宋体",
    body: '"Noto Serif SC", "Songti SC", serif',
    link: "family=Noto+Serif+SC:wght@400;500;600;700",
  },
  kai: {
    label: "楷体",
    body: '"ZCOOL XiaoWei", "KaiTi", serif',
    link: "family=ZCOOL+XiaoWei",
  },
  song: {
    label: "明朝",
    body: '"Songti SC", "Noto Serif SC", serif',
    link: "family=Noto+Serif+SC:wght@400;500;600;700",
  },
  hand: {
    label: "手写",
    body: '"Zhi Mang Xing", cursive',
    link: "family=Zhi+Mang+Xing",
  },
  cursive: {
    label: "行草",
    body: '"Long Cang", cursive',
    link: "family=Long+Cang",
  },
  brush: {
    label: "毛笔",
    body: '"Ma Shan Zheng", cursive',
    link: "family=Ma+Shan+Zheng",
  },
  grass: {
    label: "狂草",
    body: '"Liu Jian Mao Cao", cursive',
    link: "family=Liu+Jian+Mao+Cao",
  },
  sans: {
    label: "黑体",
    body: '"Noto Sans SC", "PingFang SC", sans-serif',
    link: "family=Noto+Sans+SC:wght@400;500;700",
  },
};

export const FONT_SIZES = {
  sm: { label: "偏小", body: "0.88rem", title: "clamp(2rem, 7vw, 2.8rem)" },
  md: { label: "标准", body: "1rem", title: "clamp(2.4rem, 8vw, 3.4rem)" },
  lg: { label: "偏大", body: "1.15rem", title: "clamp(2.55rem, 8.5vw, 3.7rem)" },
  xl: { label: "很大", body: "1.32rem", title: "clamp(2.75rem, 9vw, 4.1rem)" },
};

const HEX_RE = /^#[0-9a-fA-F]{6}$/;

function clampHex(value, fallback) {
  const v = String(value || "").trim();
  return HEX_RE.test(v) ? v.toLowerCase() : fallback;
}

export function normalizeTheme(input) {
  const raw = input && typeof input === "object" ? input : {};
  const presetKey = PRESETS[raw.preset] ? raw.preset : "ink";
  const base = PRESETS[presetKey];
  const fontKey = FONTS[raw.font] ? raw.font : "serif";
  const sizeKey = FONT_SIZES[raw.size] ? raw.size : "md";

  return {
    preset: presetKey,
    bg: clampHex(raw.bg, base.bg),
    text: clampHex(raw.text, base.text),
    textSoft: clampHex(raw.textSoft, base.textSoft),
    accent: clampHex(raw.accent, base.accent),
    glow: base.glow,
    font: fontKey,
    size: sizeKey,
  };
}

export function themeFontLink(theme) {
  const body = FONTS[theme.font] || FONTS.serif;
  const families = new Set(["family=Ma+Shan+Zheng", body.link]);
  return `https://fonts.googleapis.com/css2?${[...families].join("&")}&display=swap`;
}

export function themeCss(theme) {
  const t = normalizeTheme(theme);
  const bodyFont = FONTS[t.font]?.body || FONTS.serif.body;
  const size = FONT_SIZES[t.size] || FONT_SIZES.md;
  const fade = hexToRgba(t.text, 0.55);
  const line = hexToRgba(t.text, 0.16);
  const meta = hexToRgba(t.accent, 0.85);

  return `
    :root {
      --ink: ${t.bg};
      --paper: ${t.text};
      --paper-soft: ${t.textSoft};
      --fade: ${fade};
      --seal: ${t.accent};
      --line: ${line};
      --meta: ${meta};
      --glow: ${t.glow};
      --body-size: ${size.body};
      --title-size: ${size.title};
    }
    body {
      font-family: ${bodyFont};
      font-size: ${size.body};
      color: var(--paper);
      background: var(--ink);
    }
    body::before {
      background:
        radial-gradient(ellipse 80% 55% at 12% 8%, var(--glow), transparent 55%),
        linear-gradient(180deg, color-mix(in srgb, var(--ink) 92%, #000) 0%, var(--ink) 50%, color-mix(in srgb, var(--ink) 88%, #000) 100%);
    }
    .meta { color: var(--meta); }
    h1 { font-family: "Ma Shan Zheng", cursive; font-size: var(--title-size); }
    .prose { font-size: var(--body-size); line-height: 1.9; }
    .line { background: var(--seal); }
    .cta a { color: var(--paper); border-color: ${hexToRgba(t.text, 0.35)}; }
    .cta a:hover { border-color: ${hexToRgba(t.text, 0.7)}; }
    .back { color: var(--fade); }
    .back:hover { color: var(--paper); }
  `;
}

function hexToRgba(hex, alpha) {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}
