"""LangChain / LangGraph agent for Unreal Engine ops."""

from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from aetherbridge.agent.sim_llm import UnrealSimChatModel
from aetherbridge.models import AgentTrace, BackendMode
from aetherbridge.tools.ue_tools import build_ue_tools
from aetherbridge.ue.backend import UnrealBackend, build_backend

SYSTEM = """You are AetherBridge, a custom LangChain agent that operates Unreal Engine levels.
You can inspect maps, list/spawn/move/destroy actors, set NPC behaviors, change weather/time,
run console commands, and diagnose layout issues.
Prefer diagnose -> list_actors -> remediate (move/behavior/spawn/weather) -> inspect_level.
When Remote Control is available, ops go through the editor bridge; otherwise use the sim world.
Be concise and cite tools."""


def build_llm():
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model=os.getenv("AETHERBRIDGE_MODEL", "gpt-4o-mini"), temperature=0)
        except ImportError:
            pass
    return UnrealSimChatModel()


def build_agent(
    world: UnrealBackend | None = None,
    scenario: str = "plaza",
    mode: BackendMode | str = BackendMode.SIM,
):
    if world is None:
        world, _ = build_backend(mode=mode, scenario=scenario)
    tools = build_ue_tools(world)
    llm = build_llm()
    if isinstance(llm, UnrealSimChatModel):
        llm.turn = 0
    graph = create_react_agent(llm, tools, prompt=SYSTEM)
    return graph, world, tools


def run_agent(
    goal: str,
    *,
    scenario: str = "plaza",
    mode: BackendMode | str = BackendMode.SIM,
    world: UnrealBackend | None = None,
    recursion_limit: int = 28,
) -> AgentTrace:
    if world is None:
        world, resolved = build_backend(mode=mode, scenario=scenario)
    else:
        resolved = BackendMode.SIM
        snap = world.snapshot()
        resolved = snap.backend

    tools = build_ue_tools(world)
    llm = build_llm()
    if isinstance(llm, UnrealSimChatModel):
        llm.turn = 0
    graph = create_react_agent(llm, tools, prompt=SYSTEM)

    result = graph.invoke(
        {"messages": [HumanMessage(content=goal)]},
        config={"recursion_limit": recursion_limit},
    )
    messages = result.get("messages", [])
    steps: list[dict[str, Any]] = []
    final = ""
    for message in messages:
        if isinstance(message, AIMessage):
            if message.tool_calls:
                for tc in message.tool_calls:
                    steps.append(
                        {
                            "kind": "tool_call",
                            "name": tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", ""),
                            "args": tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}),
                        }
                    )
            elif message.content:
                final = str(message.content)
                steps.append({"kind": "assistant", "content": final})
        else:
            steps.append(
                {
                    "kind": message.__class__.__name__,
                    "name": getattr(message, "name", None),
                    "content": str(getattr(message, "content", ""))[:500],
                }
            )

    if not final:
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                final = str(message.content)
                break
        if not final:
            final = "Agent completed without a textual final message."

    return AgentTrace(goal=goal, backend=resolved, steps=steps, final=final, snapshot=world.snapshot())


def run_playbook(
    goal: str,
    scenario: str = "plaza",
    mode: BackendMode | str = BackendMode.SIM,
) -> AgentTrace:
    """Deterministic playbook using the same LangChain tools (no LLM)."""
    world, resolved = build_backend(mode=mode, scenario=scenario)
    tools = {t.name: t for t in build_ue_tools(world)}
    steps: list[dict[str, Any]] = []
    goal_l = goal.lower()

    def call(name: str, **kwargs: Any) -> str:
        out = tools[name].invoke(kwargs)
        steps.append({"kind": "tool_call", "name": name, "args": kwargs})
        steps.append({"kind": "tool_result", "name": name, "content": str(out)[:600]})
        return str(out)

    call("diagnose_level")
    call("list_actors", kind="npc", tag="")

    if "rain" in goal_l or "weather" in goal_l:
        call("set_weather", weather="rain" if "rain" in goal_l else "clear")
    if "night" in goal_l:
        call("set_time_of_day", hour=22.0)
    elif "day" in goal_l or "lighting" in goal_l:
        call("set_time_of_day", hour=14.0)

    npcs = world.list_actors(kind="npc")
    if "combat" in goal_l or "hostile" in goal_l or "attack" in goal_l:
        for npc in npcs:
            if "hostile" in npc.tags:
                call("set_npc_behavior", actor_id=npc.id, behavior="attack")
            else:
                call("set_npc_behavior", actor_id=npc.id, behavior="patrol")
    elif "patrol" in goal_l or "spread" in goal_l or "overlap" in goal_l:
        for i, npc in enumerate(npcs[:3]):
            call(
                "move_actor",
                actor_id=npc.id,
                x=200.0 * (i + 1),
                y=-150.0 * (i + 1),
                z=92.0,
            )
            call("set_npc_behavior", actor_id=npc.id, behavior="patrol")

    if "spawn" in goal_l or "crate" in goal_l:
        call(
            "spawn_actor",
            class_path="/Game/Props/BP_Crate.BP_Crate_C",
            name="AgentCrate",
            x=300.0,
            y=100.0,
            z=0.0,
            kind="prop",
            tags="prop,agent",
        )

    if "stat" in goal_l or "console" in goal_l:
        call("console_command", command="stat fps")

    # Fix floating props if any
    for finding in world.diagnose():
        if "floating" in finding.lower():
            for prop in world.list_actors(kind="prop"):
                if prop.location.z > 200:
                    call("move_actor", actor_id=prop.id, x=prop.location.x, y=prop.location.y, z=0.0)

    call("diagnose_level")
    call("inspect_level")
    snap = world.snapshot()
    final = (
        f"Playbook finished for '{goal}' on {snap.map_name} ({resolved.value}). "
        f"Actors={len(snap.actors)} weather={snap.weather} time={snap.time_of_day:.1f}. "
        f"Findings: {'; '.join(snap.findings[:3])}"
    )
    steps.append({"kind": "assistant", "content": final})
    return AgentTrace(goal=goal, backend=resolved, steps=steps, final=final, snapshot=snap)
