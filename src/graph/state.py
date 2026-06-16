from typing import TypedDict, List, Dict, Optional


from typing import List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

class ChangeGuardState(TypedDict):
    pr_url: str
    diff_url: str
    git_diff: str
    risk_score: str
    risk_factors: List[str]
    threat_report: str
    error: Optional[str]

class LLMRiskAnalysis(BaseModel):
    risk_score: str = Field(description="Must be exactly 'LOW', 'MEDIUM', or 'HIGH'")
    risk_factors: List[str] = Field(description="List of specific structural or security deployment risk factors found in the diff.")

# class ChangeGuardState(TypedDict):
#     event_type: str
#     repository_name: str
#     pr_number: int
#     pr_url: str

#     source_branch: str
#     target_branch: str

#     changed_files: List[str]
#     git_diff: str

#     risk_score: str
#     risk_factors: List[str]

#     impacted_services: List[str]

#     security_findings: List[str]

#     deployment_strategy: str
#     rollback_plan: str

#     threat_report: str
#     error: Optional[str]
