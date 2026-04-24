#!/usr/bin/env node
/**
 * gpt-image edit — image → image (restyle / transform) via ChatGPT subscription OAuth proxy.
 * Usage:
 *   node edit.js --input photo.png --prompt "pen sketch" [--quality high] [--size 1024x1536] [--format png] --out result.png
 */
import { spawn, execSync } from "child_process";
import { writeFile, readFile, mkdir } from "fs/promises";
import { existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { validateImage } from "./verify.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OAUTH_PORT = 10531;
const OAUTH_URL = `http://127.0.0.1:${OAUTH_PORT}`;
const CONFIG_PATH = join(__dirname, "..", "config.json");
const HISTORY_PATH = join(__dirname, "..", "history.jsonl");

async function loadConfig() {
  if (existsSync(CONFIG_PATH)) { try { return JSON.parse(await readFile(CONFIG_PATH, "utf-8")); } catch {} }
  return {};
}

async function logHistory(entry) {
  const line = JSON.stringify({ timestamp: new Date().toISOString(), ...entry }) + "\n";
  await writeFile(HISTORY_PATH, line, { flag: "a" });
}

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = { input: "", prompt: "", quality: "", size: "", format: "", out: "" };
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, ""); const val = args[i + 1];
    if (key in parsed) parsed[key] = val;
  }
  if (!parsed.input || !parsed.prompt || !parsed.out) {
    console.error("Usage: node edit.js --input <img> --prompt <desc> [--quality low|medium|high] [--size 1024x1024|1024x1536|1536x1024] [--format png|jpeg|webp] --out <file>");
    process.exit(1);
  }
  return parsed;
}

function checkOAuthSession() {
  const paths = [join(process.env.HOME, ".codex", "auth.json"), join(process.env.HOME, ".chatgpt-local", "auth.json")];
  for (const p of paths) if (existsSync(p)) return true;
  console.error("================================================================================");
  console.error("ERROR: No OAuth session found.");
  console.error("");
  console.error("Run in your own terminal (needs browser): npx @openai/codex login");
  console.error("================================================================================");
  process.exit(1);
}

function killProxyOnPort() {
  try {
    execSync(`lsof -ti:${OAUTH_PORT} | xargs kill -9 2>/dev/null`, { stdio: "ignore" });
  } catch {}
}

async function healthCheck(maxAttempts) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const r = await fetch(`${OAUTH_URL}/v1/models`, { signal: AbortSignal.timeout(1000) });
      if (r.ok) return true;
    } catch {}
    await new Promise(r => setTimeout(r, 500));
  }
  return false;
}

async function startOAuthProxy(maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    console.log(`[gpt-image] Starting OAuth proxy (attempt ${attempt}/${maxRetries})...`);
    if (attempt > 1) { killProxyOnPort(); await new Promise(r => setTimeout(r, 1000)); }

    const child = spawn("npx", ["openai-oauth", "--port", String(OAUTH_PORT)], { stdio: ["ignore", "pipe", "pipe"], env: { ...process.env } });
    child.stdout.on("data", d => { const m = d.toString().trim(); if (m) console.log(`[oauth] ${m}`); });
    child.stderr.on("data", d => {
      const m = d.toString().trim();
      if (!m) return;
      if (m.includes("npm warn") || m.includes("npm notice") || m.includes("ExperimentalWarning") || /^\(node:\d+\)/.test(m)) return;
      console.error(`[oauth] ${m}`);
    });
    child.on("error", err => console.error(`[oauth] Process error: ${err.message}`));
    child.on("exit", code => { if (code !== 0 && code !== null) console.error(`[oauth] Proxy exited with code ${code}`); });

    if (await healthCheck(30)) { console.log(`[gpt-image] OAuth proxy ready`); return child; }
    console.error(`[gpt-image] Proxy did not respond on attempt ${attempt}`);
    child.kill();
  }
  console.error("ERROR: OAuth proxy failed. Try: lsof -ti:10531 | xargs kill -9 && npx @openai/codex login");
  process.exit(1);
}

