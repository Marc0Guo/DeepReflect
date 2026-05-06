# DeepReflect — Development Plan

## 1. Project Goal

Build an open-source local tool that helps users learn from their AI usage instead of passively depending on AI answers. DeepReflect records questions, prompts, mistakes, and repeated topics across AI tools such as Claude Code, OpenCode, Cursor, ChatGPT, and Gemini. It runs a local server with a filterable dashboard, a knowledge graph, and shareable HTML summary pages. Users connect their preferred LLM API to generate memory summaries, study guides, flashcards, quizzes, and usage reports.

---

## 2. Core Problem

AI tools improve productivity, but users repeatedly ask the same questions without learning the underlying concepts. Current AI assistants focus on task completion, not long-term learning. DeepReflect adds a learning layer on top of existing AI workflows by tracking usage history and turning it into personalized study material and a visual map of knowledge gaps.

---

## 3. Target Users

Students, developers, and researchers who use coding agents or chatbots every day. They want the speed benefits of AI but also want to understand what they are doing and avoid repeated knowledge gaps.

---

## 4. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | Python + FastAPI | Best ecosystem for NLP, embeddings, NetworkX, and data processing |
| Database | SQLite + ChromaDB | SQLite for structured data, ChromaDB for semantic search |
| Graph Engine | NetworkX | Graph construction and analysis in Python |
| Frontend | React + TypeScript + Vite | Component model fits the dashboard and graph views |
| Graph Visualization | React Flow or D3.js | Interactive node-edge graph rendering |
| Shareable Pages | Static HTML + html2canvas | Screenshot-friendly, shareable without a server |
| CLI | Python Typer | Clean argument parsing, auto-generates help text |
| Claude Hook | Claude Code `settings.json` hook | Native hook system, no patching required |

The FastAPI server runs on `localhost:7733` and serves both the API and the compiled React build from a single process.

---

## 5. Key Features

### 5.1 Conversation Import

Supported sources for MVP and post-MVP:

| Source | MVP |
|---|---|
| Claude Code (via hook) | Yes |
| Local markdown / JSON / text files | Yes |
| ChatGPT export (.zip) | Post-MVP |
| Cursor logs | Post-MVP |
| OpenCode plugin | Post-MVP |
| Gemini export | Post-MVP |

Each source is normalized into a shared schema:

```json
{
  "source": "claude-code",
  "session_id": "...",
  "timestamp": "2026-05-06T14:32:00Z",
  "user_prompt": "...",
  "ai_response": "...",
  "tags": ["pytorch", "tensor shape"],
  "metadata": {}
}
```

### 5.2 Local Memory System

Stored in SQLite with optional ChromaDB for semantic lookup:

- Repeated questions
- Common mistakes
- Weak concepts
- Solved problems
- Unfinished topics
- User confidence level
- Tool usage patterns
- Concepts flagged for review

### 5.3 LLM-Agnostic API Support

Users provide their own API key. Supported providers:

- Anthropic (Claude)
- OpenAI (GPT)
- Gemini
- Local Ollama models
- OpenRouter
- Any OpenAI-compatible endpoint

### 5.4 Knowledge Graph

**This is a core feature in MVP.**

The graph builds a living map of what the user is learning, where they are stuck, and which concepts keep repeating.

Each node represents a topic, concept, or mistake. Edges show how topics co-occur across conversations.

Node properties:
- ask count (times user asked about this topic)
- weak-area score (how often the same question recurs)
- last seen timestamp
- linked conversation turns

Graph features:
- topic clusters
- time-based growth (slider or filter)
- clickable nodes that show conversation history
- study guide generation from selected nodes
- flashcard generation from weak nodes

Backend: NetworkX for graph construction, exported as JSON.
Frontend: React Flow or D3.js for interactive rendering.

### 5.5 Filterable Local Dashboard

A local web dashboard served at `localhost:7733`. Modeled after a timeline-style view with filtering.

Filter dimensions:
- Day / Week / Month / Year
- Topic or tag
- Source tool (Claude, ChatGPT, etc.)
- Weak area vs. solved
- Date range

Views:
- Timeline view (activity over time)
- Analytics view (most asked topics, patterns, learning risk areas)
- Knowledge Graph view
- Study Materials view (flashcards, guides, quizzes)

