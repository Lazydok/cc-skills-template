#!/usr/bin/env node
/**
 * gpt-image generate — text → image via ChatGPT subscription OAuth proxy.
 * Usage:
 *   node generate.js --prompt "a cat" [--quality medium] [--size 1024x1024] [--n 2] [--format png] [--out-dir ./images]
 */
import { spawn, execSync } from "child_process";
import { writeFile, mkdir, readFile } from "fs/promises";
import { existsSync } from "fs";
import { join, dirname, isAbsolute } from "path";
import { fileURLToPath } from "url";
import { validateImage } from "./verify.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OAUTH_PORT = 10531;
const OAUTH_URL = `http://127.0.0.1:${OAUTH_PORT}`;
const CONFIG_PATH = join(__dirname, "..", "config.json");
const HISTORY_PATH = join(__dirname, "..", "history.jsonl");

async function loadConfig() {
  if (existsSync(CONFIG_PATH)) {
    try { return JSON.parse(await readFile(CONFIG_PATH, "utf-8")); } catch {}
  }
  return {};
}

async function logHistory(entry) {
  const line = JSON.stringify({ timestamp: new Date().toISOString(), ...entry }) + "\n";
  await writeFile(HISTORY_PATH, line, { flag: "a" });
}

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = { prompt: "", quality: "", size: "", n: "1", format: "", "out-dir": "" };
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    const val = args[i + 1];
    if (key in parsed) parsed[key] = val;
  }
  if (!parsed.prompt) {
    console.error("Usage: node generate.js --prompt <text> [--quality low|medium|high] [--size 1024x1024|1024x1536|1536x1024] [--n 1-8] [--format png|jpeg|webp] [--out-dir <dir>]");
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
  console.error("Run this command in your own terminal (requires browser login):");
  console.error("  npx @openai/codex login");
  console.error("");
  console.error("This authenticates you using your ChatGPT Plus/Pro subscription.");
  console.error("After logging in, retry.");
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

    if (attempt > 1) {
      console.log(`[gpt-image] Clearing port ${OAUTH_PORT}...`);
      killProxyOnPort();
      await new Promise(r => setTimeout(r, 1000));
    }

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

    const ready = await healthCheck(30);
    if (ready) {
      console.log(`[gpt-image] OAuth proxy ready`);
      return child;
    }

    console.error(`[gpt-image] Proxy did not respond on attempt ${attempt}`);
    child.kill();
  }

  console.error("================================================================================");
  console.error("ERROR: OAuth proxy failed to start after 3 attempts on port 10531.");
  console.error("");
  console.error("Manual fix:");
  console.error(`  1. lsof -ti:${OAUTH_PORT} | xargs kill -9`);
  console.error("  2. npx @openai/codex login");
  console.error("  3. Test: npx openai-oauth --port 10531");
  console.error("================================================================================");
  process.exit(1);
}

async function generateOne({ prompt, quality, size }) {
  const developerPrompt = `You are an image generator. Always invoke the image_generation tool; never respond with text only. Render all text and typography in the image with accurate spelling and layout. Follow the user's prompt exactly — do not add stylistic modifiers, quality keywords, or other content the user did not explicitly request.`;

  const res = await fetch(`${OAUTH_URL}/v1/responses`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      model: "gpt-5.4",
      input: [
        { role: "developer", content: developerPrompt },
        { role: "user", content: `Generate an image: ${prompt}` },
      ],
      tools: [{ type: "image_generation", quality, size }],
      tool_choice: "required",
      stream: true,
    }),
  });

  if (!res.ok) { const text = await res.text(); throw new Error(`OAuth proxy returned ${res.status}: ${text.slice(0, 200)}`); }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let imageB64 = null;
  let usage = null;

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
        if (data.type === "response.output_item.done" && data.item?.type === "image_generation_call" && data.item.result) imageB64 = data.item.result;
        if (data.type === "response.completed") usage = data.response?.usage || null;
        if (data.type === "error") throw new Error(data.error?.message || JSON.stringify(data));
      } catch (e) { if (e.message && !e.message.startsWith("Unexpected")) throw e; }
    }
  }

  if (!imageB64) {
    // Fallback: non-streaming retry once
    const retryRes = await fetch(`${OAUTH_URL}/v1/responses`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: "gpt-5.4", input: [{ role: "user", content: prompt }], tools: [{ type: "image_generation", quality, size }], stream: false }),
    });
    if (retryRes.ok) {
      const json = await retryRes.json();
      for (const item of json.output || []) if (item.type === "image_generation_call" && item.result) { imageB64 = item.result; usage = json.usage; break; }
    }
  }
  if (!imageB64) throw new Error("No image data received");
  return { b64: imageB64, usage };
}

