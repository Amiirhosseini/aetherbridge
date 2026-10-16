"""Core AetherBridge tests — sim world, tools, playbook agent."""

from __future__ import annotations

from aetherbridge.agent.orchestrator import run_agent, run_playbook
from aetherbridge.tools.ue_tools import build_ue_tools
from aetherbridge.ue.backend import build_backend
from aetherbridge.ue.sim_world import UnrealSimWorld


def test_sim_seed_plaza():
    world = UnrealSimWorld("plaza")
    snap = world.snapshot()
    assert snap.map_name.endswith("AgentPlaza")
    assert any(a.kind.value == "npc" for a in snap.actors)
    assert world.diagnose()


def test_combat_hostile_tags():
    world = UnrealSimWorld("combat-arena")
    hostiles = [a for a in world.list_actors(kind="npc") if "hostile" in a.tags]
    assert hostiles


def test_spawn_move_behavior():
    world = UnrealSimWorld("plaza")
    actor = world.spawn_actor("/Game/Props/BP_Crate.BP_Crate_C", "Box", 10, 20, 0)
    world.move_actor(actor.id, 100, 200, 0)
    npc = world.list_actors(kind="npc")[0]
    world.set_npc_behavior(npc.id, "patrol")
    assert world.get_actor(actor.id).location.x == 100
    assert world.get_actor(npc.id).behavior == "patrol"


def test_tools_inspect():
    world, _mode = build_backend(mode="sim", scenario="night-city")
    tools = {t.name: t for t in build_ue_tools(world)}
    out = tools["diagnose_level"].invoke({})
    assert "findings" in out
    snap = tools["inspect_level"].invoke({})
    assert "NightBlock" in snap or "night" in snap.lower() or "actors" in snap


def test_playbook_combat():
    trace = run_playbook("set hostile NPCs to attack", scenario="combat-arena", mode="sim")
    assert trace.backend.value == "sim"
    assert any(s.get("name") == "set_npc_behavior" for s in trace.steps if s.get("kind") == "tool_call")
    assert trace.snapshot is not None
    assert "Playbook finished" in trace.final


def test_agent_sim_llm():
    trace = run_agent("diagnose and spread NPCs", scenario="plaza", mode="sim")
    assert len(trace.steps) >= 2
    assert trace.final
    names = {s.get("name") for s in trace.steps if s.get("kind") == "tool_call"}
    assert "diagnose_level" in names


def test_backend_auto_falls_back_to_sim():
    world, mode = build_backend(mode="auto", scenario="plaza", remote_url="http://127.0.0.1:1")
    assert mode.value == "sim"
    assert world.snapshot().actors
