from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid
from app.core.store import store
from app.services.anomaly_detector import analyze
from app.services.deployment_risk import score
from app.services.evidence_correlator import correlate
from app.services.root_cause import hypotheses
from app.services.blast_radius import graph
from app.services.recommendations import get
from app.mcp import policy_gateway as pg
from app.mcp.registry import TOOLS
from app.mcp import client as mcp_client
from app.mcp.tools import INVESTIGATION_PLAN, ACTION_ARGS
from app.data.fixtures import BASELINE

router=APIRouter()

def fresh_state(**kw):
 return {"active":False,"phase":"healthy","incident_id":None,"approval":None,"executed":False,
         "timeline":[],"gateway":[],"evidence":[],**kw}
state=fresh_state()
# The MCP servers read the simulation phase so metrics reflect the incident / recovery.
mcp_client.configure(lambda: state["phase"])

def event(name,detail=None,actor="pager"):
 item={"time":datetime.now(timezone.utc).isoformat(),"event":name,"detail":detail or {},"actor":actor}
 state["timeline"].append(item); store.log(state.get("incident_id"),actor,name,detail or {})
 return item

def feed_entry(**kw):
 entry={"id":len(state["gateway"])+1,"time":datetime.now(timezone.utc).isoformat(),**kw}
 state["gateway"].append(entry)
 return entry

async def gateway_call(tool, purpose, server=None, args=None, dry_run=False, actor="pager-agent", **ctx):
 """Every agent tool call goes through here. The policy gateway decides FIRST; only an allowed,
 non-dry-run call is sent on: read-only tools to their real MCP server, writes to the sandbox mock.
 A denied call never reaches any server."""
 args=args if args is not None else ACTION_ARGS.get(tool,{})
 server=server or TOOLS.get(tool,{}).get("server","unknown")
 gate=pg.evaluate(tool, server=server, **ctx)
 run=gate["allowed"] and not dry_run
 transport=("mcp" if gate["tier"]=="read_only" else "sandbox-mock") if run else "not-sent"
 entry=feed_entry(kind="call",tool=tool,server=server,args=args,tier=gate["tier"],decision=gate["decision"],
                  reason=gate["reason"],purpose=purpose,dry_run=dry_run,actor=actor,transport=transport)
 result=None
 if transport=="mcp":
  try:
   result=await mcp_client.call_tool(server,tool,args)
  except Exception as e:
   entry["error"]=str(e)[:200]
  for ev in (result or {}).get("evidence",[]):
   if ev["id"] not in {e["id"] for e in state["evidence"]}: state["evidence"].append(ev)
 event("GATEWAY_DRY_RUN" if dry_run else "TOOL_CALL",entry,actor)
 return gate,entry,result

def stage():
 if not state["active"]: return "idle"
 if state["executed"]: return "resolved"
 a=state["approval"]
 if a and a["status"]=="approved": return "execute"
 if a and a["status"]=="pending": return "approve"
 return "propose"

def approved_by():
 a=state["approval"]
 return a["approver"] if a and a["status"]=="approved" else None

class Decision(BaseModel):
 decision:str=Field(pattern="^(approve|reject)$")
 approver:str=Field(min_length=2,max_length=80)
 requester:str="oncall.primary"
class Trigger(BaseModel):
 scenario:str="payment_pool_regression"
class ApprovalRequest(BaseModel):
 action_id:str
 requester:str="oncall.primary"
class PreviewRequest(BaseModel):
 environment:str="SANDBOX"
class ExecuteRequest(BaseModel):
 confirmed:bool=False
class Probe(BaseModel):
 tool:str=Field(min_length=1,max_length=80)
 server:Optional[str]=Field(default=None,max_length=80)
class PolicySwitch(BaseModel):
 enabled:bool

@router.get("/status")
def status():
 return {"active":state["active"],"incident_id":state["incident_id"],"phase":state["phase"],"stage":stage(),
         "kill_switch":pg.KILL_SWITCH,"mode":"SIMULATION"}

@router.post("/incidents/trigger")
async def trigger(body:Trigger):
 state.clear(); state.update(fresh_state(active=True,phase="incident",incident_id="INC-"+uuid.uuid4().hex[:8].upper()))
 event("PREDICTIVE_WARNING",{"scenario":body.scenario,"risk":analyze("incident")["risk_score"]})
 # Agent loop step 1: discover what the MCP servers offer (tools/list).
 servers=await mcp_client.discover()
 tools=[t for s in servers for t in s["tools"]]
 untrusted=[t["name"] for t in tools if not t["trusted"]]
 disc=feed_entry(kind="discovery",servers=len(servers),tools=len(tools),untrusted=untrusted,
                 purpose=f"tools/list on {len(servers)} MCP servers: {len(tools)} tools found, {len(tools)-len(untrusted)} in the trusted registry",
                 decision="INFO",actor="pager-agent")
 event("MCP_DISCOVERY",disc)
 # Step 2: a read-only investigation where every tool call is checked by the gateway, then sent over MCP.
 for tool,args,purpose in INVESTIGATION_PLAN:
  await gateway_call(tool,purpose,args=args)
 event("INVESTIGATION_COMPLETE",{"leading_hypothesis":hypotheses()[0]["title"],"evidence":len(state["evidence"])})
 event("REMEDIATION_PROPOSED",{"actions":[a["id"] for a in get()]})
 return incident()

