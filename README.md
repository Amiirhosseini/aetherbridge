# AetherBridge

**AI agents for Unreal Engine** — LangChain tools that inspect levels, spawn/move actors, drive NPC behaviors, change weather/time, and run console commands. Talks to a live editor over **Unreal Remote Control** (`:30010`) or a deterministic **sim world** when UE is offline.

Live demo: [amiirhosseini.com/aetherbridge](https://amiirhosseini.com/aetherbridge/)

## Why

Most “game AI” demos stop at chat. AetherBridge is an **agent control plane for the editor/runtime**: same tool surface for offline demos and a real UE5 project via Remote Control + editor Python.

## Features

| Capability | Detail |
|---|---|
| **Unreal Remote Control** | HTTP client → `ExecutePythonCommand` / AetherBridge dispatch |
| **Sim world** | Seeded plaza / combat-arena / night-city for CI & Pages |
| **LangChain tools** | `inspect_level`, `spawn_actor`, `set_npc_behavior`, … |
| **LangGraph agent** | ReAct loop + offline `UnrealSimChatModel` (no API key) |
| **UE plugin stub** | `Plugins/AetherBridge` + `Content/Python/aetherbridge_ue.py` |
| **MCP / Hermes** | `aetherbridge.mcp_server` + `hermes/skills/aetherbridge-ue` |
| **FastAPI** | `/agent`, `/snapshot`, `/diagnose`, `/op/*` |

## Install

```bash
pip install -e ".[dev]"
# optional live LLM
pip install -e ".[openai]"
```

## Quick start (sim — no Unreal required)

```bash
aetherbridge scenarios
aetherbridge status -s combat-arena
aetherbridge diagnose -s night-city
aetherbridge agent "spread NPCs and set hostiles to attack" -s combat-arena --playbook
aetherbridge agent "diagnose the plaza and spawn a crate" -s plaza
```

## Live Unreal Engine

1. Enable plugins: **Python Editor Script Plugin**, **Remote Control API**, **Remote Control Web Interface**.
2. Copy `Plugins/AetherBridge` into your UE project (or add as a plugin dependency).
3. Ensure `Content/Python/aetherbridge_ue.py` is importable in the editor.
4. Start the editor with Remote Control (default `http://127.0.0.1:30010`).
5. From the host machine:

```bash
aetherbridge ping
aetherbridge agent "list NPCs and set patrol" --mode auto -s plaza
```

`--mode auto` uses Remote Control when reachable, otherwise sim.

## Agent tools

- `inspect_level` / `diagnose_level` / `suggest_actions`
- `list_actors` / `spawn_actor` / `move_actor` / `destroy_actor`
- `set_npc_behavior` — `idle` \| `patrol` \| `attack` \| `flee` \| `follow`
- `set_weather` / `set_time_of_day` / `console_command`

## API

```bash
aetherbridge serve --port 8765
curl -s http://127.0.0.1:8765/snapshot?scenario=plaza
curl -s -X POST http://127.0.0.1:8765/agent \
  -H "content-type: application/json" \
  -d '{"goal":"set hostile NPCs to attack","scenario":"combat-arena","playbook":true}'
```

## MCP

```bash
python -m aetherbridge.mcp_server
```

## Layout

```
aetherbridge/
  Plugins/AetherBridge/          # UE editor plugin + Python bridge
  src/aetherbridge/
    ue/                          # sim world, Remote Control, backend factory
    tools/                       # LangChain StructuredTools
    agent/                       # LangGraph orchestrator + sim LLM
    api.py  cli.py  mcp_server.py
  docs/index.html                # interactive Pages demo
  hermes/skills/aetherbridge-ue/
```

## Tests

```bash
pytest -q
ruff check src tests
```

## License

Apache-2.0
