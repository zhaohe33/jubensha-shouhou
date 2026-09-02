const MARKER_RE = /\[图\s*(\d+)\s*\]/g;
const MARKER_TEST_RE = /\[图\s*\d+\s*\]/;

export function hasInlineImageMarkers(content) {
  return MARKER_TEST_RE.test(String(content || ""));
}

export function getUsedImageIndices(content) {
  const used = new Set();
  const text = String(content || "");
  for (const m of text.matchAll(MARKER_RE)) {
    const n = Number(m[1]);
    if (n >= 1) used.add(n - 1);
  }
  return used;
}

export function getUnmarkedImageIndices(content, imageCount) {
  if (!imageCount) return [];
  const all = Array.from({ length: imageCount }, (_, i) => i);
  if (!hasInlineImageMarkers(content)) return all;
  const used = getUsedImageIndices(content);
  return all.filter((i) => !used.has(i));
}

/** @deprecated use getUnmarkedImageIndices */
export const getSidebarImageIndices = getUnmarkedImageIndices;

export function parseMarkerIndex(part) {
  const m = String(part).match(/^\[图\s*(\d+)\s*\]$/);
  return m ? Number(m[1]) - 1 : -1;
}

export function splitContentParts(content) {
  return String(content || "").split(/(\[图\s*\d+\s*\])/);
}
