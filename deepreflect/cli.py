"""DeepReflect CLI — deepreflect <command>"""
from __future__ import annotations

import asyncio
import json
import webbrowser
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from deepreflect.config import load_config, save_config

app = typer.Typer(
    name="deepreflect",
    help="Local AI learning memory agent",
    add_completion=False,
)
console = Console()

# ── Config ──────────────────────────────────────────────────────────────────


@app.command()
def config(
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider: anthropic|openai|ollama|openrouter"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="LLM API key"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Custom API base URL"),
    port: Optional[int] = typer.Option(None, "--port", help="Server port (default 7733)"),
    tone: Optional[str] = typer.Option(None, "--tone", help="Coach tone: strict|friendly|funny"),
    show: bool = typer.Option(False, "--show", help="Show current config"),
):
    """Configure DeepReflect settings."""
    cfg = load_config()

    if show:
        table = Table("Setting", "Value")
        table.add_row("provider", cfg.llm_provider)
        table.add_row("model", cfg.llm_model)
        table.add_row("api_key", cfg.llm_api_key[:8] + "..." if cfg.llm_api_key else "(not set)")
        table.add_row("port", str(cfg.port))
        table.add_row("tone", cfg.intervention_tone)
        table.add_row("base_url", cfg.llm_base_url or "(default)")
        table.add_row("data_dir", cfg.data_dir)
        console.print(table)
        return

    if provider:
        cfg.llm_provider = provider
    if api_key:
        cfg.llm_api_key = api_key
    if model:
        cfg.llm_model = model
    if base_url is not None:
        cfg.llm_base_url = base_url
    if port:
        cfg.port = port
    if tone:
        cfg.intervention_tone = tone

    save_config(cfg)
    console.print("[green]Config saved.[/green]")


# ── Install ──────────────────────────────────────────────────────────────────


@app.command()
def install(
    claude_code: bool = typer.Option(False, "--claude-code", help="Install Claude Code hooks"),
):
    """Install hooks into supported AI tools."""
    if not claude_code:
        console.print("Use --claude-code to install Claude Code hooks.")
        raise typer.Exit(1)

    settings_path = Path.home() / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists():
        data = json.loads(settings_path.read_text())
    else:
        data = {}

    hooks = data.setdefault("hooks", {})

    # Stop hook — ingest after session ends
    stop_hooks = hooks.setdefault("Stop", [])
    ingest_cmd = "deepreflect ingest --source claude-code"
    if not any(h.get("command") == ingest_cmd for entry in stop_hooks for h in entry.get("hooks", [])):
        stop_hooks.append({"matcher": "", "hooks": [{"type": "command", "command": ingest_cmd}]})

    # PreToolUse hook — intervention check
    pre_hooks = hooks.setdefault("PreToolUse", [])
    check_cmd = 'deepreflect check-intervention --prompt "$CLAUDE_USER_PROMPT"'
    if not any(h.get("command") == check_cmd for entry in pre_hooks for h in entry.get("hooks", [])):
        pre_hooks.append({"matcher": ".*", "hooks": [{"type": "command", "command": check_cmd}]})

    settings_path.write_text(json.dumps(data, indent=2))
    console.print(f"[green]Claude Code hooks installed in {settings_path}[/green]")
    console.print("  Stop hook: auto-ingest after each session")
    console.print("  PreToolUse hook: intervention check before each tool call")


# ── Import ──────────────────────────────────────────────────────────────────


