from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class ValidationRecommendation:
    risk_level: str
    recommended_validations: List[str]
    reasoning: List[str]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "recommended_validations": self.recommended_validations,
            "reasoning": self.reasoning,
            "summary": self.summary,
        }
