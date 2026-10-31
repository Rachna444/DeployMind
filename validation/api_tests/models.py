from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class APITestResult:
    test_name: str
    status: str  # "PASS" or "FAIL"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "status": self.status,
            "error_message": self.error_message,
        }


@dataclass
class APITestSuiteReport:
    status: str  # "PASS" or "FAIL"
    total_tests: int
    passed_count: int
    failed_count: int
    gateway_url: str
    tests: List[APITestResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "total_tests": self.total_tests,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "gateway_url": self.gateway_url,
            "tests": [t.to_dict() for t in self.tests],
        }
