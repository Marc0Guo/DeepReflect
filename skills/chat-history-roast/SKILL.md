---
name: chat-history-roast
description: >-
  Vibe Roast HTML from AI chat history. CRITICAL: On invoke, ASK the user first —
  (A) agent/session memory in this chat, or (B) disk extract via extract_cursor.py /
  extract_claude.py. NEVER run extract scripts until the user chooses B and which source.
  Then analyze and generate roast-report.html (zh/en). Not an annual review deck.
---

# Vibe Roast (AI Chat History)

Standalone **Cursor Agent Skill** — for **any agent**, not tied to DeepReflect.

Playful roast → `roast-report.html`. Brand: **Vibe Roast**. Samples: `roast-report.zh.html` / `roast-report.en.html`.

---

## Step 0 — Ask first (mandatory)

When this skill is invoked, **stop and ask the user** how to load history.

**Do NOT** — on the first turn after invoke:

- run `extract_cursor.py` or `extract_claude.py`
- scan `~/.cursor`, `~/.claude`, or agent transcript folders
- assume disk extract is the default
- start generating HTML before you have a source answer

**Only skip Step 0** if the user's message **already** states the source, e.g.:

- "use this chat / agent memory"
- "extract cursor"
- "extract claude"
- they attached `history-snippet.txt` or pasted logs and said to use that

Otherwise post **one** short question (match user language):

**English:**

> **Vibe Roast — where should I read your history?**
> 1. **This chat / agent memory** — use Cursor/Claude context already in the thread (no disk scan, saves tokens)
> 2. **Local Cursor** — run `extract_cursor.py` (slower, scans machine)
> 3. **Claude Code** — run `extract_claude.py` (`~/.claude/projects`)
>
> Reply with `1`, `2`, or `3` (optional: `--limit 50`). You can also paste a snippet instead.

**中文:**

> **Vibe Roast — 聊天记录从哪来？**
> 1. **当前对话 / agent 记忆** — 用本线程里已有的 Cursor/Claude 上下文（不扫盘，省 token）
> 2. **本机 Cursor** — 跑 `extract_cursor.py`（较慢）
> 3. **Claude Code** — 跑 `extract_claude.py`（`~/.claude`）
>
> 回复 `1` / `2` / `3`（可选 `--limit`，默认 50）。也可以直接贴一段记录。

Wait for the answer. Then continue to Step 1.

---

## Step 1 — Load history (after user chooses)

| User choice | Action |
|-------------|--------|
| **1 — agent memory** | Roast from this thread: prior turns, pasted logs, @ files. **No extract scripts.** |
| **2 — Cursor disk** | `python3 …/extract_cursor.py --limit N` (default 50, suggest 20–80) |
| **3 — Claude disk** | `python3 …/extract_claude.py --limit N` |
| **Pasted snippet** | Use paste directly; no extract unless they also ask for disk |

**Memory** = what the agent already sees in the session — not DeepReflect DB, not auto-scan.

**Never** run cursor + claude extract in one roast unless the user explicitly asks for both (keep each `--limit` small).

Extract commands (only after choice 2 or 3):

```bash
python3 skills/chat-history-roast/scripts/extract_cursor.py --limit 50
python3 skills/chat-history-roast/scripts/extract_claude.py --limit 50
```

---

## Step 2 — Analyze

Find real patterns: debug loops, framework tourism, 2am prompts, "just fix it", chaotic quotes. No placeholder jokes.

---

## Step 3 — Generate HTML

Follow [`recipes/roast-report.md`](./recipes/roast-report.md) → `roast-report.html` (zh or en; both if asked). `#report-page` + html2canvas PNG export.

---

## Step 4 — Done

`open roast-report.html` (or `.zh.html` / `.en.html`).

Optional: `git log`, TODOs, terminal snippets.

---

## Install (npm)

```bash
npm install deepreflect-chat-history-roast-skill
```

Extract scripts: stdlib Python 3 (`scripts/sources/`).

---

## Quality bar

- **Ask before extract** every time unless source was explicit in the invoke message.
- Specific > generic; match sample by locale.
- Brand **Vibe Roast**; Chinese = more 梗.
- html2canvas-safe `<em>` highlights; `await document.fonts.ready`.
