import { json, requireAdmin } from "../../_lib/admin.js";
import { getSiteViews, listStaticViews } from "../../_lib/analytics.js";

export async function onRequestGet(context) {
  const auth = requireAdmin(context.request, context.env);
  if (auth.error) return auth.error;

  const staticViews = await listStaticViews(context.env);
  const staticReads = Object.values(staticViews).reduce((sum, n) => sum + n, 0);

  return json({
    siteViews: await getSiteViews(context.env),
    staticViews,
    staticReads,
  });
}
