from typing import Any, Dict
from src.graph.state import ChangeGuardState

def threat_report_node(state: ChangeGuardState) -> Dict[str, Any]:
    print("--- GENERATING THREAT REPORT ---")
    score = state.get("risk_score", "UNKNOWN")
    factors = "\n".join([f"- {f}" for f in state.get("risk_factors", [])])
    
    report = f"## ChangeGuard AI Threat Report\n\n**Risk Level:** {score}\n\n### Findings:\n{factors}"
    return {"threat_report": report}