from app.data.fixtures import BASELINE,HEALTHY_METRICS,INCIDENT_METRICS,RECOVERY_METRICS
# Ceilings used to normalise each signal's deviation from baseline (0 = baseline, 1 = ceiling).
CEILING={"latency":400,"db":100,"errors":5.0}
WEIGHTS={"latency":35,"db":40,"errors":25}
BASE={"latency":BASELINE["latency_ms"],"db":BASELINE["db_connections"],"errors":BASELINE["error_rate"]}
SERIES={"healthy":HEALTHY_METRICS,"incident":INCIDENT_METRICS,"recovered":RECOVERY_METRICS}

def risk(current):
    total=0
    for k,w in WEIGHTS.items():
        dev=(current[k]-BASE[k])/(CEILING[k]-BASE[k])
        total+=w*min(1,max(0,dev))
    return round(total)

def analyze(phase="incident"):
    series=SERIES[phase]
    cur=series[-1]
    score=risk(cur)
    severity="critical" if score>=80 else "high" if score>=60 else "elevated" if score>=30 else "healthy"
    label={"healthy":"Healthy baseline","incident":"Predictive warning","recovered":"Recovered after sandbox rollback"}[phase]
    signals=[
        {"name":"DB connection usage","value":f"{cur['db']}%","baseline":f"{BASE['db']}%","change":f"{cur['db']-BASE['db']:+} pp"},
        {"name":"Payment P95 latency","value":f"{cur['latency']} ms","baseline":f"{BASE['latency']} ms","change":f"{round((cur['latency']/BASE['latency']-1)*100):+}%"},
        {"name":"Error rate","value":f"{cur['errors']}%","baseline":f"{BASE['errors']}%","change":f"{round(cur['errors']-BASE['errors'],1):+} pp"}]
    return {"risk_score":score,"severity":severity,"label":label,"phase":phase,"heuristic":True,
            "current":{"latency":cur["latency"],"db":cur["db"],"errors":cur["errors"]},
            "explanation":"Weighted deviation from baseline: latency 35, DB connections 40, error rate 25 points, each scaled between baseline and a fixed ceiling. "
                          "It is a transparent prototype heuristic, not a calibrated outage probability.",
            "signals":signals,"series":series}
