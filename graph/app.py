# graph/app.py
import os, sys
# make sure Python can import sibling package "mcp" no matter how you run the script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import TypedDict, Dict, Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from mcp.server import (
    md_quote, md_last_trade, risk_check,
    broker_place_order, journal_log
)

load_dotenv()  # picks up DEFAULT_SYMBOL if you set it in .env

class TradeState(TypedDict, total=False):
    symbol: str
    signal: Dict[str, Any]
    market_snapshot: Dict[str, Any]
    recommendation: Dict[str, Any]
    risk_report: Dict[str, Any]
    approval: bool
    execution_report: Dict[str, Any]
    journal_id: str

def node_market(state: TradeState) -> TradeState:
    # Be tolerant: use state.symbol -> env DEFAULT_SYMBOL -> "AAPL"
    sym = state.get("symbol") or os.getenv("DEFAULT_SYMBOL", "AAPL")
    state["symbol"] = sym  # persist so downstream nodes always have it
    q = md_quote([sym])[0]
    t = md_last_trade(sym)
    state["market_snapshot"] = {"quote": q, "trade": t}
    return state

def node_risk(state: TradeState) -> TradeState:
    last = state["market_snapshot"]["trade"]["price"]
    sig  = state.get("signal", {"side": "buy", "qty": 1})  # fallback if missing
    rec = {
        "symbol": state["symbol"],
        "side": sig["side"],
        "qty": sig["qty"],
        "entry": last,
        "stop": sig.get("stop"),
        "tp": sig.get("tp"),
        "type": "market",
    }
    rr = risk_check(rec)
    state["recommendation"] = rec
    state["risk_report"] = rr
    return state

def node_approval(state: TradeState) -> TradeState:
    # Day 2: auto-approve if risk passes (Day 3 will prompt)
    state["approval"] = bool(state.get("risk_report", {}).get("pass"))
    return state

def node_exec(state: TradeState) -> TradeState:
    if not state.get("approval"):
        return state
    rep = broker_place_order({
        "symbol": state["symbol"],
        "side": state["recommendation"]["side"],
        "qty": state["recommendation"]["qty"],
        "type": "market",
        "stop": state["recommendation"].get("stop"),
        "tp": state["recommendation"].get("tp"),
    })
    state["execution_report"] = rep
    return state

def node_journal(state: TradeState) -> TradeState:
    jid = journal_log({"state": state})["id"]
    state["journal_id"] = jid
    print(f"Journaled: {jid}")
    return state

graph = StateGraph(dict)
graph.add_node("market", node_market)
graph.add_node("risk", node_risk)
graph.add_node("approval", node_approval)
graph.add_node("exec", node_exec)
graph.add_node("journal", node_journal)

graph.add_edge(START, "market")
graph.add_edge("market", "risk")

def route_after_risk(s: TradeState):
    return "approval" if s["risk_report"]["pass"] else "journal"
graph.add_conditional_edges("risk", route_after_risk, {"approval":"approval","journal":"journal"})

def route_after_approval(s: TradeState):
    return "exec" if s.get("approval") else "journal"
graph.add_conditional_edges("approval", route_after_approval, {"exec":"exec","journal":"journal"})

graph.add_edge("exec", "journal")
graph.add_edge("journal", END)

app = graph.compile()

if __name__ == "__main__":
    # ALWAYS pass an initial state
    symbol = os.getenv("DEFAULT_SYMBOL", "AAPL")
    demo_state: TradeState = {
        "symbol": symbol,
        "signal": {"side": "buy", "qty": 5, "stop": 98.0, "tp": 102.0},
    }
    app.invoke(demo_state)