@router.post("/demo/reset")
def reset():
 state.clear(); state.update(fresh_state())
 pg.KILL_SWITCH=False
 event("DEMO_RESET",{"baseline":BASELINE})
 return {"ok":True,"message":"Demo reset to healthy baseline."}

@router.get("/incidents")
def incidents():
 return [incident()] if state["active"] else []

@router.get("/incidents/{incident_id}")
def incident(incident_id=None):
 risk=analyze(state["phase"])
 if not state["active"]: return {"status":"HEALTHY","incident_id":None,"risk":risk}
 return {"incident_id":state["incident_id"],"service":"payment-api","environment":"SANDBOX",
         "severity":analyze("incident")["severity"],"status":"RESOLVED" if state["executed"] else "INVESTIGATING","risk":risk}

@router.get("/metrics")
def metrics(): return {"active":state["active"],"baseline":BASELINE,"analysis":analyze(state["phase"])}

@router.get("/gateway/log")
def gateway_log(): return {"items":state["gateway"],"kill_switch":pg.KILL_SWITCH}

@router.post("/gateway/probe")
async def probe(body:Probe):
 gate,entry,_=await gateway_call(body.tool,"Safety probe: attempted on purpose to show the gateway's response",
                                 server=body.server,actor="demo-probe")
 return entry

@router.get("/mcp/servers")
async def mcp_servers():
 servers=await mcp_client.discover()
 sandbox={"name":"pager-sandbox","transport":"Mocked executor (simulated state, not an MCP server in this build)",
          "tools":[{"name":k,"description":None,"params":[],"readOnlyHint":v.get("readOnlyHint",False),"trusted":True,"tier":v["tier"]}
                   for k,v in TOOLS.items() if v["server"]=="pager-sandbox"]}
 return {"servers":servers+[sandbox]}

@router.get("/incidents/{incident_id}/evidence")
def evidence(incident_id:str): return {"items":state["evidence"],"correlation":correlate()}

@router.get("/incidents/{incident_id}/predictions")
def predictions(incident_id:str): return {"anomaly":analyze(state["phase"]),"deployment":score(),"hypotheses":hypotheses()}

@router.get("/incidents/{incident_id}/blast-radius")
def blast(incident_id:str): return graph(state["phase"])

@router.get("/blast-radius")
def blast_current(): return graph(state["phase"])

@router.post("/incidents/{incident_id}/recommendations")
def recommendations(incident_id:str): return {"items":get()}

NEXT_STEP={"ALLOW":"Gateway would allow this call.","REQUIRES_APPROVAL":"Needs a second teammate's approval before it can run.",
           "REQUIRES_CONFIRMATION":"Needs explicit operator confirmation before it can run.","DENY":"Gateway would block this call."}

@router.post("/actions/{action_id}/preview")
async def preview(action_id:str, body:PreviewRequest):
 action=next((x for x in get() if x["id"]==action_id),None)
 if not action: raise HTTPException(404,"Unknown action")
 gate,entry,_=await gateway_call(action["tool"],f"Dry run: {action['title']}",dry_run=True,actor="oncall.primary",
                           environment="SANDBOX",approval=approved_by(),requester=(state["approval"] or {}).get("requester"))
 result={"preview_id":"PRE-"+uuid.uuid4().hex[:8],"action":action,"environment":action["environment"],
         "exact_change":action["exact_change"],"diff":action["diff"],"blast_radius":action["affected"],"dry_run":True,
         "gateway":{"decision":gate["decision"],"reason":gate["reason"],"tier":gate["tier"],"next_step":NEXT_STEP[gate["decision"]]},
         "note":"Preview only. No system has been changed."}
 return result

@router.post("/actions/request-approval")
def request_approval(body:ApprovalRequest):
 if body.action_id!="ACT-ROLLBACK": raise HTTPException(400,"Only the rollback requires second-person approval.")
 state["approval"]={"id":"APR-"+uuid.uuid4().hex[:8],"status":"pending","requester":body.requester,"approver":None,"action_id":body.action_id}
 event("APPROVAL_REQUESTED",state["approval"],body.requester)
 return state["approval"]

@router.post("/approvals/{approval_id}/decision")
def decision(approval_id:str,body:Decision):
 a=state.get("approval")
 if not a or a["id"]!=approval_id: raise HTTPException(404,"Approval not found")
 if body.requester != a["requester"]:
  raise HTTPException(403,"Approval requester identity does not match the request.")
 if body.approver==a["requester"]:
  raise HTTPException(403,"Requester cannot approve their own action.")
 a["status"]="approved" if body.decision=="approve" else "rejected"; a["approver"]=body.approver
 event("APPROVAL_"+body.decision.upper(),a,body.approver)
 return a

