"""Typer CLI for AetherBridge."""

from __future__ import annotations

import json

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aetherbridge.agent.orchestrator import run_agent, run_playbook
from aetherbridge.ue.backend import build_backend
from aetherbridge.ue.sim_world import SCENARIOS

app = typer.Typer(
    name="aetherbridge",
    help="AI agents for Unreal Engine — Remote Control bridge, NPC brains, level ops.",
    no_args_is_help=True,
)
console = Console()


@app.command("scenarios")
def scenarios_cmd() -> None:
    """List built-in Unreal level scenarios."""
    table = Table(title="Scenarios")
    table.add_column("ID")
    table.add_column("Map")
    table.add_column("Weather")
    table.add_column("NPCs")
    for sid, cfg in SCENARIOS.items():
        table.add_row(sid, cfg["map"], cfg.get("weather", "-"), str(cfg.get("npcs", 0)))
    console.print(table)


@app.command()
def status(
    scenario: str = typer.Option("plaza", "--scenario", "-s"),
    mode: str = typer.Option("sim", "--mode", "-m", help="sim | remote | auto"),
) -> None:
    """Show level snapshot for sim or live Remote Control."""
    world, resolved = build_backend(mode=mode, scenario=scenario)
    snap = world.snapshot()
    console.print(
        Panel(
            f"map={snap.map_name}\nbackend={resolved.value}\n"
            f"actors={len(snap.actors)} weather={snap.weather} time={snap.time_of_day}\n"
            f"findings: {'; '.join(snap.findings)}",
            title="Level status",
        )
    )


@app.command()
def diagnose(
    scenario: str = typer.Option("plaza", "--scenario", "-s"),
    mode: str = typer.Option("sim", "--mode", "-m"),
) -> None:
    """Diagnose level health."""
    world, _ = build_backend(mode=mode, scenario=scenario)
    for f in world.diagnose():
        console.print(f"• {f}")
    console.print("[dim]Suggestions:[/dim]")
    for s in world.suggest_actions():
        console.print(f"  → {s}")


@app.command()
def agent(
    goal: str = typer.Argument(..., help="Natural language goal for the UE agent"),
    scenario: str = typer.Option("plaza", "--scenario", "-s"),
    mode: str = typer.Option("sim", "--mode", "-m"),
    playbook: bool = typer.Option(False, "--playbook", help="Deterministic tool playbook"),
) -> None:
    """Run the LangChain Unreal agent (or deterministic playbook)."""
    trace = (
        run_playbook(goal, scenario=scenario, mode=mode)
        if playbook
        else run_agent(goal, scenario=scenario, mode=mode)
    )
    console.print(Panel(trace.final, title=f"Agent ({trace.backend.value})"))
    table = Table(title="Trace")
    table.add_column("Kind")
    table.add_column("Detail")
    for step in trace.steps:
        kind = step.get("kind", "")
        if kind == "tool_call":
            detail = f"{step.get('name')} {json.dumps(step.get('args', {}))[:80]}"
        else:
            detail = str(step.get("content", step.get("name", "")))[:100]
        table.add_row(kind, detail)
    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
) -> None:
    """Start FastAPI demo server."""
    uvicorn.run("aetherbridge.api:app", host=host, port=port, reload=False)


@app.command()
def ping(
    url: str = typer.Option("http://127.0.0.1:30010", "--url"),
) -> None:
    """Ping Unreal Remote Control HTTP endpoint."""
    from aetherbridge.ue.remote import UnrealRemoteControl

    ok = UnrealRemoteControl(base_url=url).ping()
    if ok:
        console.print(f"[green]Remote Control reachable[/green] at {url}")
    else:
        console.print(f"[yellow]Remote Control offline[/yellow] at {url} — use --mode sim")


if __name__ == "__main__":
    app()
