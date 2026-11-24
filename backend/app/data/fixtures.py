BASELINE={"latency_ms":118,"db_connections":42,"error_rate":0.4,"cpu":38,"memory":54}
HEALTHY_METRICS=[
 {"t":"-10m","latency":118,"db":42,"errors":0.4},{"t":"-8m","latency":120,"db":43,"errors":0.4},
 {"t":"-6m","latency":116,"db":41,"errors":0.3},{"t":"-4m","latency":122,"db":44,"errors":0.4},
 {"t":"-2m","latency":119,"db":42,"errors":0.4},{"t":"now","latency":118,"db":42,"errors":0.4}]
INCIDENT_METRICS=[
 {"t":"-10m","latency":118,"db":42,"errors":0.4},{"t":"-8m","latency":126,"db":48,"errors":0.5},
 {"t":"-6m","latency":149,"db":57,"errors":0.7},{"t":"-4m","latency":181,"db":69,"errors":1.0},
 {"t":"-2m","latency":236,"db":82,"errors":1.8},{"t":"now","latency":284,"db":91,"errors":2.7}]
# Simulated readings after the sandbox rollback.
RECOVERY_METRICS=INCIDENT_METRICS[:-1]+[
 {"t":"rollback","latency":284,"db":91,"errors":2.7},{"t":"+1m","latency":171,"db":63,"errors":1.1},
 {"t":"+2m","latency":126,"db":46,"errors":0.3}]
SERVICES=[
 {"id":"edge","name":"API Gateway","role":"Edge ingress","x":90,"y":160},
 {"id":"checkout","name":"Checkout","role":"Orchestration","x":290,"y":160},
 {"id":"payment","name":"Payment API","role":"Transaction path","x":500,"y":75},
 {"id":"orders","name":"Order Service","role":"Order writes","x":500,"y":245},
 {"id":"database","name":"Orders DB","role":"Connection pool","x":710,"y":160}]
# (a, b) means service a calls / depends on service b.
EDGES=[["edge","checkout"],["checkout","payment"],["checkout","orders"],["payment","database"],["orders","database"]]
FAULT_SOURCE="database"
# Simulated health of each service while the incident is active.
INCIDENT_HEALTH={"edge":"healthy","checkout":"degraded","payment":"degraded","orders":"at-risk","database":"critical"}
EVIDENCE=[
 {"id":"EV-01","tool":"get_metrics","source":"CloudWatch (simulated)","kind":"metric","service":"database","time":"17:02:10","signal":"DB connection pool","value":"91% (baseline 42%)","detail":"Connection usage rose steadily across the last 10 minutes."},
 {"id":"EV-02","tool":"get_metrics","source":"APM fixture","kind":"metric","service":"payment-api","time":"17:02:18","signal":"Payment P95 latency","value":"284 ms (baseline 118 ms)","detail":"Latency increase follows the database connection growth."},
 {"id":"EV-03","tool":"get_logs","source":"Application logs (fixture)","kind":"log","service":"payment-api","time":"17:02:22","signal":"Connection acquisition timeout","value":"37 occurrences","detail":"Pool acquisition timed out while waiting for a database connection."},
 {"id":"EV-04","tool":"get_deployments","source":"GitHub deployment fixture","kind":"deployment","service":"database","time":"16:58:00","signal":"Deployment v2.4.1","value":"pool.max: 80 → 24","detail":"Recent connection-pool configuration change; deployment risk factors include pool reduction and payment-path scope."},
 {"id":"EV-05","tool":"read_runbook","source":"Runbook fixture","kind":"runbook","service":"payment-api","time":"Static","signal":"DB pool saturation runbook","value":"Rollback last config deployment","detail":"Runbook recommends validating pool saturation and rolling back the last configuration change after approval."},
 {"id":"EV-06","tool":"search_incident_memory","source":"Incident memory","kind":"memory","service":"checkout","time":"2026-10-19","signal":"Similar incident INC-2026-014","value":"Resolved by config rollback","detail":"A previous checkout latency incident had a similar connection-timeout signature. Similarity is heuristic."}
]
DIAGNOSTICS={"id":"EV-07","tool":"get_db_diagnostics","source":"DB host diagnostics (fixture)","kind":"metric","service":"database","time":"17:04:40","signal":"DB host CPU / I/O wait","value":"CPU 41% · I/O wait 3%","detail":"Host resources are not saturated, which weakens the host-saturation hypothesis."}
