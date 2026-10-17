# AetherBridge

**AI agents for Unreal Engine** — LangChain tools that inspect levels, spawn/move actors, drive NPC behaviors, change weather/time, and run console commands. Talks to a live editor over **Unreal Remote Control** (`:30010`) or a deterministic **sim world** when UE is offline.

> **Live demo:** [amiirhosseini.com/aetherbridge](https://amiirhosseini.com/aetherbridge/)  
> Pick Combat Arena → Run UE agent → watch diagnose → list NPCs → set attack / spread → inspect.

[![Live Demo](https://img.shields.io/badge/demo-live-e85d04)](https://amiirhosseini.com/aetherbridge/)
[![CI](https://github.com/Amiirhosseini/aetherbridge/actions/workflows/ci.yml/badge.svg)](https://github.com/Amiirhosseini/aetherbridge/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)](pyproject.toml)
[![Unreal](https://img.shields.io/badge/Unreal-UE5%20Remote%20Control-2ec4b6)](Plugins/AetherBridge)

## What it is

A control plane for **AI agents inside the Unreal editor/runtime** — not chat about games, actual level ops:

| Piece | Role |
|-------|------|
| **LangChain tools** | `inspect_level`, `spawn_actor`, `set_npc_behavior`, weather/time/console |
| **LangGraph agent** | ReAct loop; offline `UnrealSimChatModel` when no API key |
| **Remote Control** | HTTP → editor Python (`ExecutePythonCommand` / `aetherbridge_ue`) |
| **Sim world** | Seeded plaza / combat-arena / night-city for CI & Pages |
| **UE plugin** | Editor module + `Content/Python` bridge |
| **MCP / Hermes** | Same ops for agent hosts |

```text
Goal (NL)
   |
   v
LangChain agent --tools--> Backend factory
                              |
                    +---------+---------+
                    v                   v
            UnrealSimWorld      Remote Control :30010
            (offline demo)      -> aetherbridge_ue.py
                                        |
                                        v
                                 UE5 Editor / Level
```

## Quick start (sim — no Unreal required)

```bash
git clone https://github.com/Amiirhosseini/aetherbridge.git
cd aetherbridge
pip install -e ".[dev]"

aetherbridge scenarios
aetherbridge status -s combat-arena
aetherbridge diagnose -s night-city
aetherbridge agent "spread NPCs and set hostiles to attack" -s combat-arena --playbook
aetherbridge agent "diagnose the plaza and spawn a crate" -s plaza
```

## Live demo walkthrough

1. Open [amiirhosseini.com/aetherbridge](https://amiirhosseini.com/aetherbridge/)
2. Select **Combat Arena**
3. Click **Run UE agent** — hostiles → attack, NPCs spread, trace fills
4. Try **Diagnose level** or change the goal (rain / spawn crate / night)

## Live Unreal Engine

1. Enable plugins: **Python Editor Script Plugin**, **Remote Control API**, **Remote Control Web Interface**.
2. Copy `Plugins/AetherBridge` into your UE project.
3. Ensure `Content/Python/aetherbridge_ue.py` is importable in the editor.
4. Start the editor with Remote Control (default `http://127.0.0.1:30010`).
5. From the host:

```bash
aetherbridge ping
aetherbridge agent "list NPCs and set patrol" --mode auto -s plaza
```

`--mode auto` uses Remote Control when reachable, otherwise sim.

## Agent tools

| Tool | Purpose |
|------|---------|
| `inspect_level` / `diagnose_level` | Snapshot + layout health |
| `list_actors` / `spawn_actor` / `move_actor` / `destroy_actor` | Level ops |
| `set_npc_behavior` | `idle` \| `patrol` \| `attack` \| `flee` \| `follow` |
| `set_weather` / `set_time_of_day` / `console_command` | Atmosphere + console |

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

```text
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
