"""Domain models for Unreal world + agent traces."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BackendMode(str, Enum):
    SIM = "sim"
    REMOTE = "remote"
    AUTO = "auto"


class Vec3(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


class ActorKind(str, Enum):
    STATIC = "static"
    NPC = "npc"
    PLAYER_START = "player_start"
    LIGHT = "light"
    TRIGGER = "trigger"
    PROP = "prop"


class ActorState(BaseModel):
    id: str
    name: str
    kind: ActorKind = ActorKind.PROP
    class_path: str = "/Script/Engine.StaticMeshActor"
    location: Vec3 = Field(default_factory=Vec3)
    rotation_yaw: float = 0.0
    tags: list[str] = Field(default_factory=list)
    health: float = 100.0
    behavior: str = "idle"
    metadata: dict[str, Any] = Field(default_factory=dict)


class LevelSnapshot(BaseModel):
    map_name: str
    backend: BackendMode
    actors: list[ActorState]
    weather: str = "clear"
    time_of_day: float = 12.0
    findings: list[str] = Field(default_factory=list)
    console_log: list[str] = Field(default_factory=list)


class AgentTrace(BaseModel):
    goal: str
    backend: BackendMode
    steps: list[dict[str, Any]] = Field(default_factory=list)
    final: str = ""
    snapshot: LevelSnapshot | None = None
