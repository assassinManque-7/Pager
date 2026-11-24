"""The agent's read-only investigation plan: (tool, arguments, purpose), run in order on trigger.
Each step is checked by the policy gateway, then sent to the tool's MCP server."""
INVESTIGATION_PLAN=[
 ("get_metrics",{"service":"payment-api","window_minutes":10},"Confirm the anomaly in payment latency and DB connections"),
 ("get_logs",{"service":"payment-api","query":"timeout"},"Look for errors on the payment path"),
 ("get_deployments",{"service":"payment-api","limit":5},"Check for recent changes before the anomaly"),
 ("read_runbook",{"topic":"db-pool-saturation"},"Find the documented response for DB pool saturation"),
 ("search_incident_memory",{"signature":"db pool saturation + payment latency"},"Look for similar past incidents"),
]
# Arguments for actions the operator can run from the Approvals page.
ACTION_ARGS={"get_db_diagnostics":{"host":"orders-db"},"rollback_deployment":{"deployment":"v2.4.1","target":"sandbox/payment-platform"},
             "scale_workers":{"service":"payment-api","replicas":6}}
