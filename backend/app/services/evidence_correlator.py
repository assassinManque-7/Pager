from app.data.fixtures import EVIDENCE
def collect(): return EVIDENCE
def correlate(): return {"correlation":"Strong temporal and service-path correlation","evidence_ids":["EV-01","EV-02","EV-03","EV-04","EV-05"],
 "summary":"The connection-pool configuration deployment precedes rising DB connection usage, followed by payment latency and acquisition timeouts.",
 "gaps":["No live distributed trace export","No production deployment API connected"]}
