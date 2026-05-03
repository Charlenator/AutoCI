// AutoCI inbound-email webhook receiver.
//
// PHASE: STUB — returns 200 to any request so Resend's webhook validation passes.
// Real logic (signature verification, attachment storage, queue insert) lands in Sprint B4.
//
// URL: https://orxdunrevazwpyzkoaob.supabase.co/functions/v1/inbound-email

Deno.serve(async (req: Request) => {
  const method = req.method;
  const url = new URL(req.url);

  console.log(`[inbound-email stub] ${method} ${url.pathname}${url.search}`);

  // Echo a few headers for debugging Resend's pings later.
  const interestingHeaders = ["content-type", "x-resend-signature", "user-agent"];
  for (const h of interestingHeaders) {
    const v = req.headers.get(h);
    if (v) console.log(`[inbound-email stub]   ${h}: ${v}`);
  }

  // Try to log the body if it's small (skip for production once real logic lands).
  if (method === "POST") {
    try {
      const text = await req.text();
      if (text.length < 2000) {
        console.log(`[inbound-email stub] body: ${text}`);
      } else {
        console.log(`[inbound-email stub] body (${text.length} chars): ${text.slice(0, 500)}...`);
      }
    } catch (err) {
      console.log(`[inbound-email stub] body read error: ${err}`);
    }
  }

  return new Response(
    JSON.stringify({
      status: "stub",
      message: "AutoCI inbound-email receiver is online. Real handler lands in Sprint B4.",
      received: true,
      method,
    }),
    {
      headers: { "Content-Type": "application/json" },
      status: 200,
    }
  );
});
