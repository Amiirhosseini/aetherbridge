# AetherBridge init — runs when Unreal Python starts (if on sys.path).
try:
    import aetherbridge_ue  # noqa: F401
    print("[AetherBridge] aetherbridge_ue ready")
except Exception as exc:  # noqa: BLE001
    print(f"[AetherBridge] init skipped: {exc}")