async function editImage({ input, prompt, quality, size }) {
  const imageBuffer = await readFile(input);
  const imageB64 = imageBuffer.toString("base64");
  const developerPrompt = `You are an image editor. Always invoke the image_generation tool; never respond with text only. Preserve the original image's composition, subject, and pose while applying the requested transformation. Render all text and typography with accurate spelling and layout. Follow the user's prompt exactly — do not add stylistic modifiers, quality keywords, or other content the user did not explicitly request.`;

  const res = await fetch(`${OAUTH_URL}/v1/responses`, {
    method: "POST", headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      model: "gpt-5.4",
      input: [
        { role: "developer", content: developerPrompt },
        { role: "user", content: [{ type: "input_image", image_url: `data:image/png;base64,${imageB64}` }, { type: "input_text", text: `Transform this image: ${prompt}` }] },
      ],
      tools: [{ type: "image_generation", quality, size }], tool_choice: "required", stream: true,
    }),
  });
  if (!res.ok) { const text = await res.text(); throw new Error(`OAuth proxy returned ${res.status}: ${text.slice(0, 200)}`); }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "", resultB64 = null, usage = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, boundary); buffer = buffer.slice(boundary + 2);
      let eventData = "";
      for (const line of block.split("\n")) if (line.startsWith("data: ")) eventData += line.slice(6);
      if (!eventData || eventData === "[DONE]") continue;
      try {
        const data = JSON.parse(eventData);
        if (data.type === "response.output_item.done" && data.item?.type === "image_generation_call" && data.item.result) resultB64 = data.item.result;
        if (data.type === "response.completed") usage = data.response?.usage || null;
        if (data.type === "error") throw new Error(data.error?.message || JSON.stringify(data));
      } catch (e) { if (e.message && !e.message.startsWith("Unexpected")) throw e; }
    }
  }
  if (!resultB64) {
    const retryRes = await fetch(`${OAUTH_URL}/v1/responses`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: "gpt-5.4", input: [{ type: "input_image", image_url: `data:image/png;base64,${imageB64}` }, { type: "input_text", text: prompt }], tools: [{ type: "image_generation", quality, size }], stream: false }),
    });
    if (retryRes.ok) {
      const json = await retryRes.json();
      for (const item of json.output || []) if (item.type === "image_generation_call" && item.result) { resultB64 = item.result; usage = json.usage; break; }
    }
  }
  if (!resultB64) throw new Error("No image data received from OAuth proxy");
  return { b64: resultB64, usage };
}

async function main() {
  const args = parseArgs();
  checkOAuthSession();
  const config = await loadConfig();

  const quality = args.quality || config.default_quality || "medium";
  const size = args.size || config.default_size || "1024x1024";
  const format = args.format || config.default_format || "png";

  if (!existsSync(args.input)) { console.error(`ERROR: Input file not found: ${args.input}`); process.exit(1); }

  const proxy = await startOAuthProxy();
  const startTime = Date.now();

  try {
    const result = await editImage({ input: args.input, prompt: args.prompt, quality, size });
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

    let outPath = args.out;
    if (!outPath.endsWith(`.${format}`)) outPath = outPath.replace(/\.[^.]+$/, `.${format}`);
    await mkdir(dirname(outPath), { recursive: true });
    await writeFile(outPath, Buffer.from(result.b64, "base64"));

    console.log(`[gpt-image] Saved: ${outPath} (${elapsed}s)`);

    const verifyResult = await validateImage(outPath);
    if (verifyResult.valid) {
      console.log(`[gpt-image] ✅ Verified: ${verifyResult.png?.dimensions?.width}x${verifyResult.png?.dimensions?.height}`);
    } else {
      console.error(`[gpt-image] ❌ Verification failed:`);
      for (const [check, passed] of Object.entries(verifyResult.checks)) if (!passed) console.error(`       - ${check}`);
    }

    if (result.usage) console.log("[gpt-image] Usage:", JSON.stringify(result.usage));

    await logHistory({ type: "edit", input: args.input, prompt: args.prompt, quality, size, format, output: outPath, verified: verifyResult.valid, total_tokens: result.usage?.total_tokens || 0, elapsed });
  } catch (err) {
    console.error("[gpt-image] Error:", err.message);
    console.error("       Hint: 401/403 means your OAuth session expired — re-run `npx @openai/codex login`.");
    console.error("       429/rate-limit means you hit the subscription cap — wait and retry.");
    proxy.kill(); process.exit(1);
  }
  proxy.kill();
  process.exit(0);
}

main();
