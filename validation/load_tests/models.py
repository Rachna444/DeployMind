from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class LoadTestResult:
    status: str  # "PASS" or "FAIL"
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    success_rate: float
    concurrency: int
    gateway_url: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "average_response_time_ms": round(self.average_response_time_ms, 2),
            "success_rate": round(self.success_rate, 2),
            "concurrency": self.concurrency,
            "gateway_url": self.gateway_url,
        }
