import os
import requests

def format_risk_factors(risk_factors) -> str:
    print(f"[DEBUG FORMAT] Formatting {len(risk_factors) if risk_factors else 0} risk factor(s)...")

    if not risk_factors:
        print("[DEBUG FORMAT] No risk factors found — using fallback text.")
        return "No specific risk factors identified."

    blocks = []
    for i, factor in enumerate(risk_factors, 1):
        print(f"[DEBUG FORMAT] Formatting finding #{i}: type={factor.vulnerability_type}, file={factor.file_name}, line={factor.line_number}")
        blocks.append(
            f"**{i}. {factor.vulnerability_type}** — `{factor.file_name}`"
            + (f" (line {factor.line_number})" if factor.line_number else "")
            + f"\n> {factor.line_snippet}\n\n"
            f"{factor.explanation}\n\n"
            f"**Fix:** {factor.remediation}"
        )

    formatted = "\n\n---\n\n".join(blocks)
    print(f"[DEBUG FORMAT] Final formatted length: {len(formatted)} chars")
    return formatted

def post_comment_node(state: dict) -> dict:
    print("\n=== POST_COMMENT_NODE DEBUG ===")

    token = os.getenv("GITHUB_TOKEN")
    print(f"DEBUG token set        : {'YES' if token else 'NO — check .env'}")
    print(f"DEBUG token prefix     : {token[:8]}... (len={len(token) if token else 0})" if token else "DEBUG token: MISSING")

    repo      = state.get("repo_full_name")
    pr_number = state.get("pr_number")
    print(f"DEBUG repo_full_name   : {repo}")
    print(f"DEBUG pr_number        : {pr_number}")

    if not token:
        state["error"] = "GITHUB_TOKEN missing from environment"
        print(f"❌ {state['error']}")
        return state

    if not repo or not pr_number:
        state["error"] = f"Missing repo_full_name or pr_number in state. Got repo={repo}, pr_number={pr_number}"
        print(f"❌ {state['error']}")
        return state

    print(f"DEBUG risk_score       : {state.get('risk_score')}")
    print(f"DEBUG risk_factors len : {len(state.get('risk_factors', []))}")
    print(f"DEBUG threat_report len: {len(state.get('threat_report', ''))}")

    risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(state.get("risk_score"), "⚪")

    # --- Format findings properly instead of dumping raw Pydantic objects ---
    factors_list = format_risk_factors(state.get("risk_factors", []))

    comment_body = f"""## 🤖 ChangeGuard AI Risk Review

**Risk Level:** {risk_emoji} {state.get('risk_score')}

**Risk Factors:**

{factors_list}

**Summary:**
{state.get('threat_report')}

---
*Posted automatically by ChangeGuard AI*
"""

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    print(f"DEBUG POST URL          : {url}")

    try:
        print("DEBUG [1] Sending request to GitHub API ...")
        res = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            json={"body": comment_body},
            timeout=10
        )
        print(f"DEBUG [2] Response status: {res.status_code}")

        if res.status_code == 401:
            state["error"] = "401 Unauthorized — token invalid or expired"
            print(f"❌ {state['error']}")
            return state

        if res.status_code == 403:
            state["error"] = f"403 Forbidden — token lacks permission. Response: {res.text[:300]}"
            print(f"❌ {state['error']}")
            return state

        if res.status_code == 404:
            state["error"] = f"404 Not Found — check repo name/PR number. URL: {url}"
            print(f"❌ {state['error']}")
            return state

        res.raise_for_status()

        state["comment_url"] = res.json().get("html_url", "")
        print(f"DEBUG [3] Comment URL  : {state['comment_url']}")
        print(f"✅ Comment posted successfully")

    except requests.exceptions.Timeout:
        state["error"] = "Request to GitHub API timed out"
        print(f"❌ {state['error']}")

    except requests.exceptions.ConnectionError as e:
        state["error"] = f"Connection error reaching GitHub API: {e}"
        print(f"❌ {state['error']}")

    except Exception as e:
        state["error"] = f"Unexpected error: {type(e).__name__}: {e}"
        print(f"❌ {state['error']}")

    print("=== END DEBUG ===\n")
    return state