function resolveOutDir(rawOutDir) {
  if (!rawOutDir) return join(process.cwd(), "images");
  if (isAbsolute(rawOutDir)) return rawOutDir;
  return join(process.cwd(), rawOutDir);
}

async function main() {
  const args = parseArgs();
  checkOAuthSession();
  const config = await loadConfig();

  const quality = args.quality || config.default_quality || "medium";
  const size = args.size || config.default_size || "1024x1024";
  const format = args.format || config.default_format || "png";
  const outDir = resolveOutDir(args["out-dir"] || config.output_dir);
  const count = Math.min(Math.max(parseInt(args.n) || 1, 1), 8);

  console.log(`[gpt-image] Config: quality=${quality}, size=${size}, format=${format}, n=${count}, out=${outDir}`);

  const proxy = await startOAuthProxy();
  const startTime = Date.now();

  try {
    await mkdir(outDir, { recursive: true });
    const results = await Promise.allSettled(Array.from({ length: count }, () => generateOne({ prompt: args.prompt, quality, size })));

    let saved = 0;
    let totalTokens = 0;
    const outputs = [];
    const verifiedOutputs = [];
    const failedOutputs = [];

    for (let i = 0; i < results.length; i++) {
      const r = results[i];
      if (r.status === "fulfilled" && r.value.b64) {
        const filename = `gpt-img_${Date.now()}_${i}.${format}`;
        const outPath = join(outDir, filename);
        await writeFile(outPath, Buffer.from(r.value.b64, "base64"));
        console.log(`[gpt-image] [${i + 1}/${count}] Saved: ${outPath}`);

        const verifyResult = await validateImage(outPath);
        if (verifyResult.valid) {
          console.log(`[gpt-image] [${i + 1}/${count}] ✅ Verified: ${verifyResult.png?.dimensions?.width}x${verifyResult.png?.dimensions?.height}`);
          verifiedOutputs.push(outPath);
        } else {
          console.error(`[gpt-image] [${i + 1}/${count}] ❌ Verification failed:`);
          for (const [check, passed] of Object.entries(verifyResult.checks)) if (!passed) console.error(`       - ${check}`);
          failedOutputs.push({ path: outPath, checks: verifyResult.checks });
        }

        outputs.push(outPath);
        saved++;
        if (r.value.usage?.total_tokens) totalTokens += r.value.usage.total_tokens;
      } else {
        console.error(`[gpt-image] [${i + 1}/${count}] Failed:`, r.reason?.message);
      }
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`[gpt-image] Done: ${saved}/${count} images saved in ${elapsed}s`);
    if (verifiedOutputs.length > 0) console.log(`[gpt-image] Verified: ${verifiedOutputs.length}/${saved}`);
    if (failedOutputs.length > 0) console.error(`[gpt-image] Verification failures: ${failedOutputs.length}/${saved}`);

    await logHistory({ type: "generate", prompt: args.prompt, quality, size, format, count, saved, verified: verifiedOutputs.length, outputs, total_tokens: totalTokens, elapsed });
  } catch (err) {
    console.error("[gpt-image] Error:", err.message);
    proxy.kill(); process.exit(1);
  }

  proxy.kill();
  process.exit(0);
}

main();
