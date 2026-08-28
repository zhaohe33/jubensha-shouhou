import { json, listAllShares, requireAdmin } from "../../_lib/admin.js";

export async function onRequestGet(context) {
  const auth = requireAdmin(context.request, context.env);
  if (auth.error) return auth.error;

  const origin = new URL(context.request.url).origin;
  const items = await listAllShares(context.env, origin);
  const publicCount = items.filter((i) => i.public).length;
  const withImages = items.filter((i) => i.imageCount > 0).length;
  const scripts = new Set(items.map((i) => i.script).filter(Boolean));

  return json({
    total: items.length,
    publicCount,
    privateCount: items.length - publicCount,
    withImages,
    scriptCount: scripts.size,
    latest: items[0]?.created || null,
  });
}
