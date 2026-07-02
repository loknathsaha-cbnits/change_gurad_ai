import os
import requests


def post_line_comments_node(state: dict) -> dict:
    print("\n=== POST_LINE_COMMENTS_NODE DEBUG ===")

    token      = os.getenv("GITHUB_TOKEN")
    repo       = state.get("repo_full_name")
    pr_number  = state.get("pr_number")
    commit_id  = state.get("commit_id")
    findings   = state.get("risk_factors", [])

    print(f"DEBUG token set    : {'YES' if token else 'NO — check .env'}")
    print(f"DEBUG repo         : {repo}")
    print(f"DEBUG pr_number    : {pr_number}")
    print(f"DEBUG commit_id    : {commit_id}")
    print(f"DEBUG total findings: {len(findings)}")

    if not token:
        state["error"] = "GITHUB_TOKEN missing from environment"
        print(f"❌ {state['error']}")
        state["line_comments_posted"] = False
        return state

    if not repo or not pr_number or not commit_id:
        state["error"] = f"Missing repo/pr_number/commit_id. Got repo={repo}, pr_number={pr_number}, commit_id={commit_id}"
        print(f"❌ {state['error']}")
        state["line_comments_posted"] = False
        return state

    # --- Build the comments array, skipping findings with no valid line_number ---
    review_comments = []
    skipped = 0
    for i, finding in enumerate(findings, 1):
        line_number = getattr(finding, "line_number", None)
        if line_number is None:
            print(f"DEBUG [SKIP] Finding #{i} ({finding.vulnerability_type}) has no valid line_number — will only appear in summary comment.")
            skipped += 1
            continue

        body = (
            f"**{finding.vulnerability_type}**\n\n"
            f"{finding.explanation}\n\n"
            f"**Fix:** {finding.remediation}"
        )
        review_comments.append({
            "path": finding.file_name,
            "line": line_number,
            "side": "RIGHT",   # RIGHT = new version of the file
            "body": body
        })
        print(f"DEBUG [INCLUDE] Finding #{i}: file={finding.file_name}, line={line_number}")

    print(f"DEBUG total included: {len(review_comments)}, skipped (no line_number): {skipped}")

    if not review_comments:
        print("⚠️ No findings had valid line numbers — skipping review submission entirely.")
        state["line_comments_posted"] = False
        return state

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    print(f"DEBUG POST URL: {url}")

    payload = {
        "commit_id": commit_id,
        "body": "🤖 ChangeGuard AI — inline findings for this PR.",
        "event": "COMMENT",   # COMMENT = leaves feedback without approving/requesting changes
        "comments": review_comments
    }

    try:
        print("DEBUG [1] Sending batched review request to GitHub API ...")
        res = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            json=payload,
            timeout=15
        )
        print(f"DEBUG [2] Response status: {res.status_code}")

        if res.status_code == 401:
            state["error"] = "401 Unauthorized — token invalid or expired"
            print(f"❌ {state['error']}")
            state["line_comments_posted"] = False
            return state

        if res.status_code == 403:
            state["error"] = f"403 Forbidden — token lacks permission. Response: {res.text[:300]}"
            print(f"❌ {state['error']}")
            state["line_comments_posted"] = False
            return state

        if res.status_code == 404:
            state["error"] = f"404 Not Found — check repo/PR/commit_id. URL: {url}"
            print(f"❌ {state['error']}")
            state["line_comments_posted"] = False
            return state

        if res.status_code == 422:
            state["error"] = f"422 Unprocessable — one or more comment positions invalid. Response: {res.text[:500]}"
            print(f"❌ {state['error']}")
            state["line_comments_posted"] = False
            return state

        res.raise_for_status()

        state["line_comments_posted"] = True
        review_url = res.json().get("html_url", "")
        print(f"DEBUG [3] Review URL: {review_url}")
        print(f"✅ Batched review posted successfully with {len(review_comments)} inline comment(s)")

    except requests.exceptions.Timeout:
        state["error"] = "Request to GitHub API timed out"
        print(f"❌ {state['error']}")
        state["line_comments_posted"] = False

    except requests.exceptions.ConnectionError as e:
        state["error"] = f"Connection error reaching GitHub API: {e}"
        print(f"❌ {state['error']}")
        state["line_comments_posted"] = False

    except Exception as e:
        state["error"] = f"Unexpected error: {type(e).__name__}: {e}"
        print(f"❌ {state['error']}")
        state["line_comments_posted"] = False

    print("=== END DEBUG ===\n")
    return state