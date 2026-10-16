"""Offline chat model that emits LangChain tool calls for Unreal goals."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from pydantic import Field


class UnrealSimChatModel(BaseChatModel):
    """Deterministic LLM stand-in so demos/tests need no API key."""

    model_name: str = Field(default="aetherbridge-sim")
    turn: int = 0

    @property
    def _llm_type(self) -> str:
        return "aetherbridge-sim"

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Runnable:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        goal = self._latest_human(messages).lower()
        tool_payloads = self._tool_payloads(messages)
        joined = "\n".join(tool_payloads).lower()
        self.turn += 1

        if self.turn >= 8 or ("inspect_level" in joined and self.turn >= 7):
            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content=self._final(goal, tool_payloads)))]
            )

        if self.turn == 1:
            return self._tool("diagnose_level", {})

        if self.turn == 2:
            return self._tool("list_actors", {"kind": "npc", "tag": ""})

        if self.turn == 3:
            if "weather" in goal or "rain" in goal or "night" in goal:
                if "rain" in goal:
                    return self._tool("set_weather", {"weather": "rain"})
                if "night" in goal:
                    return self._tool("set_time_of_day", {"hour": 22.0})
                return self._tool("set_weather", {"weather": "clear"})
            if "spawn" in goal or "prop" in goal:
                return self._tool(
                    "spawn_actor",
                    {
                        "class_path": "/Game/Props/BP_Crate.BP_Crate_C",
                        "name": "AgentCrate",
                        "x": 200.0,
                        "y": 150.0,
                        "z": 0.0,
                        "kind": "prop",
                        "tags": "prop,agent",
                    },
                )
            if "hostile" in joined or "attack" in goal or "combat" in goal:
                match = re.search(r"npc_\d+", joined)
                aid = match.group(0) if match else "NPC_001"
                # Prefer first id from dump
                ids = re.findall(r'"id":\s*"(NPC_\d+)"', joined)
                if ids:
                    aid = ids[0]
                return self._tool("set_npc_behavior", {"actor_id": aid, "behavior": "attack"})
            if "overlap" in joined or "spread" in joined or "patrol" in goal:
                ids = re.findall(r'"id":\s*"(NPC_\d+)"', joined)
                aid = ids[0] if ids else "NPC_001"
                return self._tool("move_actor", {"actor_id": aid, "x": 400.0, "y": -300.0, "z": 92.0})
            return self._tool("suggest_actions", {})

        if self.turn == 4:
            if "floating" in joined:
                ids = re.findall(r"props floating[^:]*:\s*([p_0-9, ]+)", joined)
                # fallback move first prop-like id
                prop_ids = re.findall(r'"id":\s*"(P_\d+)"', joined)
                aid = prop_ids[0] if prop_ids else "P_001"
                return self._tool("move_actor", {"actor_id": aid, "x": 0.0, "y": 0.0, "z": 0.0})
            if "hostile" in joined or "attack" in goal:
                ids = re.findall(r'"id":\s*"(NPC_\d+)"', joined)
                aid = ids[1] if len(ids) > 1 else (ids[0] if ids else "NPC_002")
                return self._tool("set_npc_behavior", {"actor_id": aid, "behavior": "patrol"})
            if "spawn" in goal:
                return self._tool(
                    "spawn_actor",
                    {
                        "class_path": "/Game/Characters/BP_AgentNPC.BP_AgentNPC_C",
                        "name": "ScoutNPC",
                        "x": -200.0,
                        "y": 250.0,
                        "z": 92.0,
                        "kind": "npc",
                        "tags": "npc,friendly",
                    },
                )
            return self._tool("set_time_of_day", {"hour": 14.0})

        if self.turn == 5:
            if "console" in goal or "stat" in goal:
                return self._tool("console_command", {"command": "stat fps"})
            return self._tool("diagnose_level", {})

        if self.turn == 6:
            return self._tool("inspect_level", {})

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=self._final(goal, tool_payloads)))]
        )

    def _tool(self, name: str, args: dict) -> ChatResult:
        msg = AIMessage(
            content="",
            tool_calls=[{"name": name, "args": args, "id": f"call_{self.turn}_{name}"}],
        )
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def _latest_human(self, messages: list[BaseMessage]) -> str:
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                return str(message.content)
        return ""

    def _tool_payloads(self, messages: list[BaseMessage]) -> list[str]:
        return [str(m.content) for m in messages if isinstance(m, ToolMessage)]

    def _final(self, goal: str, payloads: list[str]) -> str:
        bits = [f"Goal addressed: {goal}"]
        for payload in payloads[-3:]:
            bits.append(payload[:240])
        bits.append(
            "AetherBridge agent finished: diagnose -> list NPCs -> remediate "
            "(move/behavior/weather/spawn) -> re-inspect Unreal level."
        )
        return "\n".join(bits)

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model_name": self.model_name}
