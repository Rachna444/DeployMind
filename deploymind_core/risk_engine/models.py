from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class RiskFactor:
    name: str
    points: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskAssessmentResult:
    risk_score: int
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    factors: List[RiskFactor]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "factors": [f.to_dict() for f in self.factors],
            "summary": self.summary,
        }
