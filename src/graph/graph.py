from langgraph.graph import StateGraph, END
from src.graph.state import ChangeGuardState

from src.tools.assign_reviewer import assign_reviewer
from src.tools.email_sender import email_sender
from src.tools.fetch import pr_fetch_node
from src.tools.post_comment import post_comment_node
from src.tools.report import threat_report_node
from src.tools.risk import risk_assessment_node

def route_on_risk(state: ChangeGuardState) -> str:
    risk = (state.get("risk_score") or "").strip().upper()
    if risk == "HIGH":
        return "assign_reviewer"
    return "end"

workflow = StateGraph(ChangeGuardState)
workflow.add_node("fetch_pr", pr_fetch_node)
workflow.add_node("assess_risk", risk_assessment_node)
workflow.add_node("generate_report", threat_report_node)
workflow.add_node("post_comment", post_comment_node)
workflow.add_node("assign_reviewer", assign_reviewer)
workflow.add_node("send_email", email_sender)

workflow.set_entry_point("fetch_pr")
workflow.add_edge("fetch_pr", "assess_risk")
workflow.add_edge("assess_risk", "generate_report")
workflow.add_edge("generate_report", "post_comment")
workflow.add_conditional_edges(
    "post_comment",
    route_on_risk,
    {
        "assign_reviewer": "assign_reviewer",
        "end": END
    }
)
workflow.add_edge("assign_reviewer", "send_email")
workflow.add_edge("send_email", END) 

change_guard_agent = workflow.compile()