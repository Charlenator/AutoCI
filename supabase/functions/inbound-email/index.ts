// AutoCI inbound-email webhook receiver — Sprint B4.
//
// Decoupled-pipeline design:
//   1. Verify the Resend / Svix webhook signature (best-effort; skipped if no secret configured).
//   2. Dedup on svix-id.
//   3. Upload the first attachment to the cv-attachments storage bucket.
//   4. INSERT into inbound_emails with status='pending'.
//   5. Return 200 to Resend (sub-second response).
//
// All heavy work — CV classification, extraction, confidentiality, vectorization —
// lives in the Modal Python worker (Sprint B5+) which polls / is triggered to
// process status='pending' rows.
//
// URL: https://orxdunrevazwpyzkoaob.supabase.co/functions/v1/inbound-email
//
// Environment expected (set via Supabase dashboard → Edge Functions → Secrets):
//   - RESEND_WEBHOOK_SECRET (whsec_...)  — optional; signature check is skipped if missing.
//   - SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY are auto-injected by Supabase.

import { createClient } from "npm:@supabase/supabase-js@2";

interface ResendInboundAttachment {
  filename?: string;
  contentType?: string;
  content?: string;        // base64
  size?: number;
}

interface ResendInboundPayload {
  type?: string;
  created_at?: string;
  data?: {
    from?: string | { email?: string; name?: string };
    to?: string | string[] | { email?: string; name?: string }[];
    subject?: string;
    html?: string;
    text?: string;
    attachments?: ResendInboundAttachment[];
    headers?: Record<string, string>;
  };
}

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_KEY =
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ??
  Deno.env.get("SUPABASE_SERVICE_KEY") ??
  "";
const WEBHOOK_SECRET = Deno.env.get("RESEND_WEBHOOK_SECRET") ?? "";

const ATTACHMENT_BUCKET = "cv-attachments";

const supabase = createClient(SUPABASE_URL, SERVICE_KEY, {
  auth: { persistSession: false },
});

