# Architecture & Sequence

PAGER uses an event-driven flow inspired by the project report: Monitoring → Event processing → MCP investigation → AI reasoning → Voice briefing → Policy gateway → Human approval → Execution → Verification → Audit, memory and postmortem.

The local prototype substitutes seeded monitoring/deployment/runbook adapters and a local MCP-compatible registry for live CloudWatch, EventBridge, GitHub and MCP services. The gateway is deterministic Python code outside any language model. The sandbox executor only updates simulated state.

```mermaid
sequenceDiagram
participant M as Metrics/Event
participant P as Pager API
participant T as MCP adapters
participant G as Policy gateway
participant H as Teammate
participant X as Sandbox executor
M->>P: Predictive warning
P->>T: Read metrics/logs/deploy/runbook
T-->>P: Evidence records
P->>P: Correlate + rank hypotheses
P-->>H: Browser voice briefing
H->>P: Preview rollback
P->>G: Evaluate tool identity + tier
G-->>P: Requires second approval
P->>H: Approval request
H->>P: Approve as separate teammate
P->>G: Re-evaluate authorization
G-->>P: Allow sandbox only
P->>X: Execute simulated rollback
X-->>P: Sandbox result
P->>P: Verify recovery metrics
P->>P: Persist audit + postmortem
```
