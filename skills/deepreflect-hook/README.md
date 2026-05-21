# DeepReflect Auto-Tag Hook

Captures every AI conversation turn into your DeepReflect database — **no second LLM call needed**.
Claude tags the turn itself (it just answered the question, it knows the topics).

## Platform support

| Tool | Supported | Hook event | Notes |
|------|-----------|------------|-------|
| **Cursor** | ✅ | `stop` | `.cursor/hooks.json` |
| **Claude Code** | ✅ | `Stop` | `.claude/settings.json` + reads `transcript_path` directly |

---

## How it works

```
You ask Claude something
        ↓
Claude answers, appending one invisible HTML comment at the very end:
  <!-- dr:{"t":["react hooks","typescript generics"],"d":"web"} -->
        ↓
stop/Stop hook fires → dr-turn.py reads the turn + parses the tag
        ↓
POST /ingest/raw-turn  { user_prompt, ai_response, topics, domain }
        ↓
DeepReflect stores the turn as analyzed=True immediately
Knowledge Graph updates on next visit
```

The `<!-- dr:... -->` tag is invisible in rendered markdown.
Claude picks the topics itself — no second API call needed.

---

## Installation

### Cursor

Copy three files into your project root (or into `~/.cursor/` to apply globally):

```
your-project/
  .cursor/
    hooks.json                         ← cursor/hooks.json
    hooks/
      dr-turn.py                       ← cursor/hooks/dr-turn.py
    rules/
      deepreflect-auto-tag.mdc         ← cursor/rules/deepreflect-auto-tag.mdc
```

Then **restart Cursor**.

### Claude Code

```
your-project/
  .claude/
    settings.json                      ← claude-code/settings.json
    hooks/
      dr-turn.py                       ← claude-code/hooks/dr-turn.py
    rules/
      deepreflect-auto-tag.md          ← claude-code/rules/deepreflect-auto-tag.md
```

Or use the global path `~/.claude/` to apply to all projects.
Run `claude hooks` in your terminal to verify the hook is registered.

### Global (one-time, applies everywhere)

```bash
# Cursor
mkdir -p ~/.cursor/hooks ~/.cursor/rules
cp cursor/hooks/dr-turn.py     ~/.cursor/hooks/
cp cursor/rules/*.mdc          ~/.cursor/rules/
cp cursor/hooks.json           ~/.cursor/hooks.json

# Claude Code
mkdir -p ~/.claude/hooks ~/.claude/rules
cp claude-code/hooks/dr-turn.py        ~/.claude/hooks/
cp claude-code/rules/*.md              ~/.claude/rules/
# merge claude-code/settings.json into ~/.claude/settings.json
```

---

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `DR_URL` | `http://localhost:8000` | DeepReflect base URL |

```bash
export DR_URL="http://localhost:9000"   # if you run DeepReflect on a different port
```

---

## Requirements

- `python3` on PATH — uses **stdlib only**, no `pip install` needed
- DeepReflect running locally (the hook is completely silent when it is not)

---

## How tags enter the Knowledge Graph

1. `ConversationTurn` stored (upsert — safe to re-submit the same turn)
2. Each topic upserted as a `Concept` with the given domain category
3. `ConceptMention` links created (turn ↔ concept)
4. Domain hub links backfilled
5. Turn marked `analyzed=True`

If Claude omitted the tag (non-technical turn), the turn is stored unanalyzed
and can be processed later via **Analyze** in the DeepReflect UI.
