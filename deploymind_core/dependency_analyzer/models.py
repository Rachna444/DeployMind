from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class ServiceDependency:
    caller: str
    target: str
    type: str  # e.g., "http_call", "docker_depends_on"
    details: Optional[str] = None
    source_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "caller": self.caller,
            "target": self.target,
            "type": self.type,
        }
        if self.details:
            data["details"] = self.details
        if self.source_file:
            data["source_file"] = self.source_file
        return data


@dataclass
class DependencyGraphResult:
    services: List[str]
    dependencies: List[ServiceDependency]
    graph: Dict[str, List[str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "services": sorted(list(set(self.services))),
            "dependencies": [d.to_dict() for d in self.dependencies],
            "graph": {k: sorted(list(set(v))) for k, v in self.graph.items()}
        }
