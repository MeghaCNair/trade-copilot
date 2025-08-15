
import time, json, pathlib
from typing import List, Dict, Any

# ---- STUB IMPLEMENTATION (replaced with Alpaca on Day 3) ----
JOURNAL_DIR = pathlib.Path("journal"); JOURNAL_DIR.mkdir(exist_ok=True)

def md_quote(symbols: List[str]) -> List[Dict[str, Any]]:
    # deterministic fake quote
    out = []
    for s in symbols:
        out.append({"symbol": s, "bid": 100.00, "ask": 100.05, "bid_size": 10, "ask_size": 12, "ts": "1970-01-01T00:00:00Z"})
    return out

def md_last_trade(symbol: str) -> Dict[str, Any]:
    return {"symbol": symbol, "price": 100.02, "size": 1, "ts": "1970-01-01T00:00:00Z"}

def broker_place_order(order: Dict[str, Any]) -> Dict[str, Any]:
    # pretend the broker accepted it
    return {"id": "SIM-ORDER-1", "symbol": order["symbol"], "side": order["side"], "qty": order["qty"], "status": "accepted"}

def risk_check(order: Dict[str, Any]) -> Dict[str, Any]:
    # very permissive for Day 2: pass if a stop exists
    reasons = []
    if not order.get("stop"):
        reasons.append("No stop provided (required).")
    return {"pass": len(reasons) == 0, "reasons": reasons, "limits": {"max_trade_risk": 100.0}}

def journal_log(entry: Dict[str, Any]) -> Dict[str, Any]:
    day = time.strftime("%Y%m%d")
    path = JOURNAL_DIR / f"{day}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return {"id": f"{day}:{int(time.time())}", "path": str(path)}

