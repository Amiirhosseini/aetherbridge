---
name: aetherbridge-ue
description: Operate Unreal Engine levels via AetherBridge tools (inspect, spawn, NPC behavior, weather).
---

# AetherBridge Unreal skill

Use when the user wants an AI agent to control Unreal Engine levels.

## Tools

- `inspect_level` / `diagnose_level` — snapshot and health checks
- `list_actors` / `spawn_actor` / `move_actor` / `destroy_actor`
- `set_npc_behavior` — idle | patrol | attack | flee | follow
- `set_weather` / `set_time_of_day` / `console_command`

## Flow

1. diagnose_level
2. list_actors (npc)
3. remediate (move / behavior / weather / spawn)
4. inspect_level

## Modes

- `--mode sim` — offline deterministic world (default for demos)
- `--mode remote` — Unreal Remote Control HTTP `:30010`
- `--mode auto` — remote if ping succeeds else sim

## CLI

```bash
aetherbridge agent "spread hostile NPCs and set attack" -s combat-arena --playbook
aetherbridge ping
aetherbridge serve
```
