import json
import sys
from typing import Dict, List, Any, Optional, Union

try:
    from .models import RiskFactor, RiskAssessmentResult
except ImportError:
    from models import RiskFactor, RiskAssessmentResult


class RiskEngine:
    """Calculates deployment risk scores based on change metrics, service criticality, and blast radius."""

    CRITICAL_SERVICES = {"gateway", "root", "docker-compose.yml", "requirements.txt"}

    def calculate_risk(
        self,
        change_analysis: Optional[Dict[str, Any]] = None,
        blast_radius: Optional[Dict[str, Any]] = None,
        affected_service: Optional[str] = None,
        added_lines: int = 0,
        deleted_lines: int = 0,
        changed_files_count: int = 0,
        change_types: Optional[List[str]] = None,
        directly_affected_count: int = 0,
        indirectly_affected_count: int = 0,
        dependency_chains: Optional[List[str]] = None,
    ) -> RiskAssessmentResult:
        factors: List[RiskFactor] = []
        raw_score = 0.0

        # Process change_analysis dict if provided
        if change_analysis:
            summary = change_analysis.get("summary", {})
            added_lines = summary.get("total_added_lines", added_lines)
            deleted_lines = summary.get("total_deleted_lines", deleted_lines)
            changed_files_count = summary.get("total_changed_files", changed_files_count)
            files = change_analysis.get("changed_files", [])
            if files and not change_types:
                change_types = [f.get("change_type", "modified") for f in files]
            if files and not affected_service:
                affected_service = files[0].get("affected_service")

        # Process blast_radius dict if provided
        if blast_radius:
            direct_services = blast_radius.get("directly_affected_services", [])
            indirect_services = blast_radius.get("indirectly_affected_services", [])
            directly_affected_count = len(direct_services)
            indirectly_affected_count = len(indirect_services)
            dependency_chains = blast_radius.get("dependency_chains", dependency_chains or [])
            if not affected_service and blast_radius.get("changed_service"):
                cs = blast_radius.get("changed_service")
                affected_service = cs if isinstance(cs, str) else cs[0] if cs else None

        # 1. Line Churn Factor
        total_churn = added_lines + deleted_lines
        if total_churn > 0:
            if total_churn < 20:
                pts = 5.0
                reason = f"Low code churn ({total_churn} total lines changed)"
            elif total_churn < 100:
                pts = 15.0
                reason = f"Moderate code churn ({total_churn} total lines changed)"
            elif total_churn < 500:
                pts = 25.0
                reason = f"High code churn ({total_churn} total lines changed)"
            else:
                pts = 35.0
                reason = f"Very high code churn ({total_churn} total lines changed)"
            
            raw_score += pts
            factors.append(RiskFactor(name="Code Churn", points=pts, description=reason))

        # Deletion ratio penalty
        if deleted_lines > 10 and deleted_lines > added_lines * 2:
            pts = 10.0
            raw_score += pts
            factors.append(
                RiskFactor(
                    name="High Deletion Ratio",
                    points=pts,
                    description=f"Significant code deletion ({deleted_lines} deleted vs {added_lines} added lines)"
                )
            )

        # 2. Changed Files Count Factor
        if changed_files_count > 0:
            pts = min(changed_files_count * 5.0, 25.0)
            raw_score += pts
            factors.append(
                RiskFactor(
                    name="File Changes Volume",
                    points=pts,
                    description=f"{changed_files_count} file(s) modified"
                )
            )

        # 3. Change Types Risk
        if change_types:
            type_score = 0.0
            type_counts = {}
            for ct in change_types:
                ct_lower = ct.lower()
                type_counts[ct_lower] = type_counts.get(ct_lower, 0) + 1
                if ct_lower == "deleted":
                    type_score += 15.0
                elif ct_lower == "renamed":
                    type_score += 10.0
                elif ct_lower == "modified":
                    type_score += 5.0
                elif ct_lower == "added":
                    type_score += 3.0

            type_score = min(type_score, 30.0)
            if type_score > 0:
                raw_score += type_score
                desc = ", ".join([f"{count} {t}" for t, count in type_counts.items()])
                factors.append(
                    RiskFactor(
                        name="Change Types Impact",
                        points=type_score,
                        description=f"Change types detected: {desc}"
                    )
                )

        # 4. Service Criticality Factor
        if affected_service:
            if affected_service.lower() in self.CRITICAL_SERVICES:
                pts = 20.0
                raw_score += pts
                factors.append(
                    RiskFactor(
                        name="Critical Service Modified",
                        points=pts,
                        description=f"Primary gateway or root config service modified: '{affected_service}'"
                    )
                )
            else:
                pts = 10.0
                raw_score += pts
                factors.append(
                    RiskFactor(
                        name="Service Modified",
                        points=pts,
                        description=f"Target service modified: '{affected_service}'"
                    )
                )

        # 5. Blast Radius Factors
        if directly_affected_count > 0:
            pts = min(directly_affected_count * 15.0, 45.0)
            raw_score += pts
            factors.append(
                RiskFactor(
                    name="Direct Dependencies Impact",
                    points=pts,
                    description=f"{directly_affected_count} directly affected downstream service(s)"
                )
            )

        if indirectly_affected_count > 0:
            pts = min(indirectly_affected_count * 10.0, 30.0)
            raw_score += pts
            factors.append(
                RiskFactor(
                    name="Indirect Dependencies Impact",
                    points=pts,
                    description=f"{indirectly_affected_count} indirectly affected downstream service(s)"
                )
            )

        if dependency_chains:
            max_chain_len = 0
            for chain in dependency_chains:
                links = chain.split(" -> ")
                max_chain_len = max(max_chain_len, len(links))

            if max_chain_len > 1:
                pts = min((max_chain_len - 1) * 5.0, 20.0)
                raw_score += pts
                factors.append(
                    RiskFactor(
                        name="Dependency Chain Depth",
                        points=pts,
                        description=f"Max dependency propagation depth: {max_chain_len} services in chain"
                    )
                )

        # Clamp final score between 0 and 100
        final_score = int(min(max(round(raw_score), 0), 100))

        # Determine Risk Level
        if final_score < 35:
            risk_level = "LOW"
        elif final_score < 70:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        summary = {
            "total_changed_files": changed_files_count,
            "total_lines_changed": total_churn,
            "affected_service": affected_service or "unknown",
            "directly_affected_count": directly_affected_count,
            "indirectly_affected_count": indirectly_affected_count,
            "total_affected_services": directly_affected_count + indirectly_affected_count,
        }

        return RiskAssessmentResult(
            risk_score=final_score,
            risk_level=risk_level,
            factors=factors,
            summary=summary
        )


