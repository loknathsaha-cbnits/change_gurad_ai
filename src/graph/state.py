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
    repo_full_name: str      
    pr_number: int
    comment_url: str
    reviewer_assigned: bool
    email_sent: bool
    commit_id: str          #  PR head SHA, required for line-comment API
    line_comments_posted: bool   #  track whether the batched review succeeded

class LLMRiskAnalysis(BaseModel):
    risk_score: str = Field(description="Must be exactly 'LOW', 'MEDIUM', or 'HIGH'")
    risk_factors: List[str] = Field(description="List of specific structural or security deployment risk factors found in the diff.")

