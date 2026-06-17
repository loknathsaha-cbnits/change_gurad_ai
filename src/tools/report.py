from typing import Any, Dict
from src.graph.state import ChangeGuardState

def threat_report_node(state: ChangeGuardState) -> Dict[str, Any]:
    print("--- GENERATING THREAT REPORT ---")
    
    score = state.get("risk_score", "UNKNOWN")
    findings = state.get("risk_factors", []) 
    
    # DIAGNOSTICS
    print(f"[DEBUG REPORT NODE] Current state execution evaluation:")
    print(f"  - risk_score retrieved: '{score}'")
    print(f"  - type of findings object: {type(findings)}")
    print(f"  - items found in array: {len(findings)}")
    
    report_markdown = [
        "## 🛡️ ChangeGuard AI Deployment Threat Report",
        f"**Overall Risk Classification:** `{score}`",
        "---",
        "### 🔍 Detailed Architectural & Security Findings\n"
    ]
    
    if not findings:
        print("[DEBUG REPORT NODE] Array was empty. Compiling default safe response.")
        report_markdown.append("*No major deployment hazards detected in this patch submission.*")
    else:
        for idx, item in enumerate(findings, 1):
            # Handle both Pydantic objects and raw dicts
            if isinstance(item, dict):
                v_type   = item.get('vulnerability_type', 'Unknown')
                f_name   = item.get('file_name', 'Unknown')
                snippet  = item.get('line_snippet', 'N/A')
                explain  = item.get('explanation', 'N/A')
                rem      = item.get('remediation', 'N/A')
            else:
                v_type   = getattr(item, 'vulnerability_type', 'Unknown')
                f_name   = getattr(item, 'file_name', 'Unknown')
                snippet  = getattr(item, 'line_snippet', 'N/A')
                explain  = getattr(item, 'explanation', 'N/A')
                rem      = getattr(item, 'remediation', 'N/A')

            report_markdown.append(f"#### {idx}. [{v_type}] in `{f_name}`")
            report_markdown.append(f"> **Problematic Snippet:**\n> ```python\n> {snippet}\n> ```")
            report_markdown.append(f"**Impact Analysis:** {explain}")
            report_markdown.append(f"💡 **How to Fix / Remediation:** {rem}")
            report_markdown.append("\n" + "-"*40 + "\n")
            
    return {"threat_report": "\n".join(report_markdown)}