import networkx as nx
from app.data.fixtures import SERVICES,EDGES,FAULT_SOURCE,INCIDENT_HEALTH

G=nx.DiGraph(); G.add_edges_from(EDGES)

def graph(phase="incident"):
 active=phase=="incident"
 # Everything that (transitively) depends on the faulty service can be affected.
 upstream=nx.ancestors(G,FAULT_SOURCE) if active else set()
 impacted=[s for s in SERVICES if s["id"] in upstream or (active and s["id"]==FAULT_SOURCE)]
 nodes=[{**s,"health":INCIDENT_HEALTH[s["id"]] if active else "healthy"} for s in SERVICES]
 # An edge is on the failure path when both ends are impacted and it leads toward the fault.
 ids={s["id"] for s in impacted}
 edges=[{"from":a,"to":b,"fault_path":active and a in ids and b in ids} for a,b in EDGES]
 return {"nodes":nodes,"edges":edges,"phase":phase,"fault_source":FAULT_SOURCE if active else None,
  "potential_impact":[s["name"] for s in impacted],
  "at_risk":sum(1 for n in nodes if n["health"]!="healthy"),
  "explanation":"Directed dependency traversal from the faulty service indicates potential upstream impact, not confirmed customer impact." if active
   else "No active fault. All services are at their simulated baseline."}
