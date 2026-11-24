# Judge demo (3 minutes)

The story: **the agent can only act through MCP tools, and every tool call passes a deterministic policy gateway first.**

1. **Healthy baseline (15s):** On Overview, point at the Agent loop strip and the Policy tiers. "Everything from Investigate onward goes through the gateway."
2. **Trigger (30s):** Click Trigger incident. In the Gateway feed: MCP discovery (`tools/list` on 4 real MCP servers), then 5 read-only calls, each ALLOW → SENT VIA MCP. The agent loop moves to Propose.
3. **Safety proof (20s):** Click Try drop_database (DESTRUCTIVE → DENY) and Try purge_logs. `purge_logs` is a real tool on a real MCP server that calls itself read-only, but the gateway denies it: annotations are metadata, not authorization. Both are NOT SENT.
4. **Investigate (20s):** Investigation page shows the evidence, each tagged with the MCP tool and server it came from, plus ranked hypotheses with uncertainty.
5. **Dry runs (25s):** On Approvals, dry-run all three actions: ALLOW, NEEDS CONFIRM and NEEDS APPROVAL. Open the service map from the rollback preview to show the blast radius.
6. **Approval (25s):** Request approval as `oncall.primary`; approve as `teammate.approver`. The requester cannot approve their own action.
7. **Execute and verify (20s):** Execute the sandbox rollback. The gateway re-checks the approval; the write goes to the sandbox mock; the agent verifies with an MCP `get_metrics` call. Overview turns green.
8. **Voice and close (25s):** Play the voice briefing (browser speech, no phone call). Optional: Policy & security shows the connected MCP servers, and the kill switch blocks the rollback.

Be honest when asked: read-only tools are real MCP servers with seeded data; write tools are mocked in a sandbox; no cloud services are connected.

Backup path: if browser speech is unavailable, read the text briefing. If the network is unavailable, keep the local API and UI running; everything runs locally.
