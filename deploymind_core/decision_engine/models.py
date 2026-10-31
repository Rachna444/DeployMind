from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class DecisionResult:
    decision: str  # "SAFE", "CANARY", "BLOCKED"
    reason: str
    risk_level: str
    risk_score: float
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "summary": self.summary,
        }
