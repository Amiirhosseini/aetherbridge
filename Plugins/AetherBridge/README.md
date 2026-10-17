# AetherBridge Unreal Plugin

Editor plugin that pairs with the Python `aetherbridge` package.

## Enable

1. Copy this folder to `YourProject/Plugins/AetherBridge`.
2. Enable **AetherBridge**, **Python Script Plugin**, **Remote Control**, **Remote Control Web Interface**.
3. Restart the editor. Confirm Remote Control listens on `http://127.0.0.1:30010`.

## Python bridge

`Content/Python/aetherbridge_ue.py` exposes:

- `list_actors`, `spawn_actor`, `move_actor`, `destroy_actor`, `console`
- `dispatch(op, args_json)` — JSON entrypoint used by the host agent via Remote Control `ExecutePythonCommand`

## Host agent

```bash
aetherbridge ping
aetherbridge agent "inspect NPCs" --mode remote
```

When Remote Control is offline, the host falls back to the deterministic sim world (same tool names).
