/**
 * Ario Shop - Cloudflare Worker Proxy
 *
 * PythonAnywhere free plan blocks outbound HTTP to n8n.cloud.
 * Django sends requests here, this worker forwards them to n8n.
 *
 * Security:
 *   - Every webhook call must carry X-Worker-Secret matching WORKER_SHARED_SECRET.
 *   - The n8n webhook secret is injected by the Worker, never trusted from caller.
 *   - Only JSON bodies up to 64 KB are forwarded.
 *   - No CORS headers are returned: this endpoint is server-to-server only.
 *
 * Routes:
 *   POST /webhook/new-order-notify   -> n8n /webhook/new-order-notify
 *   POST /webhook/django-auth-event  -> n8n /webhook/django-auth-event
 *   POST /webhook/order-paid         -> n8n /webhook/order-paid
 *   GET  /                           -> health check
 */

const N8N_BASE_URL = "https://aryashopai.app.n8n.cloud";

const ALLOWED_PATHS = [
  "/webhook/django-auth-event",
  "/webhook/order-paid",
  "/webhook/new-order-notify",
];

const MAX_BODY_BYTES = 64 * 1024;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Health check
    if (request.method === "GET" && (path === "/" || path === "/health")) {
      return json({ status: "ok", timestamp: new Date().toISOString() }, 200);
    }

    if (request.method !== "POST") {
      return json({ error: "Method not allowed" }, 405);
    }

    if (!ALLOWED_PATHS.includes(path)) {
      return json({ error: "Not found" }, 404);
    }

    // Fail closed if the Worker was deployed without its shared secret.
    const expectedSecret = env.WORKER_SHARED_SECRET || "";
    if (!expectedSecret) {
      return json({ error: "Worker is not configured" }, 500);
    }

    const providedSecret = request.headers.get("X-Worker-Secret") || "";
    if (!timingSafeEqual(providedSecret, expectedSecret)) {
      return json({ error: "Unauthorized" }, 401);
    }

    const contentType = request.headers.get("Content-Type") || "";
    if (!contentType.toLowerCase().startsWith("application/json")) {
      return json({ error: "Unsupported media type" }, 415);
    }

    const body = await request.arrayBuffer();
    if (body.byteLength > MAX_BODY_BYTES) {
      return json({ error: "Payload too large" }, 413);
    }

    const headers = new Headers({
      "Content-Type": "application/json",
      Accept: "application/json",
    });
    if (env.N8N_WEBHOOK_SECRET) {
      headers.set("X-Webhook-Secret", env.N8N_WEBHOOK_SECRET);
    }

    const upstreamUrl = `${N8N_BASE_URL}${path}`;

    try {
      const response = await fetch(upstreamUrl, {
        method: "POST",
        headers,
        body,
        redirect: "follow",
      });

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: { "Content-Type": response.headers.get("Content-Type") || "application/json" },
      });
    } catch (err) {
      // Do not leak upstream URL or internal error details.
      console.error("upstream fetch failed", err && err.message);
      return json({ error: "Upstream unavailable" }, 502);
    }
  },
};

function json(payload, status) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function timingSafeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  const encoder = new TextEncoder();
  const aBytes = encoder.encode(a);
  const bBytes = encoder.encode(b);
  if (aBytes.length !== bBytes.length) return false;

  let diff = 0;
  for (let i = 0; i < aBytes.length; i += 1) {
    diff |= aBytes[i] ^ bBytes[i];
  }
  return diff === 0;
}
