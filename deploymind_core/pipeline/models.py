from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class PipelineReport:
    changed_files: List[Dict[str, Any]]
    affected_services: List[str]
    blast_radius: Dict[str, Any]
    risk_score: float
    risk_level: str
    recommended_validations: List[str]
    validation_results: Dict[str, Any]
    final_decision: str  # "SAFE", "CANARY", "BLOCKED"
    reason: str
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "changed_files": self.changed_files,
            "affected_services": self.affected_services,
            "blast_radius": self.blast_radius,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "recommended_validations": self.recommended_validations,
            "validation_results": self.validation_results,
            "final_decision": self.final_decision,
            "reason": self.reason,
            "summary": self.summary,
        }
