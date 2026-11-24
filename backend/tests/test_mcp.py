import sys, anyio
from pathlib import Path
from fastapi.testclient import TestClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.main import app
client=TestClient(app)
BACKEND=Path(__file__).resolve().parents[1]

def test_discovery_compares_servers_with_registry():
 servers={s["name"]:s for s in client.get("/api/mcp/servers").json()["servers"]}
 assert {"pager-monitoring","pager-deployments","pager-runbooks","pager-memory","pager-sandbox"}<=set(servers)
 purge=next(t for t in servers["pager-monitoring"]["tools"] if t["name"]=="purge_logs")
 # The server claims read-only, but it is not in the trusted registry.
 assert purge["readOnlyHint"] and not purge["trusted"]

def test_untrusted_tool_on_real_server_is_denied_and_never_sent():
 client.post("/api/demo/reset")
 r=client.post("/api/gateway/probe",json={"tool":"purge_logs","server":"pager-monitoring"}).json()
 assert r["decision"]=="DENY" and r["transport"]=="not-sent"

def test_writes_go_to_sandbox_mock_not_mcp():
 client.post("/api/demo/reset"); client.post("/api/incidents/trigger",json={})
 client.post("/api/actions/ACT-SCALE/execute",json={"confirmed":True})
 last=client.get("/api/gateway/log").json()["items"][-1]
 assert last["tool"]=="scale_workers" and last["transport"]=="sandbox-mock"
 client.post("/api/demo/reset")

def test_server_runs_standalone_over_stdio():
 async def main():
  params=StdioServerParameters(command=sys.executable,args=["-m","app.mcp.servers","pager-runbooks"],cwd=str(BACKEND))
  async with stdio_client(params) as (r,w), ClientSession(r,w) as s:
   await s.initialize()
   assert [t.name for t in (await s.list_tools()).tools]==["read_runbook"]
   res=await s.call_tool("read_runbook",{"topic":"db-pool-saturation"})
   assert not res.isError and "EV-05" in res.content[0].text
 anyio.run(main)
