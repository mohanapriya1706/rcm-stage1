import inspect
import google.adk.tools.mcp_tool.mcp_toolset as mcp_toolset

def list_connection_params_classes():
    print("Available connection parameter classes in mcp_toolset:\n")
    
    for name, obj in inspect.getmembers(mcp_toolset):
        if inspect.isclass(obj) and name.endswith("ConnectionParams"):
            print(f"- {name}")
            # Show constructor signature
            init_sig = inspect.signature(obj.__init__)
            params = list(init_sig.parameters.values())[1:]  # skip 'self'
            print("    └── Args:", ", ".join(str(p) for p in params))

if __name__ == "__main__":
    list_connection_params_classes()
