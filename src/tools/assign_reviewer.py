import os
import requests


def assign_reviewer(state: dict) -> dict:
    print("\n=== ASSIGN_REVIEWER_NODE DEBUG ===")

    token = os.getenv("GITHUB_TOKEN")
    print(f"DEBUG token set        : {'YES' if token else 'NO — check .env'}")

    repo      = state.get("repo_full_name")
    pr_number = state.get("pr_number")
    print(f"DEBUG repo_full_name   : {repo}")
    print(f"DEBUG pr_number        : {pr_number}")

    if not token:
        state["error"] = "GITHUB_TOKEN missing from environment"
        print(f"❌ {state['error']}")
        state["reviewer_assigned"] = False
        return state

    if not repo or not pr_number:
        state["error"] = f"Missing repo_full_name or pr_number in state. Got repo={repo}, pr_number={pr_number}"
        print(f"❌ {state['error']}")
        state["reviewer_assigned"] = False
        return state

    reviewer_username = repo.split("/")[0]
    print(f"DEBUG reviewer_username: {reviewer_username}")

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/requested_reviewers"
    print(f"DEBUG POST URL          : {url}")

    try:
        print("DEBUG [1] Sending request to GitHub API ...")
        res = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            json={"reviewers": [reviewer_username]},
            timeout=10
        )
        print(f"DEBUG [2] Response status: {res.status_code}")

        if res.status_code == 401:
            state["error"] = "401 Unauthorized — token invalid or expired"
            print(f"❌ {state['error']}")
            state["reviewer_assigned"] = False
            return state

        if res.status_code == 403:
            state["error"] = f"403 Forbidden — token lacks permission. Response: {res.text[:300]}"
            print(f"❌ {state['error']}")
            state["reviewer_assigned"] = False
            return state

        if res.status_code == 404:
            state["error"] = f"404 Not Found — check repo name/PR number. URL: {url}"
            print(f"❌ {state['error']}")
            state["reviewer_assigned"] = False
            return state

        if res.status_code == 422:
            # Common cause: requesting the PR author themselves, or user isn't a collaborator
            state["error"] = f"422 Unprocessable — reviewer may be PR author or not a valid collaborator. Response: {res.text[:300]}"
            print(f"❌ {state['error']}")
            state["reviewer_assigned"] = False
            return state

        res.raise_for_status()

        state["reviewer_assigned"] = True
        print(f"✅ Reviewer '{reviewer_username}' requested successfully")

    except requests.exceptions.Timeout:
        state["error"] = "Request to GitHub API timed out"
        print(f"❌ {state['error']}")
        state["reviewer_assigned"] = False

    except requests.exceptions.ConnectionError as e:
        state["error"] = f"Connection error reaching GitHub API: {e}"
        print(f"❌ {state['error']}")
        state["reviewer_assigned"] = False

    except Exception as e:
        state["error"] = f"Unexpected error: {type(e).__name__}: {e}"
        print(f"❌ {state['error']}")
        state["reviewer_assigned"] = False

    print("=== END DEBUG ===\n")
    return state