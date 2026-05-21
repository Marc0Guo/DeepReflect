<div align="center">

# DeepReflect

Turn your LLM and coding-agent history into a personal learning map, then use it to spot repeated questions, weak concepts, and the knowledge gaps hiding inside everyday AI usage.

[![Python >=3.11](https://img.shields.io/badge/Python-3.11%2B-3776AB)](./pyproject.toml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](./deepreflect/api/app.py)
[![React + Vite](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-646CFF)](./frontend/package.json)
[![Local First](https://img.shields.io/badge/Privacy-Local%20First-2f855a)](#privacy-model)

<p>
  <a href="#why-deepreflect">Why</a> ·
  <a href="#user-guide">User Guide</a> ·
  <a href="#agent-guide">Agent Guide</a> ·
  <a href="#privacy-model">Privacy</a>
</p>

</div>

> DeepReflect is for people who use LLMs or coding agents often enough that the same gaps start repeating. It helps you see what you keep asking, what you have already solved, and what you should learn next instead of leaving that signal buried in chat history.

DeepReflect is built for this kind of workflow:

- a user works with tools like Claude Code, ChatGPT, Cursor, Gemini, OpenCode, or local agents
- the conversations contain real evidence of what the user knows, almost knows, and keeps missing
- those traces should become a structured memory, not an endless pile of transcripts
- when the user wants to study, review, or debug their own understanding, the agent should be able to surface a graph, summary, flashcards, or intervention at the right time

<a id="why-deepreflect"></a>
## Why DeepReflect

LLMs are great at answering the next question. They are much worse at helping users notice the pattern across many questions.

DeepReflect adds a learning layer on top of AI workflows. It imports conversations, extracts concepts, tracks repeated topics, builds a knowledge graph, and turns weak areas into study material. The goal is not to slow down AI-assisted work. The goal is to make the work teach you something.

Common signals DeepReflect tracks:

- concepts you ask about repeatedly
- mistakes or confusion that recur across sessions
- topics that appear together and form a larger gap
- solved areas that show progress
- weak nodes that are good candidates for flashcards or review
- agent usage patterns that reveal what kind of help you rely on

## What It Does

DeepReflect currently includes:

- conversation import from Claude Code and local markdown / JSON files
- SQLite-backed local memory
- LLM-assisted concept extraction
- a FastAPI backend at `localhost:7733`
- a React dashboard with stats, concepts, graph, study, and summary views
- a knowledge graph that connects concepts mentioned in the same turns
- flashcard generation and export
- shareable HTML summaries for daily, weekly, monthly, or yearly review
- optional Claude Code hooks for auto-ingestion and intervention checks

Planned and post-MVP sources include ChatGPT exports, Cursor logs, Gemini exports, and OpenCode plugins.

### Cursor Agent Skills

| Skill | Description | Install |
|-------|-------------|---------|
| [chat-history-roast](./skills/chat-history-roast/) | **Vibe Roast** HTML (zh/en) for any agent; chat context or `extract_cursor` / `extract_claude` | `cd skills/chat-history-roast && npm install` |

See [`skills/chat-history-roast/README.md`](./skills/chat-history-roast/README.md) for usage with pasted Claude/Cursor/ChatGPT logs.

<a id="user-guide"></a>
## User Guide

### Installation

Requirements:

- Python `>= 3.11`
- Node.js and npm for the frontend
- an LLM API key if you want analysis, flashcards, study guides, or quizzes

Install the Python package locally:

```bash
pip install -e .
```

Install and build the frontend:

```bash
cd frontend
npm install
npm run build
cd ..
```

Start the local dashboard:

```bash
deepreflect serve
```

The default address is:

```text
http://localhost:7733
```

### Configure an LLM Provider

You can configure DeepReflect with the CLI:

```bash
deepreflect config \
  --provider openai \
  --api-key YOUR_API_KEY \
  --model gpt-4o-mini
```

Or use environment variables:

```bash
DEEPREFLECT_LLM_PROVIDER=openai
DEEPREFLECT_LLM_API_KEY=YOUR_API_KEY
DEEPREFLECT_LLM_MODEL=gpt-4o-mini
DEEPREFLECT_LLM_BASE_URL=
```

Supported provider modes:

- `openai`
- `anthropic`
- `openrouter`
- `ollama`
- any OpenAI-compatible endpoint through `--base-url` or `DEEPREFLECT_LLM_BASE_URL`

### Import Conversations

Import all available Claude Code conversations:

```bash
deepreflect import --source claude-code --all
```

Import a local folder or file:

```bash
deepreflect import ./conversations
deepreflect import ./notes/session.md
deepreflect import ./exports/conversation.json
```

Then analyze unprocessed turns:

```bash
deepreflect analyze --limit 50
```

### Review Your Learning State

Show stored metrics:

```bash
deepreflect status
```

Run the dashboard:

```bash
deepreflect serve --port 7733
```

Generate a shareable summary:

```bash
deepreflect summary --period weekly
deepreflect summary --period monthly
```

Generate and export flashcards:

```bash
deepreflect flashcards --generate --limit 10
deepreflect flashcards --format csv
deepreflect flashcards --format markdown
```

### Where Data Lives

By default, DeepReflect stores local state under:

```text
~/.deepreflect/
```

Important paths:

- `~/.deepreflect/config.json`
  local configuration written by `deepreflect config`
- `~/.deepreflect/data/deepreflect.db`
  SQLite memory database
- `~/.deepreflect/data/summaries/`
  generated HTML summary pages

Project-level `.env` files are ignored by git. Use `.env.example` as the safe template.

<a id="agent-guide"></a>
## Agent Guide

### Command Entrypoints

```bash
deepreflect --help
deepreflect config --show
deepreflect install --claude-code
deepreflect import --help
deepreflect import --source claude-code --all
deepreflect analyze --limit 50
deepreflect status
deepreflect serve
deepreflect summary --period weekly
deepreflect flashcards --generate
deepreflect check-intervention --prompt "..."
```

### Basic Rules

- prefer the CLI before reading or editing the database directly
- import first, analyze second, then generate summaries or study material
- use `status` to check whether the memory has data before creating reports
- avoid sending private conversation data to remote LLMs unless the user has configured and approved that provider
- for local-only analysis, configure `ollama` or an OpenAI-compatible local endpoint

### Typical Agent Workflow

1. Import recent conversations:

```bash
deepreflect import --source claude-code --all
```

2. Analyze the new turns:

```bash
deepreflect analyze --limit 100
```

3. Inspect the current memory:

```bash
deepreflect status
```

4. Create learning artifacts:

```bash
deepreflect summary --period weekly --no-open
deepreflect flashcards --generate --limit 15
```

5. Start the dashboard if the user wants to browse:

```bash
deepreflect serve --no-open
```

### Claude Code Hook

DeepReflect can install Claude Code hooks:

```bash
deepreflect install --claude-code
```

This writes hooks to:

```text
~/.claude/settings.json
```

Hook behavior:

- `Stop`
  imports completed Claude Code sessions into DeepReflect
- `PreToolUse`
  checks the incoming prompt against repeated concepts and can trigger a learning intervention

Example intervention:

> You have asked about tensor shapes several times recently. Before continuing, write your current understanding in three sentences.

## Dashboard Views

The local dashboard is designed around fast inspection:

- Dashboard
  high-level counts, sources, top concepts, weak areas
- Knowledge Graph
  concept nodes and co-occurrence edges from conversation history
- Study Materials
  flashcards, study guides, and quizzes generated from your memory
- Summaries
  screenshot-friendly learning reports by period

The graph is the heart of the project. It is meant to show where the user's understanding is growing, where it is looping, and where a small amount of study would remove a lot of friction.

<a id="privacy-model"></a>
## Privacy Model

DeepReflect is local-first:

- conversation memory is stored in SQLite on your machine
- generated summaries are written to local HTML files
- `.env`, local databases, build output, dependency folders, and Python caches are ignored by git
- LLM calls use the provider you configure
- Ollama or another local OpenAI-compatible endpoint can keep analysis fully local

You control which provider receives conversation text. If a remote model is configured, analysis and study generation may send selected conversation content to that provider.

## Development

Backend:

```bash
pip install -e ".[dev]"
deepreflect serve --no-open
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Production frontend build:

```bash
cd frontend
npm run build
```

The FastAPI app serves `frontend/dist/` when that directory exists.
