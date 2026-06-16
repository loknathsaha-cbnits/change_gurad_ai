from fastapi import FastAPI, Request, BackgroundTasks
from src.graph.graph import change_guard_agent

app = FastAPI()

def run_ai_workflow(initial_state: dict):
    # Asynchronously runs the LangGraph workflow
    result = change_guard_agent.invoke(initial_state)
    print("\n=== FINAL WORKFLOW OUTPUT ===")
    print(result["threat_report"])

@app.post("/github/webhook")
async def github_webhook_endpoint(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    
    # Verify this is a pull request event action we care about
    if "pull_request" in payload:
        action = payload.get("action")
        # Trigger on opened, synchronized (new commits pushed), or reopened
        if action in ["opened", "synchronize", "reopened"]:
            pr_data = payload["pull_request"]
            
            # Extract necessary details matching your state keys
            initial_state = {
                "pr_url": pr_data.get("html_url"),
                "diff_url": pr_data.get("diff_url"), # GitHub provides direct raw diff links
                "git_diff": "",
                "risk_score": "",
                "risk_factors": [],
                "threat_report": ""
            }
            
            print(f"Triggering ChangeGuard AI for PR #{payload.get('number')}")
            # Offload processing to background task so GitHub doesn't timeout waiting
            background_tasks.add_task(run_ai_workflow, initial_state)
            
            return {"status": "workflow_initiated"}

    return {"status": "ignored_event"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)