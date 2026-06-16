import os
import httpx
from typing import Any, Dict, List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from src.graph.state import ChangeGuardState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL = os.getenv("GEMINI_LLM_MODEL")
API_KEY=os.getenv("GEMINI_API_KEY")
BASE_URL=os.getenv("GEMINI_BASE_URL")

class LLMRiskAnalysis(BaseModel):
    risk_score: str = Field(description="Must be exactly 'LOW', 'MEDIUM', or 'HIGH'")
    risk_factors: List[str] = Field(description="List of specific structural or security deployment risk factors found in the diff.")

llm = ChatOpenAI(model= LLM_MODEL,
                 api_key = API_KEY,
                 base_url = BASE_URL,
                 temperature= 0.1,)
structured_llm = llm.with_structured_output(LLMRiskAnalysis)

def pr_fetch_node(state: ChangeGuardState) -> Dict[str, Any]:
    print("--- FETCHING PR DIFF ---")
    diff_url = state["diff_url"]
    response = httpx.get(diff_url)
    diff_text = response.text if response.status_code == 200 else "Error fetching diff"
    return {"git_diff": diff_text}

def risk_assessment_node(state: ChangeGuardState) -> Dict[str, Any]:
    print("--- ASSESSING DEPLOYMENT RISK WITH LLM ---")
    git_diff = state.get("git_diff", "")
    
    if not git_diff or git_diff == "Error fetching diff":
        return {"risk_score": "HIGH", "risk_factors": ["Could not parse PR code changes securely."]}

    system_prompt = (
        "You are an expert Enterprise DevOps and Security Agent. Analyze the following GitHub Git Diff "
        "for structural deployment risks, breaking database migrations, cascading retry hazards, "
        "and critical security vulnerabilities.\n\n"
        f"Git Diff:\n{git_diff}"
    )

    try:
        # Invoke the structured model
        ai_analysis = structured_llm.invoke(system_prompt)
        
        # Returns a clean dictionary matching your state modifications
        return {
            "risk_score": ai_analysis.risk_score.upper(),
            "risk_factors": ai_analysis.risk_factors
        }
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"risk_score": "HIGH", "risk_factors": [f"LLM analysis failed: {str(e)}"]}


# Node 3: Compile markdown report for the UI
def threat_report_node(state: ChangeGuardState) -> Dict[str, Any]:
    print("--- GENERATING THREAT REPORT ---")
    score = state.get("risk_score", "UNKNOWN")
    factors = "\n".join([f"- {f}" for f in state.get("risk_factors", [])])
    
    report = f"## ChangeGuard AI Threat Report\n\n**Risk Level:** {score}\n\n### Findings:\n{factors}"
    return {"threat_report": report}


# Build the Week 1 Graph workflow
workflow = StateGraph(ChangeGuardState)
workflow.add_node("fetch_pr", pr_fetch_node)
workflow.add_node("assess_risk", risk_assessment_node)
workflow.add_node("generate_report", threat_report_node)

workflow.set_entry_point("fetch_pr")
workflow.add_edge("fetch_pr", "assess_risk")
workflow.add_edge("assess_risk", "generate_report")
workflow.add_edge("generate_report", END)

change_guard_agent = workflow.compile()