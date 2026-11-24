from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_demo_lifecycle():
 client.post("/api/demo/reset")
 r=client.post("/api/incidents/trigger",json={}); assert r.status_code==200
 iid=r.json()["incident_id"]
 assert client.get(f"/api/incidents/{iid}/evidence").status_code==200
 client.post(f"/api/actions/ACT-ROLLBACK/preview",json={"environment":"SANDBOX"})
 a=client.post("/api/actions/request-approval",json={"action_id":"ACT-ROLLBACK","requester":"alice"}).json()
 assert client.post(f"/api/approvals/{a['id']}/decision",json={"decision":"approve","approver":"alice","requester":"alice"}).status_code==403
 assert client.post(f"/api/approvals/{a['id']}/decision",json={"decision":"approve","approver":"bob","requester":"alice"}).status_code==200
 assert client.post("/api/actions/ACT-ROLLBACK/execute").json()["status"]=="verified"
 assert client.get("/api/postmortem").json()["verification"].startswith("Passed")
 client.post("/api/demo/reset")
