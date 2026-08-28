import { json, listAllShares, requireAdmin } from "../../_lib/admin.js";

export async function onRequestGet(context) {
  const auth = requireAdmin(context.request, context.env);
  if (auth.error) return auth.error;

  const origin = new URL(context.request.url).origin;
  const items = await listAllShares(context.env, origin);
  return json({ total: items.length, items });
}
