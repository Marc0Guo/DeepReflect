# Vibe Roast (Cursor Agent Skill)

Playful **Vibe Roast** HTML from AI chat history. Let your agent roast your vibe anything behavior!

## Ask before extract

When you run the skill, the agent **will always ask** how you want to extract the memory. You have three options:

| Choice | Source | Cost |
|--------|--------|--------|
| **1** | **Current chat / agent memory** — thread context (no disk scan) | 💰 |
| **2** | **Cursor** — `extract_cursor.py` | 💰💰💰 |
| **3** | **Claude Code** — `extract_claude.py` |💰💰💰|

```bash
# only if user choose 2 or 3
python3 skills/chat-history-roast/scripts/extract_cursor.py --limit 50
python3 skills/chat-history-roast/scripts/extract_claude.py --limit 30
```

`--limit` recommend **20–80**. Extract all will consume A LOT of tokens.

## Demo

- [中文 sample](./examples/sample/roast-report.zh.html)
- [English sample](./examples/sample/roast-report.en.html)

## Install

From any project root (with `.git` or `.cursor`):

```bash
npm install deepreflect-chat-history-roast-skill
```

`postinstall` copies the skill to `.cursor/skills/chat-history-roast/`.

```bash
npx chat-history-roast-skill install
```