Deno.serve(async (req: Request) => {
  const t0 = Date.now();
  if (req.method !== "POST") {
    return json({ error: "method not allowed" }, 405);
  }

  const svixId = req.headers.get("svix-id") ?? req.headers.get("webhook-id") ?? null;
  const svixTs = req.headers.get("svix-timestamp") ?? req.headers.get("webhook-timestamp") ?? null;
  const svixSig = req.headers.get("svix-signature") ?? req.headers.get("webhook-signature") ?? null;

  // Read body once. We need it for signature verification + JSON parsing.
  const rawBody = await req.text();

  // ---- Signature verification (best effort) --------------------------------
  if (WEBHOOK_SECRET && svixId && svixTs && svixSig) {
    const ok = await verifySvixSignature(WEBHOOK_SECRET, svixId, svixTs, rawBody, svixSig);
    if (!ok) {
      console.warn(`[inbound-email] signature verification FAILED svix-id=${svixId}`);
      return json({ error: "invalid signature" }, 401);
    }
    console.log(`[inbound-email] signature OK svix-id=${svixId}`);
  } else if (WEBHOOK_SECRET) {
    console.warn("[inbound-email] missing svix-* headers; signature check skipped");
  } else {
    console.warn("[inbound-email] RESEND_WEBHOOK_SECRET not set; signature check skipped");
  }

  // ---- Dedup on svix-id ----------------------------------------------------
  if (svixId) {
    const { data: existing } = await supabase
      .from("inbound_emails")
      .select("id")
      .eq("svix_id", svixId)
      .maybeSingle();
    if (existing) {
      console.log(`[inbound-email] duplicate svix-id, returning existing row ${existing.id}`);
      return json({ status: "duplicate", id: existing.id }, 200);
    }
  }

  // ---- Parse payload --------------------------------------------------------
  let payload: ResendInboundPayload;
  try {
    payload = JSON.parse(rawBody);
  } catch (err) {
    console.warn(`[inbound-email] body is not JSON: ${err}`);
    return json({ error: "invalid json" }, 400);
  }

  const email = payload.data ?? {};
  const sender = normalizeAddress(email.from);
  const recipient = normalizeAddress(email.to);
  const subject = email.subject ?? "";
  const bodyText = email.text ?? "";
  const bodyHtml = email.html ?? "";
  const dedupHash = await sha256Hex(`${sender}::${subject}`);

  // ---- Attachment upload (POC handles the first attachment only) -----------
  let attachmentPath: string | null = null;
  let attachmentMime: string | null = null;
  let attachmentName: string | null = null;
  let attachmentSize: number | null = null;
  const firstAttachment = (email.attachments ?? []).find(
    (a) => a && (a.content || (a as any).path),
  );

  if (firstAttachment && firstAttachment.content) {
    try {
      const bytes = base64ToUint8Array(firstAttachment.content);
      const safeName = sanitizeFilename(firstAttachment.filename ?? "attachment.bin");
      const path = `${new Date().toISOString().slice(0, 10)}/${crypto.randomUUID()}_${safeName}`;
      const upload = await supabase.storage.from(ATTACHMENT_BUCKET).upload(path, bytes, {
        contentType: firstAttachment.contentType ?? "application/octet-stream",
        upsert: false,
      });
      if (upload.error) {
        console.warn(`[inbound-email] storage upload failed: ${upload.error.message}`);
      } else {
        attachmentPath = path;
        attachmentMime = firstAttachment.contentType ?? null;
        attachmentName = firstAttachment.filename ?? null;
        attachmentSize = firstAttachment.size ?? bytes.length;
      }
    } catch (err) {
      console.warn(`[inbound-email] failed to decode/upload attachment: ${err}`);
    }
  }

  // ---- Queue the row -------------------------------------------------------
  const insertResp = await supabase
    .from("inbound_emails")
    .insert({
      svix_id: svixId,
      status: "pending",
      sender,
      recipient,
      subject,
      body_text: bodyText,
      body_html: bodyHtml,
      attachment_filename: attachmentName,
      attachment_storage_path: attachmentPath,
      attachment_mime: attachmentMime,
      attachment_size: attachmentSize,
      dedup_hash: dedupHash,
      raw_webhook_payload: payload,
    })
    .select("id")
    .single();

  if (insertResp.error) {
    console.error(`[inbound-email] insert failed: ${insertResp.error.message}`);
    return json({ error: "insert failed", detail: insertResp.error.message }, 500);
  }

  const inboundId = insertResp.data?.id;
  console.log(
    `[inbound-email] queued id=${inboundId} sender=${sender} subject="${subject}" attachment=${attachmentPath ?? "<none>"} (${
      Date.now() - t0
    }ms)`,
  );

  return json({ status: "queued", id: inboundId, attachment_path: attachmentPath }, 200);
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function json(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function normalizeAddress(value: unknown): string {
  if (!value) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map((v) => normalizeAddress(v)).filter(Boolean).join(", ");
  if (typeof value === "object") {
    const v = value as { email?: string; name?: string };
    return v.email ?? "";
  }
  return String(value);
}

function sanitizeFilename(name: string): string {
  return name.replace(/[^\w\-. ]+/g, "_").slice(0, 200);
}

function base64ToUint8Array(b64: string): Uint8Array {
  const cleaned = b64.replace(/\s+/g, "");
  const binary = atob(cleaned);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function sha256Hex(text: string): Promise<string> {
  const buf = new TextEncoder().encode(text);
  const hashBuf = await crypto.subtle.digest("SHA-256", buf);
  return [...new Uint8Array(hashBuf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function verifySvixSignature(
  secret: string,
  svixId: string,
  svixTimestamp: string,
  body: string,
  signatureHeader: string,
): Promise<boolean> {
  // Svix-style signing: HMAC-SHA256 over `${id}.${timestamp}.${body}`, key = decoded(secret).
  // The header is space-separated `v1,base64sig v2,base64sig` — we accept any v1 that matches.
  const secretClean = secret.startsWith("whsec_") ? secret.slice(6) : secret;
  let secretBytes: Uint8Array;
  try {
    secretBytes = base64ToUint8Array(secretClean);
  } catch {
    secretBytes = new TextEncoder().encode(secretClean);
  }
  const key = await crypto.subtle.importKey(
    "raw",
    secretBytes,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const data = new TextEncoder().encode(`${svixId}.${svixTimestamp}.${body}`);
  const sigBuf = await crypto.subtle.sign("HMAC", key, data);
  const expected = btoa(String.fromCharCode(...new Uint8Array(sigBuf)));

  for (const candidate of signatureHeader.split(/\s+/)) {
    const [scheme, sig] = candidate.split(",");
    if (scheme === "v1" && sig && timingSafeEqual(sig, expected)) return true;
  }
  return false;
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return result === 0;
}
