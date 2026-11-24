from app.mcp.registry import TRUSTED_SERVERS,TOOLS
KILL_SWITCH=False
def evaluate(tool, server=None, environment="SANDBOX", actor="operator", approval=None, requester=None, confirmed=False):
 spec=TOOLS.get(tool)
 server=server or (spec or {}).get("server")
 if not spec or server not in TRUSTED_SERVERS or spec["server"]!=server:
  return {"allowed":False,"decision":"DENY","reason":"Unknown tool/server: strict default deny.","tier":"unknown"}
 tier=spec["tier"]
 if KILL_SWITCH and tier!="read_only":
  return {"allowed":False,"decision":"DENY","reason":"Global kill switch is active: writes are disabled.","tier":tier}
 if tier=="destructive":
  return {"allowed":False,"decision":"DENY","reason":"Destructive operations are prohibited.","tier":tier}
 if tier=="production_write":
  if environment!="SANDBOX":
   return {"allowed":False,"decision":"DENY","reason":"This prototype executes writes only in SANDBOX.","tier":tier}
  if not approval:
   return {"allowed":False,"decision":"REQUIRES_APPROVAL","reason":"Second authorized teammate approval required.","tier":tier}
  if requester and approval==requester:
   return {"allowed":False,"decision":"DENY","reason":"Requester cannot approve their own action.","tier":tier}
 if tier=="nonprod_write":
  if environment not in ("STAGING","SANDBOX"):
   return {"allowed":False,"decision":"DENY","reason":"Non-production action requires STAGING or SANDBOX.","tier":tier}
  if not confirmed:
   return {"allowed":False,"decision":"REQUIRES_CONFIRMATION","reason":"Operator must explicitly confirm this write.","tier":tier}
 return {"allowed":True,"decision":"ALLOW","reason":"Trusted registry identity and local policy checks passed.","tier":tier}
