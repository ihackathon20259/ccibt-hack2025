from agent import root_handle

def test_report():
    out = root_handle("Show me my wire status report for last 30 days cust_001")
    assert out["payload"]["kind"] == "report_card"

def test_upgrade_needs_confirmation():
    out = root_handle("Upgrade me to Pro cust_001")
    assert out["payload"]["kind"] == "upgrade_decision"
    assert out["payload"]["requires_confirmation"] is True
