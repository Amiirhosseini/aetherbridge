# Copyright AetherBridge Contributors. Apache-2.0.

using UnrealBuildTool;

public class AetherBridge : ModuleRules
{
	public AetherBridge(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine"
		});
		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"UnrealEd",
			"PythonScriptPlugin",
			"RemoteControl"
		});
	}
}
