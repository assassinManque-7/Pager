def get():
 return [
 {"id":"ACT-ROLLBACK","tool":"rollback_deployment","title":"Rollback database configuration v2.4.1","benefit":"Restore previous connection-pool settings; expected to reduce acquisition contention.",
  "risk":"Medium","affected":["Orders DB","Payment API","Order Service","Checkout"],"preconditions":["Confirm target deployment v2.4.1","Review dry-run diff","Second-person approval"],
  "tier":"production_write","approval":"Second authorized teammate","target":"sandbox/payment-platform","environment":"SANDBOX",
  "exact_change":"config/database.yaml: pool.max 24 → 80 (revert deployment v2.4.1, simulated)",
  "diff":["- pool.max: 24","+ pool.max: 80"]},
 {"id":"ACT-SCALE","tool":"scale_workers","title":"Increase payment worker capacity (simulation)","benefit":"May reduce request queueing while investigation continues.","risk":"Medium","affected":["Payment API"],
  "preconditions":["Capacity headroom confirmed"],"tier":"nonprod_write","approval":"Explicit operator confirmation","target":"sandbox/payment-api","environment":"SANDBOX",
  "exact_change":"sandbox/payment-api: worker replicas 4 → 6 (simulated)",
  "diff":["- replicas: 4","+ replicas: 6"]},
 {"id":"ACT-READ","tool":"get_db_diagnostics","title":"Collect database host diagnostics","benefit":"Gather CPU, I/O and connection wait evidence.","risk":"Low","affected":["Orders DB"],
  "preconditions":["Read-only access"],"tier":"read_only","approval":"None","target":"monitoring/diagnostics","environment":"READ_ONLY",
  "exact_change":"No change. Reads CPU, I/O wait and connection-wait metrics for Orders DB.",
  "diff":[]}]