### 5.6 Shareable HTML Summary Pages

Users can generate a self-contained HTML summary page at any time. Styled like a shareable "roast" or report card — readable in any browser, screenshot-friendly, and exportable to PNG via html2canvas.

Summary types:

```bash
deepreflect summary --daily
deepreflect summary --weekly
deepreflect summary --monthly
deepreflect summary --yearly
```

Each page includes:
- Top topics asked this period
- Repeated questions and weak areas
- AI tools used
- Learning risk score
- Most improved concepts
- A shareable URL or HTML file the user can post or screenshot

### 5.7 Study Materials

Generated from conversation memory using the user's LLM API:

- Weekly study guides
- Topic summaries
- Weak-area review plans
- Coding concept explanations
- Anki-compatible flashcards (markdown, CSV, or `.apkg`)
- Multiple-choice and short-answer quizzes
- Spaced repetition schedules

### 5.8 Intervention Mode (Coach Agent)

When the user repeats the same question above a configurable threshold, the coach agent can fire a warning. Tone is user-configurable: strict, friendly, or funny.

Example output:

> You have asked about backpropagation 4 times this week. Before I answer, write your current understanding in 3 sentences.

For Claude Code, this runs as a `PreToolUse` hook that checks the incoming prompt against memory before the conversation proceeds.

---

## 6. System Architecture

```
Data Sources
├── Claude Code Hook  ──────────────────────────────────────────────┐
├── File Import (markdown, JSON, ZIP)                               │
└── OpenCode / Cursor plugin (post-MVP)                             │
                                                                    ▼
                                              FastAPI Backend  (localhost:7733)
                                              ┌─────────────────────────────────┐
                                              │  Ingestion Layer                │
                                              │    normalize → tag → store      │
                                              │                                 │
                                              │  Memory Layer                   │
                                              │    SQLite  +  ChromaDB          │
                                              │                                 │
                                              │  Analysis Agent                 │
                                              │    cluster  detect  score       │
                                              │                                 │
                                              │  Knowledge Graph Engine         │
                                              │    NetworkX → JSON export       │
                                              │                                 │
                                              │  Study Agent                    │
                                              │    guides  flashcards  quizzes  │
                                              │                                 │
                                              │  Coach Agent                    │
                                              │    intervention  warnings       │
                                              └─────────────────┬───────────────┘
                                                                │
                                              React Frontend (served by FastAPI)
                                              ┌─────────────────────────────────┐
                                              │  Dashboard  (filterable)        │
                                              │  Knowledge Graph  (React Flow)  │
                                              │  Study Materials                │
                                              │  Shareable Summary HTML pages   │
                                              └─────────────────────────────────┘
```

### A. Ingestion Layer

```
src/importers/
  claude_code.py        # primary MVP importer
  markdown_importer.py
  json_importer.py
  chatgpt_export.py     # post-MVP
  cursor_logs.py        # post-MVP
  gemini_export.py      # post-MVP
```

### B. Memory Layer

```
src/memory/
  db.py                 # SQLite schema and queries
  embeddings.py         # ChromaDB wrapper
  models.py             # Pydantic data models
```

Memory types stored:
- `RawConversation`
- `ConceptMemory`
- `MistakeMemory`
- `RepeatedQuestion`
- `StudyPlan`
- `Flashcard`

### C. Analysis Agent

Runs on stored conversations and produces structured memory.

Tasks:
- extract topic tags from conversations (LLM call)
- cluster similar questions by embedding similarity
- detect repeated mistakes
- score topic familiarity (0–100)
- summarize learning progress

### D. Knowledge Graph Engine

```
src/graph/
  builder.py            # NetworkX graph construction
  exporter.py           # serialize to JSON for frontend
  scorer.py             # weak-area and familiarity scoring
```

### E. Study Agent

Converts memory into study outputs via LLM API calls.

### F. Coach Agent

Checks incoming prompts against memory. Fires when repeat threshold is crossed. Integrated as a Claude Code hook.

---

## 7. Claude Code Hook Integration

DeepReflect installs as a hook in the user's `~/.claude/settings.json`.

