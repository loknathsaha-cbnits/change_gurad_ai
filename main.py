import os
from dotenv import load_dotenv

# print("\n=== SYSTEM ENV LOADING VERIFICATION ===")
# 1. Boot the environment injector
load_dotenv()

# 2. Extract and print current diagnostics directly to the terminal console
gemini_model = os.getenv("GEMINI_LLM_MODEL")
gemini_key = os.getenv("GEMINI_API_KEY")

# print(f"[ENV DIAGNOSTIC] GEMINI_LLM_MODEL: '{gemini_model}'")
# print(f"[ENV DIAGNOSTIC] GEMINI_API_KEY Found: {True if gemini_key else False}")
# if gemini_key:
#     # Print the first 5 characters and last 4 characters to confirm it's valid without leaking it
#     print(f"[ENV DIAGNOSTIC] Key Mask: {gemini_key[:5]}...{gemini_key[-4:]}")
# else:
#     print("[ENV DIAGNOSTIC] ❌ ERROR: GEMINI_API_KEY is returning None or Empty String!")
# print("=======================================\n")


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
            
            # Extract necessary details matching state keys
            initial_state = {
                "pr_url": pr_data.get("html_url"),
                "diff_url": pr_data.get("diff_url"), # GitHub provides direct raw diff links
                "git_diff": "",
                "risk_score": "",
                "risk_factors": [],
                "threat_report": "",
                "repo_full_name": payload["repository"]["full_name"],   
                "pr_number": payload.get("number"),                      
                "comment_url": "",
                "reviewer_assigned": False,
                "email_sent": False
            }
            
            print(f"Triggering ChangeGuard AI for PR #{payload.get('number')}")
            # Offload processing to background task so GitHub doesn't timeout waiting
            background_tasks.add_task(run_ai_workflow, initial_state)
            
            return {"status": "workflow_initiated"}

    return {"status": "ignored_event"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)