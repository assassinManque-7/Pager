from app.mcp.policy_gateway import evaluate
def test_read_only_allowed(): assert evaluate("get_metrics")["allowed"]
def test_unknown_denied(): assert not evaluate("unknown_tool",server="untrusted")["allowed"]
def test_destructive_denied(): assert not evaluate("drop_database")["allowed"]
def test_production_write_requires_approval(): assert evaluate("rollback_deployment",environment="SANDBOX")["decision"]=="REQUIRES_APPROVAL"
def test_self_approval_denied(): assert not evaluate("rollback_deployment",environment="SANDBOX",approval="alice",requester="alice")["allowed"]
def test_approved_sandbox_write_allowed(): assert evaluate("rollback_deployment",environment="SANDBOX",approval="bob",requester="alice")["allowed"]
def test_staging_only_for_nonprod(): assert not evaluate("restart_staging",environment="PRODUCTION")["allowed"]