def calculate_risk_score(
    change_analysis: Optional[Dict[str, Any]] = None,
    blast_radius: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    engine = RiskEngine()
    return engine.calculate_risk(change_analysis=change_analysis, blast_radius=blast_radius, **kwargs).to_dict()


def calculate_risk_score_to_json(
    change_analysis: Optional[Dict[str, Any]] = None,
    blast_radius: Optional[Dict[str, Any]] = None,
    indent: int = 2,
    **kwargs
) -> str:
    engine = RiskEngine()
    result = engine.calculate_risk(change_analysis=change_analysis, blast_radius=blast_radius, **kwargs)
    return json.dumps(result.to_dict(), indent=indent)


if __name__ == "__main__":
    engine = RiskEngine()
    sample_change = {
        "summary": {
            "total_changed_files": 2,
            "total_added_lines": 45,
            "total_deleted_lines": 12
        },
        "changed_files": [
            {"file_path": "app/task_service/main.py", "affected_service": "task_service", "change_type": "modified"}
        ]
    }
    sample_blast = {
        "changed_service": "task_service",
        "directly_affected_services": ["gateway"],
        "indirectly_affected_services": [],
        "dependency_chains": ["gateway -> task_service"]
    }
    print(json.dumps(engine.calculate_risk(sample_change, sample_blast).to_dict(), indent=2))
