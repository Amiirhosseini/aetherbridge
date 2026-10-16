"""Deterministic Unreal level simulator for offline agent demos."""

from __future__ import annotations

import random
from copy import deepcopy

from aetherbridge.models import ActorKind, ActorState, BackendMode, LevelSnapshot, Vec3


SCENARIOS: dict[str, dict] = {
    "plaza": {
        "map": "/Game/Maps/AgentPlaza",
        "seed": 11,
        "weather": "clear",
        "npcs": 3,
        "props": 6,
    },
    "combat-arena": {
        "map": "/Game/Maps/CombatArena",
        "seed": 22,
        "weather": "overcast",
        "npcs": 5,
        "props": 4,
        "hostile": True,
    },
    "night-city": {
        "map": "/Game/Maps/NightBlock",
        "seed": 33,
        "weather": "rain",
        "time": 22.5,
        "npcs": 4,
        "props": 8,
    },
}


class UnrealSimWorld:
    """In-editor stand-in when Unreal Remote Control is offline."""

    def __init__(self, scenario: str = "plaza") -> None:
        if scenario not in SCENARIOS:
            raise KeyError(f"Unknown scenario '{scenario}'. Known: {', '.join(SCENARIOS)}")
        self.scenario = scenario
        self.cfg = SCENARIOS[scenario]
        self.rng = random.Random(self.cfg["seed"])
        self.map_name = self.cfg["map"]
        self.weather = self.cfg.get("weather", "clear")
        self.time_of_day = float(self.cfg.get("time", 12.0))
        self.console_log: list[str] = []
        self.actors: list[ActorState] = []
        self._seq = 0
        self._seed_level()

    def _id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}_{self._seq:03d}"

    def _seed_level(self) -> None:
        self.actors = [
            ActorState(
                id=self._id("PS"),
                name="PlayerStart",
                kind=ActorKind.PLAYER_START,
                class_path="/Script/Engine.PlayerStart",
                location=Vec3(x=0, y=0, z=92),
                tags=["spawn"],
            ),
            ActorState(
                id=self._id("L"),
                name="SunLight",
                kind=ActorKind.LIGHT,
                class_path="/Script/Engine.DirectionalLight",
                location=Vec3(x=0, y=0, z=500),
                tags=["lighting"],
            ),
        ]
        for i in range(int(self.cfg.get("props", 4))):
            self.actors.append(
                ActorState(
                    id=self._id("P"),
                    name=f"Prop_{i}",
                    kind=ActorKind.PROP,
                    class_path="/Game/Props/BP_Crate.BP_Crate_C",
                    location=Vec3(
                        x=self.rng.uniform(-800, 800),
                        y=self.rng.uniform(-800, 800),
                        z=0,
                    ),
                    rotation_yaw=self.rng.uniform(0, 360),
                    tags=["prop"],
                )
            )
        hostile = bool(self.cfg.get("hostile"))
        for i in range(int(self.cfg.get("npcs", 2))):
            self.actors.append(
                ActorState(
                    id=self._id("NPC"),
                    name=f"NPC_{i}",
                    kind=ActorKind.NPC,
                    class_path="/Game/Characters/BP_AgentNPC.BP_AgentNPC_C",
                    location=Vec3(
                        x=self.rng.uniform(-600, 600),
                        y=self.rng.uniform(-600, 600),
                        z=92,
                    ),
                    tags=["npc", "hostile" if hostile and i % 2 == 0 else "friendly"],
                    behavior="patrol" if not hostile else ("attack" if i % 2 == 0 else "patrol"),
                    health=100.0,
                    metadata={"blackboard": {"target": None, "alert": hostile}},
                )
            )

    def snapshot(self) -> LevelSnapshot:
        return LevelSnapshot(
            map_name=self.map_name,
            backend=BackendMode.SIM,
            actors=deepcopy(self.actors),
            weather=self.weather,
            time_of_day=self.time_of_day,
            findings=self.diagnose(),
            console_log=list(self.console_log[-20:]),
        )

    def list_actors(self, kind: str | None = None, tag: str | None = None) -> list[ActorState]:
        rows = self.actors
        if kind:
            rows = [a for a in rows if a.kind.value == kind]
        if tag:
            rows = [a for a in rows if tag in a.tags]
        return rows

    def get_actor(self, actor_id: str) -> ActorState:
        for a in self.actors:
            if a.id == actor_id or a.name == actor_id:
                return a
        raise KeyError(f"Actor not found: {actor_id}")

    def spawn_actor(
        self,
        class_path: str,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        kind: str = "prop",
        tags: list[str] | None = None,
    ) -> ActorState:
        actor = ActorState(
            id=self._id("A"),
            name=name,
            kind=ActorKind(kind),
            class_path=class_path,
            location=Vec3(x=float(x), y=float(y), z=float(z)),
            tags=tags or [],
        )
        self.actors.append(actor)
        self.console_log.append(f"SpawnActor {class_path} as {name} @ ({x:.0f},{y:.0f},{z:.0f})")
        return actor

    def destroy_actor(self, actor_id: str) -> str:
        actor = self.get_actor(actor_id)
        self.actors = [a for a in self.actors if a.id != actor.id]
        self.console_log.append(f"DestroyActor {actor.id}")
        return f"destroyed {actor.id}"

    def move_actor(self, actor_id: str, x: float, y: float, z: float | None = None) -> ActorState:
        actor = self.get_actor(actor_id)
        actor.location.x = x
        actor.location.y = y
        if z is not None:
            actor.location.z = z
        self.console_log.append(f"SetActorLocation {actor.id} -> ({x:.1f},{y:.1f},{actor.location.z:.1f})")
        return actor

    def set_npc_behavior(self, actor_id: str, behavior: str) -> ActorState:
        actor = self.get_actor(actor_id)
        if actor.kind != ActorKind.NPC:
            raise ValueError(f"{actor_id} is not an NPC")
        actor.behavior = behavior
        actor.metadata.setdefault("blackboard", {})["behavior"] = behavior
        self.console_log.append(f"NPC {actor.id} behavior={behavior}")
        return actor

    def set_weather(self, weather: str) -> str:
        self.weather = weather
        self.console_log.append(f"Weather={weather}")
        return f"weather={weather}"

    def set_time_of_day(self, hour: float) -> str:
        self.time_of_day = max(0.0, min(24.0, hour))
        self.console_log.append(f"TimeOfDay={self.time_of_day}")
        return f"time_of_day={self.time_of_day}"

    def console_command(self, command: str) -> str:
        self.console_log.append(f"> {command}")
        # Tiny command surface for demos
        low = command.strip().lower()
        if low.startswith("stat "):
            return f"ok: {command}"
        if "destroyalls" in low.replace(" ", ""):
            before = len(self.actors)
            self.actors = [a for a in self.actors if a.kind in {ActorKind.PLAYER_START, ActorKind.LIGHT}]
            return f"destroyed {before - len(self.actors)} actors"
        return f"executed: {command}"

    def diagnose(self) -> list[str]:
        findings: list[str] = []
        npcs = [a for a in self.actors if a.kind == ActorKind.NPC]
        floating = [
            a.id
            for a in self.actors
            if a.kind == ActorKind.PROP and a.location.z > 200
        ]
        clustered = 0
        for i, a in enumerate(npcs):
            for b in npcs[i + 1 :]:
                dx = a.location.x - b.location.x
                dy = a.location.y - b.location.y
                if (dx * dx + dy * dy) ** 0.5 < 120:
                    clustered += 1
        if not any(a.kind == ActorKind.PLAYER_START for a in self.actors):
            findings.append("Missing PlayerStart")
        if floating:
            findings.append(f"Props floating too high: {', '.join(floating[:4])}")
        if clustered:
            findings.append(f"NPC overlap risk ({clustered} close pairs) - spread patrol points")
        if self.weather == "rain" and self.time_of_day > 20:
            findings.append("Night + rain: consider stronger key light for readability")
        hostile = [a.id for a in npcs if "hostile" in a.tags]
        if hostile and any(a.behavior == "idle" for a in npcs if a.id in hostile):
            findings.append("Hostile NPCs idle - set attack/patrol behavior")
        if not findings:
            findings.append("Level looks healthy")
        return findings

    def suggest_actions(self) -> list[str]:
        actions: list[str] = []
        for finding in self.diagnose():
            low = finding.lower()
            if "playerstart" in low:
                actions.append("spawn PlayerStart near origin")
            if "floating" in low:
                actions.append("move floating props to z=0")
            if "overlap" in low:
                actions.append("spread NPCs with move_actor")
            if "hostile" in low:
                actions.append("set_npc_behavior attack on hostile NPCs")
            if "rain" in low or "night" in low:
                actions.append("set_time_of_day 14 or spawn fill light")
        if not actions:
            actions.append("list_actors and inspect_level")
        return actions
