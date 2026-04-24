# Installation & Configuration Guide

Everything you need to do **once** before the `gpt-image` skill will work. The main `SKILL.md` stays lean; dig into this file when you need to (re)install, tweak defaults, or debug a failure.

---

## 1. Requirements

| Requirement | Why |
|-------------|-----|
| **Node.js ≥ 18** | Scripts use native `fetch`, `AbortSignal.timeout`, and ES modules. |
| **ChatGPT Plus or Pro subscription** | Image generation is billed against your ChatGPT account via the Codex OAuth proxy — no separate API key needed. |
| **`npx` available** | The scripts spawn `npx openai-oauth` to start the local proxy on first run. |

Optional: a host CLI that knows how to invoke skills (Claude Code, Kimi CLI, etc.). You can also run the scripts directly with `node`.

---

## 2. One-time authentication

The skill talks to OpenAI through a **local OAuth proxy** that reuses your ChatGPT session. You authenticate once with the Codex CLI; it writes a token file the proxy reads.

```bash
npx @openai/codex login
```

This creates `auth.json` at one of:

- `$HOME/.codex/auth.json` (preferred)
- `$HOME/.chatgpt-local/auth.json` (fallback)

Scripts auto-detect either location. If neither exists, they exit early with a message telling you to run the login command.

**When to re-run login:**
- First install.
- `401` / `403` errors from the proxy (token expired).
- You switched ChatGPT accounts.

This step is **interactive** (browser login) — Claude cannot do it for the user.

---

## 3. The OAuth proxy (auto-managed)

On every run, `generate.js` / `edit.js`:

1. Check for an OAuth session file (see above).
2. Spawn `npx openai-oauth --port 10531` as a child process.
3. Poll `http://127.0.0.1:10531/v1/models` up to 30× (500 ms each) until healthy.
4. Do the image call.
5. Kill the proxy on exit.

You should **not** need to start the proxy manually. If you do, the exact command is:

```bash
npx openai-oauth --port 10531
```

**Port:** `10531` is hardcoded. If another process holds that port, scripts will retry 3 times (clearing the port between attempts) before giving up.

---

## 4. Configuration file

`config.json` (next to `SKILL.md`) sets defaults that every CLI invocation inherits when a flag is omitted.

```json
{
  "default_quality": "medium",
  "default_size": "1024x1024",
  "default_format": "png",
  "output_dir": "./images"
}
```

| Key | Accepted values | Notes |
|-----|-----------------|-------|
| `default_quality` | `low`, `medium`, `high` | Higher = more tokens and slower. Most prompts look great at `medium`. |
| `default_size` | `1024x1024`, `1024x1536`, `1536x1024` | Square / portrait / landscape. |
| `default_format` | `png`, `jpeg`, `webp` | Output file encoding. The skill verifies PNGs; JPEG/WebP skip PNG-specific checks. |
| `output_dir` | Any path | **Relative paths resolve against the current working directory.** The default `./images` means files land in `<project-root>/images/` when you invoke from a project root. Use an absolute path for a global collection. |

Always overridable per-invocation with flags:

```bash
node scripts/generate.js --prompt "..." --quality high --size 1536x1024 --n 4 --out-dir ./renders
```

---

## 5. Output directory conventions

Results stay inside the project they were run from:

- Default `output_dir` is `./images` (relative → resolved against `process.cwd()`).
- If `output_dir` is missing from `config.json`, scripts fall back to `<cwd>/images`.
- The directory is created on demand.
- Filenames are `gpt-img_<unix-ms>_<index>.<ext>` so parallel runs don't collide.

---

## 6. History log

Every run appends a single JSON line to `history.jsonl` (next to `SKILL.md`) with prompt, settings, output paths, token usage, and elapsed time. Treat it as an audit trail, not a database — safe to delete or rotate.

If sharing this skill via git, consider `.gitignore`-ing `history.jsonl` so you don't leak prompt history.

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No OAuth session found` | `auth.json` missing. | `npx @openai/codex login` |
| `Proxy did not respond` (3× retries) | Port 10531 held by a stale process, or `openai-oauth` unreachable. | `lsof -ti:10531 \| xargs kill -9`, retry. Or install: `npm i -g openai-oauth`. |
| `OAuth proxy returned 401` / `403` | Token expired or revoked. | Re-run `npx @openai/codex login`. |
| `OAuth proxy returned 429` / `Rate limit` | Hit ChatGPT tier limit. | Wait a few minutes; reduce `--n`; drop `--quality` to `medium`. |
| `No image data received` | Stream interrupted or model refused. | Retry once. If persistent, simplify the prompt. |
| Verification failures (`pngSignature`, `ihdrPresent`) | Corrupt write, usually from an interrupted stream. | Re-run the same prompt. |
| `ENOENT` on `config.json` | Config file deleted. | Scripts tolerate a missing config — they fall back to built-in defaults. Recreate from §4 if you want persistent preferences. |

---

## 8. Uninstalling

The skill is just this folder — delete it to remove. Additionally:

- `rm -rf ~/.codex ~/.chatgpt-local` → revokes the local OAuth session.
- Nothing is installed globally unless you ran `npm i -g openai-oauth`; remove with `npm rm -g openai-oauth`.
