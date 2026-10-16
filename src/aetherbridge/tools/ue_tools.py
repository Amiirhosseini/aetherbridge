"""LangChain tools bound to an Unreal backend (sim or Remote Control)."""

from __future__ import annotations

import json
from typing import Annotated

from langchain_core.tools import tool

from aetherbridge.ue.backend import UnrealBackend


def build_ue_tools(world: UnrealBackend):
    """Create StructuredTools closed over the Unreal world backend."""

    @tool
    def inspect_level() -> str:
        """Return map snapshot: actors, weather, time, findings, console log."""
        return json.dumps(world.snapshot().model_dump(mode="json"), indent=2)

    @tool
    def list_actors(
        kind: Annotated[str, "Optional kind: npc|prop|light|player_start|static|trigger"] = "",
        tag: Annotated[str, "Optional tag filter"] = "",
    ) -> str:
        """List actors in the current level, optionally filtered."""
        rows = world.list_actors(kind=kind or None, tag=tag or None)
        return json.dumps([a.model_dump(mode="json") for a in rows], indent=2)

    @tool
    def spawn_actor(
        class_path: Annotated[str, "UE class path e.g. /Game/Props/BP_Crate.BP_Crate_C"],
        name: Annotated[str, "Actor name"],
        x: Annotated[float, "World X"] = 0.0,
        y: Annotated[float, "World Y"] = 0.0,
        z: Annotated[float, "World Z"] = 0.0,
        kind: Annotated[str, "prop|npc|light|trigger|static"] = "prop",
        tags: Annotated[str, "Comma-separated tags"] = "",
    ) -> str:
        """Spawn an actor in the level (sim or via Remote Control bridge)."""
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        actor = world.spawn_actor(class_path, name, x, y, z, kind, tag_list)
        return json.dumps(actor.model_dump(mode="json"), indent=2)

    @tool
    def destroy_actor(actor_id: Annotated[str, "Actor id or name"]) -> str:
        """Destroy an actor by id or name."""
        return world.destroy_actor(actor_id)

    @tool
    def move_actor(
        actor_id: Annotated[str, "Actor id or name"],
        x: Annotated[float, "World X"],
        y: Annotated[float, "World Y"],
        z: Annotated[float, "World Z; omit to keep current"] = -999999.0,
    ) -> str:
        """Set actor world location."""
        z_arg = None if z <= -999998 else z
        actor = world.move_actor(actor_id, x, y, z_arg)
        return json.dumps(actor.model_dump(mode="json"), indent=2)

    @tool
    def set_npc_behavior(
        actor_id: Annotated[str, "NPC id or name"],
        behavior: Annotated[str, "idle|patrol|attack|flee|follow"],
    ) -> str:
        """Set NPC blackboard behavior."""
        actor = world.set_npc_behavior(actor_id, behavior)
        return json.dumps(actor.model_dump(mode="json"), indent=2)

    @tool
    def set_weather(weather: Annotated[str, "clear|overcast|rain|fog|snow"]) -> str:
        """Change level weather / atmosphere preset."""
        return world.set_weather(weather)

    @tool
    def set_time_of_day(hour: Annotated[float, "0-24 decimal hour"]) -> str:
        """Set time of day for lighting."""
        return world.set_time_of_day(hour)

    @tool
    def console_command(command: Annotated[str, "Unreal console command"]) -> str:
        """Execute an Unreal console command (stat fps, etc.)."""
        return world.console_command(command)

    @tool
    def diagnose_level() -> str:
        """Run layout / gameplay health checks on the current level."""
        return json.dumps(
            {"findings": world.diagnose(), "suggestions": world.suggest_actions()},
            indent=2,
        )

    @tool
    def suggest_actions() -> str:
        """Suggest remediation steps for current level findings."""
        return json.dumps(world.suggest_actions(), indent=2)

    return [
        inspect_level,
        list_actors,
        spawn_actor,
        destroy_actor,
        move_actor,
        set_npc_behavior,
        set_weather,
        set_time_of_day,
        console_command,
        diagnose_level,
        suggest_actions,
    ]
