import { recordHomeView, recordStaticView } from "../_lib/analytics.js";

export async function onRequestPost(context) {
  const { env } = context;
  if (!env.SHARES) {
    return new Response(null, { status: 204 });
  }

  let body = {};
  try {
    body = await context.request.json();
  } catch {
    /* empty */
  }

  const page = body.page || "home";
  if (page === "static" && body.path) {
    await recordStaticView(env, body.path);
  } else if (page === "home") {
    await recordHomeView(env);
  }

  return new Response(null, { status: 204 });
}
