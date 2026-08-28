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

  return {
    preset: presetKey,
    bg: clampHex(raw.bg, base.bg),
    text: clampHex(raw.text, base.text),
    textSoft: clampHex(raw.textSoft, base.textSoft),
    accent: clampHex(raw.accent, base.accent),
    glow: base.glow,
    font: fontKey,
  };
}

export function themeFontLink(theme) {
  const body = FONTS[theme.font] || FONTS.serif;
  return `https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&${body.link}&display=swap`;
}

export function themeCss(theme) {
  const t = normalizeTheme(theme);
  const bodyFont = FONTS[t.font]?.body || FONTS.serif.body;
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
    }
    body {
      font-family: ${bodyFont};
      color: var(--paper);
      background: var(--ink);
    }
    body::before {
      background:
        radial-gradient(ellipse 80% 55% at 12% 8%, var(--glow), transparent 55%),
        linear-gradient(180deg, color-mix(in srgb, var(--ink) 92%, #000) 0%, var(--ink) 50%, color-mix(in srgb, var(--ink) 88%, #000) 100%);
    }
    .meta { color: var(--meta); }
    h1 { font-family: "Ma Shan Zheng", cursive; }
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
