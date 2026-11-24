# Policy matrix & threat model

| Tier | Example | Rule |
|---|---|---|
| Read-only | metrics/logs/deploy/runbook | Normal authorization; audit |
| Non-production write | staging restart | Explicit confirmation; STAGING/SANDBOX only |
| Production write | production rollback/config change | Explicit confirmation + second authorized teammate; prototype executes sandbox only |
| Destructive | drop database/delete critical data/disable safeguards | Deny outright |

The registry is allow-listed. MCP annotations are metadata only. Unknown servers/tools are denied. Voice is not identity proof. Untrusted retrieved text is evidence, never instructions. The kill switch blocks agent-initiated writes. The demo approval identities are illustrative and must be replaced with authenticated SSO/RBAC before real use.
