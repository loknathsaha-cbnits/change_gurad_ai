import httpx
from typing import Any, Dict
from src.graph.state import ChangeGuardState

def pr_fetch_node(state: ChangeGuardState) -> Dict[str, Any]:
    print("--- FETCHING PR DIFF ---")
    diff_url = state["diff_url"]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/vnd.github.v3.diff"
    }
    
    response = httpx.get(diff_url, headers=headers, follow_redirects=True)
    
    print(f"[DEBUG] GitHub Status Code: {response.status_code}")
    
    if response.status_code == 200:
        diff_text = response.text
        print(f"[DEBUG] Success! Fetched Diff Content Length: {len(diff_text)} chars")
        print(f"[DEBUG] RAW DIFF CONTENT:\n{diff_text[:2000]}")
    else:
        print(f"[DEBUG] Raw Error Content: {response.text[:200]}")
        diff_text = "Error fetching diff"
        
    return {"git_diff": diff_text}