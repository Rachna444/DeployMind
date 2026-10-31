from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class ServiceHealthResult:
    service_name: str
    status: str  # "PASS" or "FAIL"
    endpoint: str
    response_time_ms: float
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "status": self.status,
            "endpoint": self.endpoint,
            "response_time_ms": round(self.response_time_ms, 2),
            "error_message": self.error_message,
        }


@dataclass
class HealthCheckReport:
    status: str  # "PASS" or "FAIL"
    total_checked: int
    passed_count: int
    failed_count: int
    results: List[ServiceHealthResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "total_checked": self.total_checked,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "results": [r.to_dict() for r in self.results],
        }
