"""Unreal Editor Python module — copy/symlink into project's Content/Python path.

Exposed as ``aetherbridge_ue`` when imported inside the editor. The external
AetherBridge agent calls into this via Remote Control ExecutePythonCommand.
"""

from __future__ import annotations

import json
from typing import Any


def _log(msg: str) -> None:
    try:
        import unreal

        unreal.log(f"[AetherBridge] {msg}")
    except Exception:
        print(f"[AetherBridge] {msg}")


def list_actors(kind: str | None = None) -> list[dict[str, Any]]:
    import unreal

    rows: list[dict[str, Any]] = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        loc = actor.get_actor_location()
        name = actor.get_name()
        cls = actor.get_class().get_name()
        row = {
            "id": name,
            "name": name,
            "class": cls,
            "location": {"x": loc.x, "y": loc.y, "z": loc.z},
        }
        if kind and kind.lower() not in cls.lower() and kind.lower() not in name.lower():
            continue
        rows.append(row)
    return rows


def spawn_actor(class_path: str, name: str, x: float = 0, y: float = 0, z: float = 0) -> dict:
    import unreal

    cls = unreal.load_class(None, class_path)
    if cls is None:
        # Fallback: static mesh actor marker
        _log(f"class not found: {class_path}")
        return {"error": f"class not found: {class_path}"}
    loc = unreal.Vector(x, y, z)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc)
    if actor:
        try:
            actor.set_actor_label(name)
        except Exception:
            pass
        _log(f"spawned {name} ({class_path})")
        return {"id": actor.get_name(), "name": name, "class_path": class_path}
    return {"error": "spawn failed"}


def move_actor(actor_id: str, x: float, y: float, z: float) -> dict:
    import unreal

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_name() == actor_id or actor.get_actor_label() == actor_id:
            actor.set_actor_location(unreal.Vector(x, y, z), False, True)
            _log(f"moved {actor_id}")
            return {"id": actor.get_name(), "location": {"x": x, "y": y, "z": z}}
    return {"error": f"actor not found: {actor_id}"}


def destroy_actor(actor_id: str) -> dict:
    import unreal

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_name() == actor_id or actor.get_actor_label() == actor_id:
            unreal.EditorLevelLibrary.destroy_actor(actor)
            _log(f"destroyed {actor_id}")
            return {"destroyed": actor_id}
    return {"error": f"actor not found: {actor_id}"}


def console(command: str) -> dict:
    import unreal

    unreal.SystemLibrary.execute_console_command(None, command)
    _log(f"console: {command}")
    return {"ok": True, "command": command}


def dispatch(op: str, args_json: str = "{}") -> str:
    """JSON dispatcher used by the external Remote Control client."""
    args = json.loads(args_json) if isinstance(args_json, str) else (args_json or {})
    table = {
        "list_actors": lambda: list_actors(args.get("kind")),
        "spawn_actor": lambda: spawn_actor(
            args["class_path"], args["name"], args.get("x", 0), args.get("y", 0), args.get("z", 0)
        ),
        "move_actor": lambda: move_actor(args["actor_id"], args["x"], args["y"], args["z"]),
        "destroy_actor": lambda: destroy_actor(args["actor_id"]),
        "console": lambda: console(args["command"]),
    }
    if op not in table:
        return json.dumps({"error": f"unknown op {op}"})
    return json.dumps(table[op]())
