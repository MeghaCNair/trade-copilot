import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mcp.server import risk_check

def test_requires_stop():
    rr = risk_check({"symbol": "AAPL", "side": "buy", "qty": 5, "entry": 100.0})
    assert rr["pass"] is False
    assert any("stop" in r.lower() for r in rr["reasons"])