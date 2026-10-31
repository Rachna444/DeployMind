import json
import sys
from typing import Dict, List, Any, Optional, Union

try:
    from .models import ValidationRecommendation
except ImportError:
    from models import ValidationRecommendation


class ValidationAgent:
    """Agent that selects required pre-deployment validations based on risk assessment and blast radius."""

    VALIDATION_HEALTH_CHECKS = "health_checks"
    VALIDATION_API_TESTS = "api_tests"
    VALIDATION_DEPENDENCY = "dependency_validation"
    VALIDATION_LOAD_TESTS = "load_tests"

    def select_validations(
        self,
        risk_level: str = "LOW",
        risk_score: float = 0.0,
        affected_services: Optional[List[str]] = None,
        blast_radius: Optional[Dict[str, Any]] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
    ) -> ValidationRecommendation:
        if risk_assessment:
            risk_level = risk_assessment.get("risk_level", risk_level)
            risk_score = risk_assessment.get("risk_score", risk_score)
            summary = risk_assessment.get("summary", {})
            if not affected_services and summary.get("affected_service"):
                affected_services = [summary.get("affected_service")]

        affected_services = affected_services or []
        risk_level_upper = (risk_level or "LOW").upper()

        directly_affected = []
        indirectly_affected = []
        total_affected_count = 0

        if blast_radius:
            directly_affected = blast_radius.get("directly_affected_services", [])
            indirectly_affected = blast_radius.get("indirectly_affected_services", [])
            total_affected_count = blast_radius.get(
                "total_affected_service_count",
                len(directly_affected) + len(indirectly_affected)
            )

        recommended_validations: List[str] = []
        reasoning: List[str] = []

        # 1. Health Checks
        recommended_validations.append(self.VALIDATION_HEALTH_CHECKS)
        reasoning.append("health_checks: Always required as baseline validation for container and service readiness.")

        # 2. API Tests
        if risk_level_upper in ("MEDIUM", "HIGH") or risk_score >= 25 or len(affected_services) > 0:
            recommended_validations.append(self.VALIDATION_API_TESTS)
            reasoning.append(
                f"api_tests: Recommended because risk level is {risk_level_upper} (score: {risk_score}) "
                f"with active services affected."
            )

        # 3. Dependency Validation
        if total_affected_count > 0 or risk_level_upper in ("MEDIUM", "HIGH"):
            recommended_validations.append(self.VALIDATION_DEPENDENCY)
            reasoning.append(
                f"dependency_validation: Recommended due to blast radius affecting {total_affected_count} "
                f"downstream service(s) (direct: {len(directly_affected)}, indirect: {len(indirectly_affected)})."
            )

        # 4. Load Tests
        if risk_level_upper == "HIGH" or risk_score >= 70 or total_affected_count >= 3:
            recommended_validations.append(self.VALIDATION_LOAD_TESTS)
            reasoning.append(
                f"load_tests: Recommended due to HIGH deployment risk (score: {risk_score}) "
                f"and potential impact across system infrastructure."
            )

        summary = {
            "risk_score": risk_score,
            "total_validations_count": len(recommended_validations),
            "total_affected_services_count": total_affected_count,
        }

        return ValidationRecommendation(
            risk_level=risk_level_upper,
            recommended_validations=recommended_validations,
            reasoning=reasoning,
            summary=summary
        )


def select_validations(
    risk_level: str = "LOW",
    risk_score: float = 0.0,
    affected_services: Optional[List[str]] = None,
    blast_radius: Optional[Dict[str, Any]] = None,
    risk_assessment: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    agent = ValidationAgent()
    return agent.select_validations(
        risk_level=risk_level,
        risk_score=risk_score,
        affected_services=affected_services,
        blast_radius=blast_radius,
        risk_assessment=risk_assessment,
    ).to_dict()


def select_validations_to_json(
    risk_level: str = "LOW",
    risk_score: float = 0.0,
    affected_services: Optional[List[str]] = None,
    blast_radius: Optional[Dict[str, Any]] = None,
    risk_assessment: Optional[Dict[str, Any]] = None,
    indent: int = 2,
) -> str:
    agent = ValidationAgent()
    result = agent.select_validations(
        risk_level=risk_level,
        risk_score=risk_score,
        affected_services=affected_services,
        blast_radius=blast_radius,
        risk_assessment=risk_assessment,
    )
    return json.dumps(result.to_dict(), indent=indent)


if __name__ == "__main__":
    agent = ValidationAgent()
    sample_blast = {
        "directly_affected_services": ["task_service"],
        "indirectly_affected_services": ["gateway"],
        "total_affected_service_count": 2
    }
    print(json.dumps(agent.select_validations("MEDIUM", 60.0, ["worker_service"], sample_blast).to_dict(), indent=2))
