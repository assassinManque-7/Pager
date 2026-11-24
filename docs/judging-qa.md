# Judge Q&A

**Why MCP?** MCP standardizes tool discovery and invocation. The read-only tools are real MCP servers (official Python SDK); the agent discovers them with `tools/list` and calls them with `tools/call`. PAGER's differentiator is that a trusted registry and deterministic policy gateway decide every call *before* it reaches a server, independently of model output and of what the server claims about itself.

**Is the MCP real?** Yes for discovery and the read-only tools (seeded data behind them). The write tools (rollback, scaling) are mocked in a sandbox. Any read-only server can run standalone over stdio: `python -m app.mcp.servers pager-monitoring`.

**Can the AI roll back production by itself?** No. It proposes; deterministic policy checks the registered tool, environment and approval; a second teammate approves. This prototype executes only against simulated sandbox state.

**Is the risk score (67/100) or the 82% an outage probability?** No. The risk score is a transparent weighted heuristic of how far latency, DB connections and error rate are from baseline. The 82% is the heuristic confidence of the leading root-cause hypothesis. Neither is a calibrated probability.

**Is the root cause confirmed?** No. Database pool exhaustion is the leading evidence-backed hypothesis; alternatives and evidence gaps are shown.

**Are metrics live?** No. They are seeded fixtures. CloudWatch/EventBridge/GitHub/Bedrock/ElevenLabs/Slack adapters are planned and require credentials and integration work.

**What happens if a tool is unknown or destructive?** Unknown tools/servers default deny; destructive operations are blocked.

**What if voice fails?** Browser text fallback remains available; normal alerting remains additive and should stay enabled.
