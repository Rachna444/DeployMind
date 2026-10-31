import json
import sys
from typing import Dict, List, Any, Optional, Union

try:
    from .models import DecisionResult
except ImportError:
    from models import DecisionResult


class DecisionEngine:
    """Evaluates risk metrics and validation results to issue deployment decisions (SAFE, CANARY, BLOCKED)."""

    DECISION_SAFE = "SAFE"
    DECISION_CANARY = "CANARY"
    DECISION_BLOCKED = "BLOCKED"

    def make_decision(
        self,
        risk_score: float = 0.0,
        risk_level: str = "LOW",
        validation_results: Optional[Union[Dict[str, Any], List[Any]]] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
    ) -> DecisionResult:
        if risk_assessment:
            risk_level = risk_assessment.get("risk_level", risk_level)
            risk_score = risk_assessment.get("risk_score", risk_score)

        risk_level_upper = (risk_level or "LOW").upper()

        passed_validations: List[str] = []
        failed_validations: List[str] = []

        if validation_results:
            if isinstance(validation_results, dict):
                for name, status in validation_results.items():
                    if status is True or (isinstance(status, str) and status.upper() in ("PASSED", "PASS", "SUCCESS", "TRUE", "OK")):
                        passed_validations.append(name)
                    else:
                        failed_validations.append(name)
            elif isinstance(validation_results, list):
                for item in validation_results:
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("validation") or "unknown"
                        status = item.get("status") if "status" in item else item.get("passed", True)
                        if status is True or (isinstance(status, str) and status.upper() in ("PASSED", "PASS", "SUCCESS", "TRUE", "OK")):
                            passed_validations.append(str(name))
                        else:
                            failed_validations.append(str(name))
                    elif isinstance(item, str):
                        passed_validations.append(item)

        if failed_validations:
            decision = self.DECISION_BLOCKED
            failed_str = ", ".join(failed_validations)
            reason = (
                f"Deployment BLOCKED: {len(failed_validations)} required validation(s) failed ({failed_str})."
            )
        elif risk_level_upper == "LOW":
            decision = self.DECISION_SAFE
            reason = (
                f"Deployment marked SAFE: LOW risk level (score: {risk_score}) "
                f"and all {len(passed_validations)} required validation(s) passed successfully."
            )
        else:  # MEDIUM or HIGH risk level
            decision = self.DECISION_CANARY
            reason = (
                f"Deployment routed to CANARY: {risk_level_upper} risk level (score: {risk_score}) "
                f"with all {len(passed_validations)} required validation(s) passed."
            )

        summary = {
            "passed_validations_count": len(passed_validations),
            "failed_validations_count": len(failed_validations),
            "passed_validations": passed_validations,
            "failed_validations": failed_validations,
        }

        return DecisionResult(
            decision=decision,
            reason=reason,
            risk_level=risk_level_upper,
            risk_score=risk_score,
            summary=summary
        )


def evaluate_decision(
    risk_score: float = 0.0,
    risk_level: str = "LOW",
    validation_results: Optional[Union[Dict[str, Any], List[Any]]] = None,
    risk_assessment: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    engine = DecisionEngine()
    return engine.make_decision(
        risk_score=risk_score,
        risk_level=risk_level,
        validation_results=validation_results,
        risk_assessment=risk_assessment,
    ).to_dict()


def evaluate_decision_to_json(
    risk_score: float = 0.0,
    risk_level: str = "LOW",
    validation_results: Optional[Union[Dict[str, Any], List[Any]]] = None,
    risk_assessment: Optional[Dict[str, Any]] = None,
    indent: int = 2,
) -> str:
    engine = DecisionEngine()
    result = engine.make_decision(
        risk_score=risk_score,
        risk_level=risk_level,
        validation_results=validation_results,
        risk_assessment=risk_assessment,
    )
    return json.dumps(result.to_dict(), indent=indent)


if __name__ == "__main__":
    engine = DecisionEngine()
    sample_val = {"health_checks": "PASSED", "api_tests": "PASSED"}
    print(json.dumps(engine.make_decision(55.0, "MEDIUM", sample_val).to_dict(), indent=2))
