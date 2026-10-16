"""MCP server exposing Unreal level tools to Hermes / MCP clients."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from aetherbridge.ue.backend import build_backend

mcp = FastMCP("aetherbridge")


@mcp.tool()
def inspect_level(scenario: str = "plaza") -> str:
    """Snapshot the Unreal (sim) level."""
    world, _ = build_backend(mode="sim", scenario=scenario)
    return json.dumps(world.snapshot().model_dump(mode="json"), indent=2)


@mcp.tool()
def diagnose_level(scenario: str = "plaza") -> str:
    """Diagnose level layout / NPC issues."""
    world, _ = build_backend(mode="sim", scenario=scenario)
    return json.dumps({"findings": world.diagnose(), "suggestions": world.suggest_actions()}, indent=2)


@mcp.tool()
def set_npc_behavior(actor_id: str, behavior: str, scenario: str = "plaza") -> str:
    """Set NPC behavior on the sim world (demo)."""
    world, _ = build_backend(mode="sim", scenario=scenario)
    actor = world.set_npc_behavior(actor_id, behavior)
    return json.dumps(actor.model_dump(mode="json"), indent=2)


@mcp.tool()
def spawn_actor(
    class_path: str,
    name: str,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    scenario: str = "plaza",
) -> str:
    """Spawn an actor in the sim level."""
    world, _ = build_backend(mode="sim", scenario=scenario)
    actor = world.spawn_actor(class_path, name, x, y, z)
    return json.dumps(actor.model_dump(mode="json"), indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