@app.command("import")
def import_cmd(
    path: Optional[str] = typer.Argument(None, help="File or directory to import"),
    source: str = typer.Option("auto", "--source", help="Source: claude-code|markdown|json|auto"),
    all_projects: bool = typer.Option(False, "--all", help="Import all Claude Code projects"),
):
    """Import conversations from files or Claude Code."""
    from deepreflect.importers.claude_code import ClaudeCodeImporter
    from deepreflect.importers.json_importer import JsonImporter
    from deepreflect.importers.markdown_importer import MarkdownImporter
    from deepreflect.memory.db import get_session, upsert_turn

    cfg = load_config()
    turns = []

    if all_projects or (source == "claude-code" and path is None):
        importer = ClaudeCodeImporter()
        turns = importer.import_all_projects()
    elif path:
        p = Path(path)
        importers = [ClaudeCodeImporter(), MarkdownImporter(), JsonImporter()]
        files = list(p.rglob("*")) if p.is_dir() else [p]
        for f in files:
            for imp in importers:
                if imp.detect(str(f)):
                    turns.extend(imp.parse(str(f)))
                    break
    else:
        console.print("[red]Provide a path or use --all for all Claude Code projects.[/red]")
        raise typer.Exit(1)

    with get_session(cfg.db_path) as session:
        saved = 0
        for turn in turns:
            existing = upsert_turn(session, turn)
            if existing.id and turn.id != existing.id:
                saved += 1

    console.print(f"[green]Imported {len(turns)} turns ({saved} new)[/green]")


# ── Ingest (called by hook) ──────────────────────────────────────────────────


@app.command()
def ingest(
    source: str = typer.Option("claude-code", "--source"),
    session_id: Optional[str] = typer.Option(None, "--session-id"),
):
    """Ingest conversations (called by hooks). Runs silently."""
    from deepreflect.importers.claude_code import ClaudeCodeImporter
    from deepreflect.memory.db import get_session, upsert_turn

    cfg = load_config()
    importer = ClaudeCodeImporter()

    if session_id:
        turns = importer.import_session(session_id)
    else:
        turns = importer.import_all_projects()

    with get_session(cfg.db_path) as session:
        for turn in turns:
            upsert_turn(session, turn)


# ── Check intervention (called by PreToolUse hook) ──────────────────────────


@app.command()
def check_intervention(
    prompt: str = typer.Option("", "--prompt"),
):
    """Check if prompt triggers an intervention. Called by PreToolUse hook."""
    from deepreflect.analysis.detector import check_intervention as _check
    from deepreflect.agents.coach_agent import build_intervention_message, format_hook_output
    from deepreflect.memory.db import get_concepts, get_session
    from deepreflect.memory.models import Concept

    cfg = load_config()
    if not prompt:
        return

    with get_session(cfg.db_path) as session:
        should_intervene, triggered = _check(session, prompt, threshold=cfg.repeat_threshold)
        if should_intervene:
            # Get the highest ask count for the triggered concept
            from sqlmodel import select
            concept = session.exec(
                select(Concept).where(Concept.name.in_(triggered))
                .order_by(Concept.ask_count.desc())
            ).first()
            ask_count = concept.ask_count if concept else cfg.repeat_threshold
            msg = build_intervention_message(triggered, ask_count, cfg.intervention_tone)
            typer.echo(format_hook_output(msg))


# ── Analyze ──────────────────────────────────────────────────────────────────


@app.command()
def analyze(limit: int = typer.Option(50, "--limit", help="Max turns to analyze")):
    """Analyze unprocessed conversations and extract concepts."""
    from deepreflect.analysis.llm_client import LLMClient
    from deepreflect.analysis.tagger import tag_turn
    from deepreflect.memory.db import get_or_create_concept, get_session, get_unanalyzed_turns, record_mention

    cfg = load_config()
    if not cfg.llm_api_key:
        console.print("[red]Set your LLM API key first: deepreflect config --api-key <key>[/red]")
        raise typer.Exit(1)

    llm = LLMClient.from_config(cfg)

    async def _run():
        with get_session(cfg.db_path) as session:
            turns = get_unanalyzed_turns(session)[:limit]
            if not turns:
                console.print("No unanalyzed turns. Import conversations first.")
                return
            console.print(f"Analyzing {len(turns)} turns...")
            for i, turn in enumerate(turns):
                concepts, category = await tag_turn(turn, llm)
                for name in concepts:
                    concept = get_or_create_concept(session, name, category)
                    record_mention(session, turn, concept)
                turn.analyzed = True
                session.add(turn)
                session.commit()
                if (i + 1) % 10 == 0:
                    console.print(f"  {i+1}/{len(turns)} processed...")
            console.print(f"[green]Done. {len(turns)} turns analyzed.[/green]")

    asyncio.run(_run())


