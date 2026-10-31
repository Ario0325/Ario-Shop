/**
 * Ario Shop - Cloudflare Worker Proxy
 *
 * PythonAnywhere free plan blocks outbound HTTP to n8n.cloud.
 * Django sends requests here, this worker forwards them to n8n.
 *
 * Routes:
 *   POST /webhook/new-order-notify   -> n8n /webhook/new-order-notify
 *
 *   POST /webhook/django-auth-event  -> n8n /webhook/django-auth-event
 *   POST /webhook/order-paid         -> n8n /webhook/order-paid
 *   GET  /                           -> health check
 */

const N8N_BASE_URL = "https://aryashopai.app.n8n.cloud";

const ALLOWED_PATHS = ["/webhook/django-auth-event", "/webhook/order-paid", "/webhook/new-order-notify"];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Health check
    if (request.method === "GET" && (path === "/" || path === "/health")) {
      return new Response(
        JSON.stringify({ status: "ok", timestamp: new Date().toISOString() }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    // Only POST for webhooks
    if (request.method !== "POST") {
      return new Response(
        JSON.stringify({ error: "Method not allowed" }),
        { status: 405, headers: { "Content-Type": "application/json" } }
      );
    }

    // Validate path
    if (!ALLOWED_PATHS.includes(path)) {
      return new Response(
        JSON.stringify({ error: "Not found", allowed: ALLOWED_PATHS }),
        { status: 404, headers: { "Content-Type": "application/json" } }
      );
    }

    // Build upstream URL
    const upstreamUrl = `${N8N_BASE_URL}${path}`;

    // Forward request to n8n preserving method, headers, body
    const upstreamRequest = new Request(upstreamUrl, {
      method: request.method,
      headers: filterHeaders(request.headers),
      body: request.body,
      redirect: "follow",
    });

    try {
      const response = await fetch(upstreamRequest);

      // Return n8n response to Django
      const responseHeaders = new Headers(response.headers);
      responseHeaders.set("Access-Control-Allow-Origin", "*");

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    } catch (err) {
      return new Response(
        JSON.stringify({
          error: "Upstream fetch failed",
          message: err.message,
          upstream: upstreamUrl,
        }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  },
};

function filterHeaders(headers) {
  const forwarded = new Headers();
  const skip = new Set([
    "host", "connection", "keep-alive", "transfer-encoding",
    "te", "trailer", "upgrade",
  ]);
  for (const [key, value] of headers) {
    if (!skip.has(key.toLowerCase())) {
      forwarded.set(key, value);
    }
  }
  return forwarded;
}