Two hooks:

**PostToolUse / Stop hook** — logs completed conversations to DeepReflect:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "deepreflect ingest --source claude-code --session $CLAUDE_SESSION_ID"
          }
        ]
      }
    ]
  }
}
```

**PreToolUse hook (Coach Agent)** — checks the prompt before answering:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "deepreflect check-intervention --prompt \"$CLAUDE_USER_PROMPT\""
          }
        ]
      }
    ]
  }
}
```

The hook setup is automated via:

```bash
deepreflect install --claude-code
```

---

## 8. Plugin Interface

The importer system is plugin-based so contributors can add new sources.

```python
class ImporterPlugin:
    name: str
    source_id: str

    def detect(self, path: str) -> bool:
        """Return True if this importer can handle the given file or path."""

    def parse(self, path: str) -> list[ConversationTurn]:
        """Parse and return normalized conversation turns."""
```

Future plugins:
- OpenCode plugin
- Cursor plugin
- VS Code extension
- Browser extension (capture ChatGPT/Gemini sessions)
- CLI file watcher (watch a directory for new logs)
- Obsidian export
- Anki `.apkg` export

---

## 9. MVP Scope

The first version is a working local tool: CLI + local dashboard + Claude Code hook.

### MVP Features

1. Claude Code hook — auto-ingest conversations after each session
2. File import — markdown and JSON conversation files
3. SQLite memory storage
4. LLM API integration (user provides key; supports Anthropic and OpenAI)
5. Topic extraction and repeated-question detection
6. Knowledge Graph — interactive view in the dashboard
7. Filterable local dashboard (day/week/month, topic, source)
8. Shareable HTML summary pages (daily, weekly, monthly, yearly)
9. Flashcard export (markdown and CSV)
10. `deepreflect install --claude-code` — one-command hook setup

### MVP CLI

```bash
# Setup
deepreflect install --claude-code         # wire up Claude Code hooks

# Import
deepreflect import ./conversations/       # import a folder of markdown/JSON files
deepreflect ingest --source claude-code   # called automatically by the hook

# Analyze
deepreflect analyze                       # run analysis and update memory

# Dashboard
deepreflect serve                         # open localhost:7733

# Outputs
deepreflect summary --weekly              # generate shareable HTML summary
deepreflect flashcards --format csv       # export flashcards
deepreflect quiz                          # generate a quiz from weak areas
```

---

## 10. Multi-Agent Design

```
Conversation Importer
        ↓
Memory Manager Agent   (tag, store, embed)
        ↓
Pattern Detection Agent  (cluster, score, detect repeats)
        ↓
Knowledge Graph Engine   (build / update node graph)
        ↓
Study Guide Agent        (generate guides, summaries)
        ↓
Flashcard / Quiz Agent   (generate study materials)
        ↓
Coach Agent              (intervention, warnings)
```

Each agent is independently runnable and can be disabled in config.

---

## 11. Privacy Design

Privacy is a core feature, not an afterthought.

- Local-first by default — no cloud storage required
- All data stays on the user's machine
- User controls which LLM provider receives conversation data
- Optional local LLM mode via Ollama (zero data leaves the machine)
- Clear delete and export options in the dashboard
- Optional redaction for names, emails, API keys, and private code before sending to LLM

---

## 12. Example User Flow

A user runs `deepreflect install --claude-code`. From that point, every Claude Code session is automatically ingested after it ends. After one week, they open `localhost:7733` and see their knowledge graph: Python, PyTorch, and Git are the largest clusters. The graph shows they asked about tensor shapes 6 times. They click the node, see the conversation history, and generate a flashcard set from it. They run `deepreflect summary --weekly` and get a shareable HTML page showing their top topics, weak areas, and learning score. They post it to share their progress.

---

## 13. Future Features (Post-MVP)

- ChatGPT, Cursor, Gemini, OpenCode importers
- Desktop app (Electron or Tauri)
- Browser extension (capture sessions from ChatGPT and Gemini)
- Real-time intervention via browser extension
- Anki `.apkg` sync
- Obsidian plugin
- Spaced repetition scheduler
- Team / classroom dashboard
- Learning score over time with streak tracking
- Public profile page (opt-in)
