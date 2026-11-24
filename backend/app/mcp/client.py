"""PAGER's MCP client. Opens a real MCP session (initialize, tools/list, tools/call over JSON-RPC)
to each server. Callers must check the policy gateway BEFORE calling `call_tool`."""
import json
from mcp.shared.memory import create_connected_server_and_client_session
from app.mcp.servers import build_servers
from app.mcp.registry import TOOLS

TRANSPORT="MCP session (in-memory JSON-RPC)"
_servers={}

def configure(phase):
    _servers.clear(); _servers.update(build_servers(phase))

def server_names(): return list(_servers)

async def call_tool(server,tool,arguments):
    async with create_connected_server_and_client_session(_servers[server]) as session:
        r=await session.call_tool(tool,arguments)
    text=next((c.text for c in r.content if getattr(c,"type","")=="text"),"{}")
    if r.isError: raise RuntimeError(text)
    return json.loads(text)

_discovery=None
async def discover():
    """tools/list on every server. Compares what each server advertises with the trusted registry."""
    global _discovery
    if _discovery is None:
        out=[]
        for name,srv in _servers.items():
            async with create_connected_server_and_client_session(srv) as session:
                listed=(await session.list_tools()).tools
            tools=[]
            for t in listed:
                spec=TOOLS.get(t.name)
                trusted=bool(spec and spec["server"]==name)
                ann=t.annotations
                tools.append({"name":t.name,"description":t.description,"params":list((t.inputSchema or {}).get("properties",{})),
                              "readOnlyHint":bool(ann and ann.readOnlyHint),"trusted":trusted,"tier":spec["tier"] if trusted else "unknown"})
            out.append({"name":name,"transport":TRANSPORT,"tools":tools})
        _discovery=out
    return _discovery
