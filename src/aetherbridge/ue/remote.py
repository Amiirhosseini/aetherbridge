"""Unreal Engine Remote Control HTTP client."""

from __future__ import annotations

from typing import Any

import httpx


class RemoteControlError(RuntimeError):
    pass


class UnrealRemoteControl:
    """Minimal client for UE Remote Control API (default :30010)."""

    def __init__(self, base_url: str = "http://127.0.0.1:30010", timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def ping(self) -> bool:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(f"{self.base_url}/remote/info")
                return r.status_code < 500
        except Exception:
            return False

    def call_function(
        self,
        object_path: str,
        function_name: str,
        parameters: dict[str, Any] | None = None,
        generate_transaction: bool = True,
    ) -> Any:
        payload = {
            "objectPath": object_path,
            "functionName": function_name,
            "parameters": parameters or {},
            "generateTransaction": generate_transaction,
        }
        with httpx.Client(timeout=self.timeout) as client:
            r = client.put(f"{self.base_url}/remote/object/call", json=payload)
        if r.status_code >= 400:
            raise RemoteControlError(f"Remote call failed ({r.status_code}): {r.text[:400]}")
        return r.json() if r.content else {}

    def execute_python(self, code: str) -> Any:
        """Run Python in the editor via PythonScriptLibrary CDO."""
        return self.call_function(
            object_path="/Script/PythonScriptPlugin.Default__PythonScriptLibrary",
            function_name="ExecutePythonCommand",
            parameters={"PythonCommand": code},
            generate_transaction=True,
        )

    def call_bridge(self, op: str, **kwargs: Any) -> Any:
        """Preferred path: call AetherBridge Python module through ExecutePythonCommand."""
        import json

        args = json.dumps(kwargs)
        code = (
            "import aetherbridge_ue as ab\n"
            f"print(ab.dispatch({op!r}, {args!r}))\n"
        )
        return self.execute_python(code)
