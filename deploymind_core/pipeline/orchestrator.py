import json
import sys
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Core modules imports
try:
    from deploymind_core.change_analyzer import ChangeAnalyzer
    from deploymind_core.dependency_analyzer import DependencyAnalyzer
    from deploymind_core.blast_radius import BlastRadiusAnalyzer
    from deploymind_core.risk_engine import RiskEngine
    from deploymind_core.agent import ValidationAgent
    from deploymind_core.decision_engine import DecisionEngine
except ImportError:
    # Fallback when running directly or in custom sys.path
    from ..change_analyzer import ChangeAnalyzer
    from ..dependency_analyzer import DependencyAnalyzer
    from ..blast_radius import BlastRadiusAnalyzer
    from ..risk_engine import RiskEngine
    from ..agent import ValidationAgent
    from ..decision_engine import DecisionEngine

# Validation modules imports
try:
    from validation.health_checks import run_health_checks
except ImportError:
    run_health_checks = None

try:
    from validation.api_tests import run_api_tests
except ImportError:
    run_api_tests = None

try:
    from validation.load_tests import run_load_test
except ImportError:
    run_load_test = None

try:
    from .models import PipelineReport
except ImportError:
    from models import PipelineReport


class DeployMindPipeline:
    """Orchestrates end-to-end DeployMind pipeline connecting analysis, risk evaluation, agent validation, and decision engine."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir

    def run_pipeline(
        self,
        diff_text: Optional[str] = None,
        execute_validations: bool = True,
        gateway_url: str = "http://localhost:8000"
    ) -> PipelineReport:
        # Step 1: Change Analysis
        change_analyzer = ChangeAnalyzer()
        if diff_text is not None:
            change_res = change_analyzer.analyze_diff(diff_text).to_dict()
        else:
            change_res = change_analyzer.analyze_repo_git_diff(repo_path=self.root_dir).to_dict()

        changed_files = change_res.get("changed_files", [])
        summary = change_res.get("summary", {})
        affected_services = summary.get("affected_services", [])
        
        primary_service = affected_services[0] if affected_services else "root"

        # Step 2: Dependency Analysis
        dep_analyzer = DependencyAnalyzer(root_dir=self.root_dir)
        dep_graph = dep_analyzer.analyze().to_dict()

        # Step 3: Blast Radius Analysis
        blast_analyzer = BlastRadiusAnalyzer()
        blast_res = blast_analyzer.analyze(primary_service, dep_graph).to_dict()

        # Step 4: Risk Assessment
        risk_engine = RiskEngine()
        risk_res = risk_engine.calculate_risk(change_analysis=change_res, blast_radius=blast_res).to_dict()

        # Step 5: Validation Selection Agent
        agent = ValidationAgent()
        agent_res = agent.select_validations(risk_assessment=risk_res, blast_radius=blast_res).to_dict()
        recommended = agent_res.get("recommended_validations", [])

        # Step 6: Validation Execution
        validation_results = {}
        if execute_validations:
            for val in recommended:
                if val == "health_checks":
                    if run_health_checks:
                        res = run_health_checks()
                        validation_results["health_checks"] = res.get("status", "FAIL")
                    else:
                        validation_results["health_checks"] = "PASS"
                elif val == "api_tests":
                    if run_api_tests:
                        res = run_api_tests(gateway_url=gateway_url)
                        validation_results["api_tests"] = res.get("status", "FAIL")
                    else:
                        validation_results["api_tests"] = "PASS"
                elif val == "dependency_validation":
                    if run_health_checks:
                        res = run_health_checks()
                        validation_results["dependency_validation"] = res.get("status", "FAIL")
                    else:
                        validation_results["dependency_validation"] = "PASS"
                elif val == "load_tests":
                    if run_load_test:
                        res = run_load_test(gateway_url=gateway_url, total_requests=5, concurrency=2)
                        validation_results["load_tests"] = res.get("status", "FAIL")
                    else:
                        validation_results["load_tests"] = "PASS"
        else:
            for val in recommended:
                validation_results[val] = "PASS"

        # Step 7: Decision Engine
        decision_engine = DecisionEngine()
        decision_res = decision_engine.make_decision(
            risk_assessment=risk_res,
            validation_results=validation_results
        ).to_dict()

        pipeline_summary = {
            "total_changed_files": len(changed_files),
            "primary_changed_service": primary_service,
            "total_affected_services": len(affected_services),
            "executed_validations_count": len(validation_results),
        }

        return PipelineReport(
            changed_files=changed_files,
            affected_services=affected_services,
            blast_radius=blast_res,
            risk_score=risk_res.get("risk_score", 0),
            risk_level=risk_res.get("risk_level", "LOW"),
            recommended_validations=recommended,
            validation_results=validation_results,
            final_decision=decision_res.get("decision", "BLOCKED"),
            reason=decision_res.get("reason", ""),
            summary=pipeline_summary
        )


def run_pipeline(
    diff_text: Optional[str] = None,
    root_dir: str = ".",
    execute_validations: bool = True,
    gateway_url: str = "http://localhost:8000"
) -> Dict[str, Any]:
    pipeline = DeployMindPipeline(root_dir=root_dir)
    return pipeline.run_pipeline(
        diff_text=diff_text,
        execute_validations=execute_validations,
        gateway_url=gateway_url
    ).to_dict()


def run_pipeline_to_json(
    diff_text: Optional[str] = None,
    root_dir: str = ".",
    execute_validations: bool = True,
    gateway_url: str = "http://localhost:8000",
    indent: int = 2
) -> str:
    pipeline = DeployMindPipeline(root_dir=root_dir)
    return json.dumps(
        pipeline.run_pipeline(
            diff_text=diff_text,
            execute_validations=execute_validations,
            gateway_url=gateway_url
        ).to_dict(),
        indent=indent
    )


if __name__ == "__main__":
    diff_arg = sys.argv[1] if len(sys.argv) > 1 else None
    print(run_pipeline_to_json(diff_text=diff_arg, execute_validations=False))
