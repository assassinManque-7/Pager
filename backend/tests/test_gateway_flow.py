from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def start():
 client.post("/api/demo/reset")
 return client.post("/api/incidents/trigger",json={}).json()["incident_id"]

def test_investigation_runs_through_gateway():
 iid=start()
 feed=client.get("/api/gateway/log").json()["items"]
 assert feed[0]["kind"]=="discovery" and feed[0]["untrusted"]==["purge_logs"]
 log=[x for x in feed if x["kind"]=="call"]
 assert [x["tool"] for x in log]==["get_metrics","get_logs","get_deployments","read_runbook","search_incident_memory"]
 assert all(x["decision"]=="ALLOW" and x["tier"]=="read_only" and x["transport"]=="mcp" and "error" not in x for x in log)
 # Evidence comes only from the tool calls the gateway allowed.
 ev=client.get(f"/api/incidents/{iid}/evidence").json()["items"]
 assert {e["tool"] for e in ev}=={x["tool"] for x in log}
 assert client.get("/api/status").json()["stage"]=="propose"

def test_dry_runs_are_per_action():
 start()
 got={a:client.post(f"/api/actions/{a}/preview",json={}).json() for a in ("ACT-ROLLBACK","ACT-SCALE","ACT-READ")}
 assert got["ACT-ROLLBACK"]["gateway"]["decision"]=="REQUIRES_APPROVAL"
 assert got["ACT-SCALE"]["gateway"]["decision"]=="REQUIRES_CONFIRMATION"
 assert got["ACT-READ"]["gateway"]["decision"]=="ALLOW"
 assert len({g["exact_change"] for g in got.values()})==3
 # A dry run must not change anything.
 assert client.get("/api/status").json()["phase"]=="incident"

def test_probes_are_denied_and_logged():
 start()
 assert client.post("/api/gateway/probe",json={"tool":"drop_database"}).json()["decision"]=="DENY"
 assert client.post("/api/gateway/probe",json={"tool":"delete_bucket","server":"unknown-mcp"}).json()["decision"]=="DENY"
 assert client.get("/api/gateway/log").json()["items"][-1]["tier"]=="unknown"

def test_scale_needs_confirmation_and_read_adds_evidence():
 iid=start()
 assert client.post("/api/actions/ACT-SCALE/execute",json={}).status_code==403
 assert client.post("/api/actions/ACT-SCALE/execute",json={"confirmed":True}).status_code==200
 assert client.post("/api/actions/ACT-READ/execute",json={}).status_code==200
 assert "EV-07" in {e["id"] for e in client.get(f"/api/incidents/{iid}/evidence").json()["items"]}

def test_kill_switch_blocks_rollback_then_recovery_resets_dashboard():
 iid=start()
 a=client.post("/api/actions/request-approval",json={"action_id":"ACT-ROLLBACK","requester":"alice"}).json()
 client.post(f"/api/approvals/{a['id']}/decision",json={"decision":"approve","approver":"bob","requester":"alice"})
 client.post("/api/policy/kill-switch",json={"enabled":True})
 r=client.post("/api/actions/ACT-ROLLBACK/execute",json={})
 assert r.status_code==403 and "kill switch" in r.json()["detail"]
 client.post("/api/policy/kill-switch",json={"enabled":False})
 assert client.post("/api/actions/ACT-ROLLBACK/execute",json={}).json()["status"]=="verified"
 s=client.get("/api/status").json()
 assert s["stage"]=="resolved" and s["phase"]=="recovered"
 m=client.get("/api/metrics").json()["analysis"]
 assert m["severity"]=="healthy" and m["current"]["latency"]==126
 assert client.get(f"/api/incidents/{iid}/blast-radius").json()["at_risk"]==0
 client.post("/api/demo/reset")

def test_blast_radius_follows_dependency_edges():
 iid=start()
 g=client.get(f"/api/incidents/{iid}/blast-radius").json()
 assert set(g["potential_impact"])=={"API Gateway","Checkout","Payment API","Order Service","Orders DB"}
 assert g["at_risk"]==4
 client.post("/api/demo/reset")
