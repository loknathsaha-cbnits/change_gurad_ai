import os
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from src.graph.state import ChangeGuardState

# 1. FIX THE IMPORT: Import the actual Google Native Driver
from langchain_google_genai import ChatGoogleGenerativeAI

class DetailedRiskFactor(BaseModel):
    file_name: str = Field(description="The path/name of the file where the vulnerability was found.")
    line_snippet: str = Field(description="The exact snippet or specific lines of code introducing the threat.")
    vulnerability_type: str = Field(description="Category e.g., SQL Injection, Hardcoded Secret, Breaking Schema Migration.")
    explanation: str = Field(description="Deep technical analysis explaining exactly why this is a production deployment risk.")
    remediation: str = Field(description="Clear, step-by-step instructions showing how the developer can rewrite this code securely.")

class LLMRiskAnalysis(BaseModel):
    risk_score: str = Field(description="Must be exactly 'LOW', 'MEDIUM', or 'HIGH'")
    detailed_findings: List[DetailedRiskFactor] = Field(description="List of isolated code level risk factors found within the diff.")

# --- INITIALIZATION DIAGNOSTICS ---
LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-1.5-flash")
API_KEY = os.getenv("GEMINI_API_KEY")

print("\n=== CHANGEGUARD INITIALIZATION LOGS ===")
print(f"[DEBUG INITIALIZATION] Target Model Configured: '{LLM_MODEL}'")
print(f"[DEBUG INITIALIZATION] API Key Present: {True if API_KEY else False}")
print("========================================\n")

# Use native class to execute structured payloads over Google's gateway
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL, 
    google_api_key=API_KEY, 
    temperature=0.1
)
structured_llm = llm.with_structured_output(LLMRiskAnalysis)

def risk_assessment_node(state: ChangeGuardState) -> Dict[str, Any]:
    print("--- ASSESSING DEPLOYMENT RISK WITH NATIVE GEMINI ---")
    git_diff = state.get("git_diff", "")
    
    if not git_diff or git_diff == "Error fetching diff":
        print("[DEBUG RISK NODE] Error: Git Diff data empty or missing!")
        return {
            "risk_score": "HIGH",
            "risk_factors": [] 
        }

    print(f"[DEBUG RISK NODE] Forwarding {len(git_diff)} characters of Diff data to Gemini API...")

    system_prompt = (
        "You are an enterprise-grade automated DevOps and Security Review Agent.\n"
        "Analyze the provided Git Diff code submission. Isolate vulnerabilities, structural code hazards, "
        "hardcoded credentials, and high blast-radius database mistakes.\n\n"
        f"Git Diff Data:\n{git_diff}"
    )

    try:
        ai_analysis = structured_llm.invoke(system_prompt)
        print("[DEBUG RISK NODE] Successfully received structured response from Gemini!")
        print(f"[DEBUG RISK NODE] Extracted Risk Classification: {ai_analysis.risk_score}")
        print(f"[DEBUG RISK NODE] Total Vulnerabilities Identified: {len(ai_analysis.detailed_findings)}")
        
        return {
            "risk_score": ai_analysis.risk_score.upper(),
            "risk_factors": ai_analysis.detailed_findings 
        }
    except Exception as e:
        print(f"\n[!!! CRITICAL CRASH IN RISK NODE !!!] Exception Message: {e}")
        return {"risk_score": "HIGH", "risk_factors": []}