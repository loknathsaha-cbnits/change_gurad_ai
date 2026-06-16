import httpx
from typing import Any, Dict
from src.graph.state import ChangeGuardState

def pr_fetch_node(state: ChangeGuardState) -> Dict[str, Any]:
    print("--- FETCHING PR DIFF ---")
    diff_url = state["diff_url"]
    
    headers = {"User-Agent": "ChangeGuardAI-Agent"}
    response = httpx.get(diff_url, headers=headers)
    
    diff_text = response.text if response.status_code == 200 else "Error fetching diff"
    return {"git_diff": diff_text}