@router.post("/actions/{action_id}/execute")
async def execute(action_id:str, body:Optional[ExecuteRequest]=None):
 body=body or ExecuteRequest()
 action=next((x for x in get() if x["id"]==action_id),None)
 if not action: raise HTTPException(404,"Unknown action")
 a=state["approval"]
 gate,_,result=await gateway_call(action["tool"],action["title"],actor="oncall.primary",environment="SANDBOX",
                            approval=approved_by() if action_id=="ACT-ROLLBACK" else None,
                            requester=(a or {}).get("requester"),confirmed=body.confirmed)
 if not gate["allowed"]: raise HTTPException(403,gate["reason"])
 if action_id=="ACT-READ":
  return {"status":"collected","message":"Read-only diagnostics collected and added to the evidence.","evidence":result["evidence"]}
 if action_id=="ACT-SCALE":
  event("SANDBOX_EXECUTION",{"action":"scale_workers","target":action["target"],"change":action["exact_change"]})
  return {"status":"done","message":"Sandbox workers scaled 4 → 6 (simulated). This buys time but does not fix the pool limit."}
 state["executed"]=True; state["phase"]="recovered"
 event("SANDBOX_EXECUTION",{"action":"rollback_deployment","target":action["target"],"change":action["exact_change"]})
 _,_,check=await gateway_call("get_metrics","Verify recovery after the rollback",args={"service":"payment-api","window_minutes":2})
 m=check["current"] if check else analyze("recovered")["current"]
 verified={"latency_ms":m["latency"],"db_connections":m["db"],"error_rate":m["errors"]}
 event("RECOVERY_VERIFIED",{**verified,"result":"PASS"})
 return {"status":"verified","message":"Sandbox rollback simulated; recovery verification passed.","metrics":verified}

@router.get("/incidents/{incident_id}/timeline")
def timeline(incident_id:str): return {"items":state["timeline"]}

@router.get("/audit")
def audit(): return {"items":store.audit()}

@router.get("/postmortem")
def postmortem():
 done=state["executed"]
 return {"incident_id":state["incident_id"],"status":"draft","summary":"A seeded database connection-pool configuration change was followed by elevated connection use, payment latency and connection-acquisition timeouts.",
 "impact":"Potential payment and checkout degradation inferred from the seeded dependency graph; customer impact is not measured.",
 "root_cause":"Leading hypothesis: connection-pool exhaustion after deployment v2.4.1. Not confirmed.",
 "timeline":state["timeline"],"gateway_calls":sum(1 for x in state["gateway"] if x["kind"]=="call"),
 "action":"Sandbox rollback of v2.4.1 configuration" if done else "No action executed yet.",
 "verification":"Passed using simulated recovery metrics." if done else "Pending sandbox remediation.",
 "follow_ups":["Validate pool sizing against peak concurrency","Add deployment soak checks for DB pool changes","Connect live telemetry and trace evidence"]}

@router.post("/policy/kill-switch")
def kill_switch(body:PolicySwitch):
 pg.KILL_SWITCH=body.enabled
 event("KILL_SWITCH_CHANGED",{"enabled":body.enabled},"security-admin")
 return {"enabled":pg.KILL_SWITCH}

TIERS=[
 {"id":"read_only","name":"Read-only","rule":"Allowed and audited","examples":"metrics, logs, deployments, runbooks"},
 {"id":"nonprod_write","name":"Non-production write","rule":"Operator must confirm; staging/sandbox only","examples":"scale sandbox workers, restart staging"},
 {"id":"production_write","name":"Production write","rule":"Second teammate must approve; executes in sandbox only","examples":"rollback, config change"},
 {"id":"destructive","name":"Destructive","rule":"Always blocked","examples":"drop database, delete data"}]

@router.get("/policy")
def policy():
 return {"tiers":TIERS,"tools":TOOLS,"kill_switch":pg.KILL_SWITCH,"unknown_default":"DENY"}

@router.get("/voice/briefing")
def voice():
 if not state["active"]: return {"text":"Pager is healthy. No active incident. The demo is using its seeded baseline.","mode":"browser_tts_fallback"}
 if state["executed"]: return {"text":"Pager update. The sandbox rollback of deployment v2.4.1 was approved by a second teammate and executed. Payment latency is back to 126 milliseconds and database connections to 46 percent. Recovery verification passed. A postmortem draft is ready.","mode":"browser_tts_fallback"}
 n=sum(1 for x in state["gateway"] if x["kind"]=="call" and x["transport"]=="mcp")
 return {"text":f"Pager predictive warning. Payment API latency is rising after deployment v2.4.1. I discovered the tools on four MCP servers and made {n} read-only MCP calls, each checked by the policy gateway first. Database connection usage is at 91 percent, and logs show connection acquisition timeouts. The leading hypothesis is database connection-pool exhaustion, not yet confirmed. I recommend reviewing the rollback preview. Production writes require a second teammate approval. This prototype will execute only in its sandbox.","mode":"browser_tts_fallback"}

@router.get("/memory")
def memory():
 return {"similar_incidents":[{"id":"INC-2026-014","service":"checkout","signature":"DB pool saturation + payment latency","resolution":"Rollback connection-pool configuration","similarity":"0.78 (heuristic)","source":"seeded incident memory"}]}
