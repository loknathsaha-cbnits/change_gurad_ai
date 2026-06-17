from langgraph.graph import StateGraph, END
from src.graph.state import ChangeGuardState
from src.tools.fetch import pr_fetch_node
from src.tools.report import threat_report_node
from src.tools.risk import risk_assessment_node

workflow = StateGraph(ChangeGuardState)
workflow.add_node("fetch_pr", pr_fetch_node)
workflow.add_node("assess_risk", risk_assessment_node)
workflow.add_node("generate_report", threat_report_node)

workflow.set_entry_point("fetch_pr")
workflow.add_edge("fetch_pr", "assess_risk")
workflow.add_edge("assess_risk", "generate_report")
workflow.add_edge("generate_report", END)

change_guard_agent = workflow.compile()