# ── Summary ──────────────────────────────────────────────────────────────────


@app.command()
def summary(
    period: str = typer.Option("weekly", "--period", "-p", help="daily|weekly|monthly|yearly"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open in browser"),
):
    """Generate a shareable HTML summary page."""
    from deepreflect.agents.summary_generator import generate_summary_html
    from deepreflect.memory.db import get_session

    cfg = load_config()
    with get_session(cfg.db_path) as session:
        out = generate_summary_html(session, period, cfg.summaries_dir)

    console.print(f"[green]Summary saved: {out}[/green]")
    if open_browser:
        webbrowser.open(f"file://{out}")


# ── Flashcards ────────────────────────────────────────────────────────────────


@app.command()
def flashcards(
    fmt: str = typer.Option("csv", "--format", "-f", help="csv|markdown"),
    generate: bool = typer.Option(False, "--generate", "-g", help="Generate new cards via LLM"),
    limit: int = typer.Option(10, "--limit"),
):
    """Export or generate flashcards."""
    from deepreflect.agents.study_agent import generate_flashcards as gen_cards
    from deepreflect.analysis.llm_client import LLMClient
    from deepreflect.memory.db import get_flashcards, get_session

    cfg = load_config()

    if generate:
        if not cfg.llm_api_key:
            console.print("[red]Set your LLM API key first.[/red]")
            raise typer.Exit(1)
        llm = LLMClient.from_config(cfg)

        async def _gen():
            with get_session(cfg.db_path) as session:
                cards = await gen_cards(session, llm, limit=limit)
                console.print(f"[green]Generated {len(cards)} flashcards.[/green]")

        asyncio.run(_gen())
        return

    with get_session(cfg.db_path) as session:
        cards = get_flashcards(session)

    if not cards:
        console.print("No flashcards yet. Run with --generate to create some.")
        return

    if fmt == "csv":
        import csv, sys
        writer = csv.writer(sys.stdout)
        writer.writerow(["Front", "Back"])
        for c in cards:
            writer.writerow([c.front, c.back])
    else:
        for i, c in enumerate(cards):
            console.print(f"\n[bold]Card {i+1}[/bold]")
            console.print(f"Q: {c.front}")
            console.print(f"A: {c.back}")


# ── Serve ─────────────────────────────────────────────────────────────────────


@app.command()
def serve(
    port: Optional[int] = typer.Option(None, "--port", "-p"),
    open_browser: bool = typer.Option(True, "--open/--no-open"),
):
    """Start the local DeepReflect dashboard server."""
    from deepreflect.api.app import app as fastapi_app

    cfg = load_config()
    _port = port or cfg.port

    if open_browser:
        import threading, time
        def _open():
            time.sleep(1.2)
            webbrowser.open(f"http://localhost:{_port}")
        threading.Thread(target=_open, daemon=True).start()

    console.print(f"[bold green]DeepReflect running at http://localhost:{_port}[/bold green]")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=_port, log_level="warning")


# ── Status ────────────────────────────────────────────────────────────────────


@app.command()
def status():
    """Show a summary of stored data."""
    from deepreflect.memory.db import get_session, get_stats

    cfg = load_config()
    with get_session(cfg.db_path) as session:
        s = get_stats(session)

    table = Table("Metric", "Value", title="DeepReflect Status")
    table.add_row("Total exchanges", str(s["total_turns"]))
    table.add_row("This week", str(s["weekly_turns"]))
    table.add_row("Concepts tracked", str(s["total_concepts"]))
    table.add_row("Flashcards", str(s["total_flashcards"]))
    table.add_row("Sources", ", ".join(f"{k}:{v}" for k, v in s["sources"].items()) or "none")
    console.print(table)


if __name__ == "__main__":
    app()
