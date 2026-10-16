// Copyright AetherBridge Contributors. Apache-2.0.

#include "AetherBridgeModule.h"
#include "Misc/Paths.h"
#include "HAL/PlatformFilemanager.h"

#define LOCTEXT_NAMESPACE "FAetherBridgeModule"

void FAetherBridgeModule::StartupModule()
{
	// Editor Python startup scripts under Content/Python are auto-discovered when
	// PythonScriptPlugin is enabled. See Content/Python/init_unreal.py.
	UE_LOG(LogTemp, Log, TEXT("AetherBridge: editor module started — enable Remote Control (:30010) for live agents."));
}

void FAetherBridgeModule::ShutdownModule()
{
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAetherBridgeModule, AetherBridge)
