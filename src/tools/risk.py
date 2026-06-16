import os
from typing import Any, Dict
from langchain_openai import ChatOpenAI
from src.graph.state import ChangeGuardState, LLMRiskAnalysis

# Read clean environment configs
LLM_MODEL = os.getenv("GROQ_LLM_MODEL") or os.getenv("GEMINI_LLM_MODEL")
API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("GROQ_BASE_URL") or os.getenv("GEMINI_BASE_URL")

llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.1
)
structured_llm = llm.with_structured_output(LLMRiskAnalysis)

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
        ai_analysis = structured_llm.invoke(system_prompt)
        return {
            "risk_score": ai_analysis.risk_score.upper(),
            "risk_factors": ai_analysis.risk_factors
        }
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"risk_score": "HIGH", "risk_factors": [f"LLM analysis failed: {str(e)}"]}