// Copyright AetherBridge Contributors. Apache-2.0.
#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FAetherBridgeModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
