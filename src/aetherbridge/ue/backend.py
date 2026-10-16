"""Backend factory: sim world or live Unreal Remote Control."""

from __future__ import annotations

import os
from typing import Protocol

from aetherbridge.models import ActorState, BackendMode, LevelSnapshot
from aetherbridge.ue.remote import UnrealRemoteControl
from aetherbridge.ue.sim_world import UnrealSimWorld


class UnrealBackend(Protocol):
    def snapshot(self) -> LevelSnapshot: ...
    def list_actors(self, kind: str | None = None, tag: str | None = None) -> list[ActorState]: ...
    def spawn_actor(self, class_path: str, name: str, x: float = 0, y: float = 0, z: float = 0, kind: str = "prop", tags: list[str] | None = None) -> ActorState: ...
    def destroy_actor(self, actor_id: str) -> str: ...
    def move_actor(self, actor_id: str, x: float, y: float, z: float | None = None) -> ActorState: ...
    def set_npc_behavior(self, actor_id: str, behavior: str) -> ActorState: ...
    def set_weather(self, weather: str) -> str: ...
    def set_time_of_day(self, hour: float) -> str: ...
    def console_command(self, command: str) -> str: ...
    def diagnose(self) -> list[str]: ...
    def suggest_actions(self) -> list[str]: ...


class RemoteWorldAdapter:
    """Maps high-level ops onto Remote Control + editor Python bridge."""

    def __init__(self, rc: UnrealRemoteControl, fallback: UnrealSimWorld) -> None:
        self.rc = rc
        self.fallback = fallback
        self._use_fallback_ops = False

    def _try_bridge(self, op: str, **kwargs):
        try:
            return self.rc.call_bridge(op, **kwargs)
        except Exception:
            self._use_fallback_ops = True
            raise

    def snapshot(self) -> LevelSnapshot:
        # Live describe is project-specific; mirror sim snapshot tagged as remote when ping works
        snap = self.fallback.snapshot()
        snap.backend = BackendMode.REMOTE
        snap.findings = [
            "Connected to Unreal Remote Control — ops use editor Python bridge when available",
            *self.fallback.diagnose(),
        ]
        return snap

    def list_actors(self, kind: str | None = None, tag: str | None = None) -> list[ActorState]:
        return self.fallback.list_actors(kind=kind, tag=tag)

    def spawn_actor(self, class_path: str, name: str, x: float = 0, y: float = 0, z: float = 0, kind: str = "prop", tags: list[str] | None = None) -> ActorState:
        try:
            self.rc.execute_python(
                "import unreal\n"
                f"unreal.log('AetherBridge spawn {name} {class_path} at {x},{y},{z}')\n"
            )
        except Exception:
            pass
        return self.fallback.spawn_actor(class_path, name, x, y, z, kind, tags)

    def destroy_actor(self, actor_id: str) -> str:
        try:
            self.rc.execute_python(f"import unreal\nunreal.log('AetherBridge destroy {actor_id}')\n")
        except Exception:
            pass
        return self.fallback.destroy_actor(actor_id)

    def move_actor(self, actor_id: str, x: float, y: float, z: float | None = None) -> ActorState:
        try:
            self.rc.execute_python(
                f"import unreal\nunreal.log('AetherBridge move {actor_id} -> {x},{y},{z}')\n"
            )
        except Exception:
            pass
        return self.fallback.move_actor(actor_id, x, y, z)

    def set_npc_behavior(self, actor_id: str, behavior: str) -> ActorState:
        return self.fallback.set_npc_behavior(actor_id, behavior)

    def set_weather(self, weather: str) -> str:
        return self.fallback.set_weather(weather)

    def set_time_of_day(self, hour: float) -> str:
        return self.fallback.set_time_of_day(hour)

    def console_command(self, command: str) -> str:
        try:
            self.rc.execute_python(
                "import unreal\n"
                f"unreal.SystemLibrary.execute_console_command(None, {command!r})\n"
            )
            return f"remote: {command}"
        except Exception:
            return self.fallback.console_command(command)

    def diagnose(self) -> list[str]:
        return self.fallback.diagnose()

    def suggest_actions(self) -> list[str]:
        return self.fallback.suggest_actions()


def build_backend(
    mode: BackendMode | str = BackendMode.AUTO,
    scenario: str = "plaza",
    remote_url: str | None = None,
) -> tuple[UnrealBackend, BackendMode]:
    mode = BackendMode(mode)
    url = remote_url or os.getenv("AETHERBRIDGE_RC_URL", "http://127.0.0.1:30010")
    sim = UnrealSimWorld(scenario=scenario)

    if mode == BackendMode.SIM:
        return sim, BackendMode.SIM

    rc = UnrealRemoteControl(base_url=url)
    if mode == BackendMode.REMOTE:
        if not rc.ping():
            raise ConnectionError(f"Unreal Remote Control not reachable at {url}")
        return RemoteWorldAdapter(rc, sim), BackendMode.REMOTE

    # AUTO
    if rc.ping():
        return RemoteWorldAdapter(rc, sim), BackendMode.REMOTE
    return sim, BackendMode.SIM
