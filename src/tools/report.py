from typing import Any, Dict
import traceback
from src.graph.state import ChangeGuardState


def threat_report_node(state: ChangeGuardState) -> Dict[str, Any]:
    print("\n" + "=" * 20 + " ENTERING THREAT REPORT NODE " + "=" * 20)

    # 1. STATE RESOLUTION & SAFETY CHECK
    try:
        score = str(state.get("risk_score", "UNKNOWN")).upper().strip()
        findings = state.get("risk_factors", [])
    except Exception as state_err:
        print(
            f"[CRITICAL ERROR] Failed to extract base properties from LangGraph state: {str(state_err)}"
        )
        traceback.print_exc()
        score, findings = "CRITICAL_SYSTEM_ERROR", []

    # 2. VERBOSE DIAGNOSTICS
    print("[DEBUG REPORT NODE] Evaluation metrics captured:")
    print(f"  - Resolved risk_score string: '{score}'")
    print(f"  - Extracted findings container type: {type(findings)}")
    print(f"  - Total findings detected in batch array: {len(findings)}")

    # 3. REPORT HEADER
    report_lines = [
        "=" * 70,
        "CHANGEGUARD AI DEPLOYMENT THREAT REPORT",
        "=" * 70,
        "",
        f"Risk Level     : {score}",
        f"Total Findings : {len(findings)}",
        "Engine         : Gemini",
        "",
    ]

    # 4. HANDLE CLEAN REPORT
    if not findings:
        print(
            "[DEBUG REPORT NODE] Finding array evaluated to empty or null. Packaging clean report."
        )

        report_lines.extend(
            [
                "=" * 70,
                "NO SECURITY FINDINGS DETECTED",
                "=" * 70,
                "",
                "The submitted changes do not contain any detected",
                "security vulnerabilities, architectural risks,",
                "or deployment blockers.",
                "",
            ]
        )

    # 5. PROCESS FINDINGS
    else:
        for idx, item in enumerate(findings, 1):
            print(
                f"[DEBUG REPORT NODE] Processing element index [{idx}/{len(findings)}]..."
            )

            try:
                if isinstance(item, dict):
                    v_type = item.get(
                        "vulnerability_type", "Unknown Vulnerability"
                    )
                    f_name = item.get("file_name", "Unknown File")
                    snippet = item.get(
                        "line_snippet", "Code snippet unavailable."
                    )
                    explain = item.get(
                        "explanation",
                        "No explanation provided."
                    )
                    remediation = item.get(
                        "remediation",
                        "No remediation guidance available."
                    )
                else:
                    v_type = getattr(
                        item,
                        "vulnerability_type",
                        "Unknown Vulnerability",
                    )
                    f_name = getattr(item, "file_name", "Unknown File")
                    snippet = getattr(
                        item,
                        "line_snippet",
                        "Code snippet unavailable.",
                    )
                    explain = getattr(
                        item,
                        "explanation",
                        "No explanation provided.",
                    )
                    remediation = getattr(
                        item,
                        "remediation",
                        "No remediation guidance available.",
                    )

                report_lines.extend(
                    [
                        "=" * 70,
                        f"Finding #{idx}: {v_type}",
                        f"Severity : {score}",
                        f"File     : {f_name}",
                        "=" * 70,
                        "",
                        "Affected Code:",
                    ]
                )

                # Preserve code formatting nicely
                if snippet:
                    for line in str(snippet).strip().splitlines():
                        report_lines.append(f"    {line}")
                else:
                    report_lines.append("    Code snippet unavailable.")

                report_lines.extend(
                    [
                        "",
                        "Issue:",
                        explain.strip(),
                        "",
                        "Recommendation:",
                        remediation.strip(),
                        "",
                    ]
                )

            except Exception as element_err:
                print(
                    f"[DEBUG REPORT NODE] Error unpacking node index [{idx}]: {str(element_err)}"
                )

                report_lines.extend(
                    [
                        "=" * 70,
                        f"ERROR PROCESSING FINDING #{idx}",
                        "=" * 70,
                        f"Reason: {str(element_err)}",
                        "",
                    ]
                )

    # 6. REPORT FOOTER
    report_lines.extend(
        [
            "=" * 70,
            "End of Report",
            "=" * 70,
        ]
    )

    final_report = "\n".join(report_lines)

    print(
        "[DEBUG REPORT NODE] Document built successfully. Sending final string downstream."
    )
    print("=" * 20 + " EXITING THREAT REPORT NODE " + "=" * 20 + "\n")

    return {"threat_report": final_report}
