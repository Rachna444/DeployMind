from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Union


@dataclass
class BlastRadiusResult:
    changed_service: Union[str, List[str]]
    directly_affected_services: List[str]
    indirectly_affected_services: List[str]
    dependency_chains: List[str]
    total_affected_service_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "changed_service": self.changed_service,
            "directly_affected_services": sorted(list(set(self.directly_affected_services))),
            "indirectly_affected_services": sorted(list(set(self.indirectly_affected_services))),
            "dependency_chains": sorted(list(set(self.dependency_chains))),
            "total_affected_service_count": self.total_affected_service_count,
        }
