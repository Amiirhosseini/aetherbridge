"""FastAPI surface for AetherBridge demos and Pages proxy."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from aetherbridge import __version__
from aetherbridge.agent.orchestrator import run_agent, run_playbook
from aetherbridge.models import BackendMode
from aetherbridge.ue.backend import build_backend
from aetherbridge.ue.sim_world import SCENARIOS

app = FastAPI(title="AetherBridge", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    goal: str
    scenario: str = "plaza"
    mode: BackendMode = BackendMode.SIM
    playbook: bool = False


class OpRequest(BaseModel):
    scenario: str = "plaza"
    mode: BackendMode = BackendMode.SIM
    actor_id: str = ""
    class_path: str = "/Game/Props/BP_Crate.BP_Crate_C"
    name: str = "DemoActor"
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    behavior: str = "patrol"
    weather: str = "clear"
    hour: float = 12.0
    kind: str = "prop"
    tags: list[str] = Field(default_factory=list)


@app.get("/health")
def health():
    return {"ok": True, "version": __version__, "scenarios": list(SCENARIOS)}


@app.get("/scenarios")
def scenarios():
    return SCENARIOS


@app.get("/snapshot")
def snapshot(scenario: str = "plaza", mode: BackendMode = BackendMode.SIM):
    world, resolved = build_backend(mode=mode, scenario=scenario)
    snap = world.snapshot()
    snap.backend = resolved
    return snap.model_dump(mode="json")


@app.get("/diagnose")
def diagnose(scenario: str = "plaza", mode: BackendMode = BackendMode.SIM):
    world, _ = build_backend(mode=mode, scenario=scenario)
    return {"findings": world.diagnose(), "suggestions": world.suggest_actions()}


@app.post("/agent")
def agent(req: AgentRequest):
    try:
        fn = run_playbook if req.playbook else run_agent
        trace = fn(req.goal, scenario=req.scenario, mode=req.mode)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return trace.model_dump(mode="json")


@app.post("/op/{op}")
def op(op: str, req: OpRequest):
    world, resolved = build_backend(mode=req.mode, scenario=req.scenario)
    try:
        if op == "spawn":
            out = world.spawn_actor(req.class_path, req.name, req.x, req.y, req.z, req.kind, req.tags)
            return {"backend": resolved, "result": out.model_dump(mode="json")}
        if op == "move":
            out = world.move_actor(req.actor_id, req.x, req.y, req.z)
            return {"backend": resolved, "result": out.model_dump(mode="json")}
        if op == "destroy":
            return {"backend": resolved, "result": world.destroy_actor(req.actor_id)}
        if op == "behavior":
            out = world.set_npc_behavior(req.actor_id, req.behavior)
            return {"backend": resolved, "result": out.model_dump(mode="json")}
        if op == "weather":
            return {"backend": resolved, "result": world.set_weather(req.weather)}
        if op == "time":
            return {"backend": resolved, "result": world.set_time_of_day(req.hour)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise HTTPException(status_code=404, detail=f"Unknown op: {op}")
