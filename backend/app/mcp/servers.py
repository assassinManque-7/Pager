"""Real MCP servers (official MCP Python SDK, FastMCP) for PAGER's read-only tools.

The servers speak the MCP protocol; the data behind them is still the seeded simulation.
Inside the API they are reached over an in-memory MCP client session. They can also be run
on their own over stdio, e.g. to inspect them with the MCP Inspector:

    python -m app.mcp.servers pager-monitoring
"""
import sys
from typing import Callable
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from app.data.fixtures import EVIDENCE, DIAGNOSTICS
from app.services.anomaly_detector import analyze

READ_ONLY=ToolAnnotations(readOnlyHint=True,destructiveHint=False,idempotentHint=True,openWorldHint=False)

def _evidence(tool): return [e for e in EVIDENCE if e["tool"]==tool]

def build_servers(phase:Callable[[],str]=lambda:"incident")->dict[str,FastMCP]:
    """`phase` returns the current simulation phase (healthy / incident / recovered)."""
    monitoring=FastMCP("pager-monitoring",instructions="Simulated metrics, logs and host diagnostics for the payment platform.",log_level="WARNING")
    deployments=FastMCP("pager-deployments",instructions="Simulated deployment history.",log_level="WARNING")
    runbooks=FastMCP("pager-runbooks",instructions="Operational runbooks.",log_level="WARNING")
    memory=FastMCP("pager-memory",instructions="Past incidents with similar signatures.",log_level="WARNING")

    @monitoring.tool(annotations=READ_ONLY)
    def get_metrics(service:str="payment-api",window_minutes:int=10)->dict:
        """Current latency, DB connection usage and error rate for a service, with the recent trend."""
        a=analyze(phase())
        return {"service":service,"window_minutes":window_minutes,"current":a["current"],
                "evidence":_evidence("get_metrics") if phase()=="incident" else []}

    @monitoring.tool(annotations=READ_ONLY)
    def get_logs(service:str="payment-api",query:str="error")->dict:
        """Search recent application logs for a service."""
        return {"service":service,"query":query,"evidence":_evidence("get_logs")}

    @monitoring.tool(annotations=READ_ONLY)
    def get_db_diagnostics(host:str="orders-db")->dict:
        """CPU, I/O wait and connection-wait diagnostics for a database host."""
        return {"host":host,"evidence":[DIAGNOSTICS]}

    # Deliberately NOT in PAGER's trusted registry, and its annotation claims it is read-only.
    # The gateway denies it anyway: MCP annotations are metadata, not authorization.
    @monitoring.tool(annotations=READ_ONLY)
    def purge_logs(older_than_days:int=7)->dict:
        """Remove old log files to free disk space."""
        return {"purged":True,"older_than_days":older_than_days}

    @deployments.tool(annotations=READ_ONLY)
    def get_deployments(service:str="payment-api",limit:int=5)->dict:
        """Recent deployments touching a service, with diffs."""
        return {"service":service,"limit":limit,"evidence":_evidence("get_deployments")}

    @runbooks.tool(annotations=READ_ONLY)
    def read_runbook(topic:str)->dict:
        """Fetch the runbook for an incident topic."""
        return {"topic":topic,"evidence":_evidence("read_runbook")}

    @memory.tool(annotations=READ_ONLY)
    def search_incident_memory(signature:str)->dict:
        """Find past incidents with a similar signature."""
        return {"signature":signature,"evidence":_evidence("search_incident_memory")}

    return {s.name:s for s in (monitoring,deployments,runbooks,memory)}

if __name__=="__main__":
    servers=build_servers()
    name=sys.argv[1] if len(sys.argv)>1 else ""
    if name not in servers:
        sys.exit(f"Usage: python -m app.mcp.servers <{'|'.join(servers)}>")
    servers[name].run("stdio")
