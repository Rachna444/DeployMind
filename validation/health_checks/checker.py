import json
import time
import sys
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from .models import ServiceHealthResult, HealthCheckReport
except ImportError:
    from models import ServiceHealthResult, HealthCheckReport


class HealthChecker:
    """Performs HTTP health checks for gateway, task_service, and worker_service."""

    DEFAULT_SERVICES = {
        "gateway": "http://localhost:8000/health",
        "task_service": "http://localhost:8001/health",
        "worker_service": "http://localhost:8002/health",
    }

    CONTAINER_SERVICES = {
        "gateway": "http://gateway:8000/health",
        "task_service": "http://task_service:8001/health",
        "worker_service": "http://worker_service:8002/health",
    }

    def __init__(self, service_urls: Optional[Dict[str, str]] = None, timeout: float = 5.0):
        self.service_urls = service_urls or self.DEFAULT_SERVICES
        self.timeout = timeout

    def check_service(self, service_name: str, url: str) -> ServiceHealthResult:
        start_time = time.time()
        
        if HAS_HTTPX:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url)
                    elapsed_ms = (time.time() - start_time) * 1000.0
                    if resp.status_code == 200:
                        return ServiceHealthResult(
                            service_name=service_name,
                            status="PASS",
                            endpoint=url,
                            response_time_ms=elapsed_ms,
                            error_message=None
                        )
                    else:
                        return ServiceHealthResult(
                            service_name=service_name,
                            status="FAIL",
                            endpoint=url,
                            response_time_ms=elapsed_ms,
                            error_message=f"HTTP Status {resp.status_code}: {resp.text}"
                        )
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000.0
                return ServiceHealthResult(
                    service_name=service_name,
                    status="FAIL",
                    endpoint=url,
                    response_time_ms=elapsed_ms,
                    error_message=str(e)
                )

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DeployMind-HealthChecker'})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = (time.time() - start_time) * 1000.0
                if resp.status == 200:
                    return ServiceHealthResult(
                        service_name=service_name,
                        status="PASS",
                        endpoint=url,
                        response_time_ms=elapsed_ms,
                        error_message=None
                    )
                else:
                    return ServiceHealthResult(
                        service_name=service_name,
                        status="FAIL",
                        endpoint=url,
                        response_time_ms=elapsed_ms,
                        error_message=f"HTTP Status {resp.status}"
                    )
        except urllib.error.HTTPError as e:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return ServiceHealthResult(
                service_name=service_name,
                status="FAIL",
                endpoint=url,
                response_time_ms=elapsed_ms,
                error_message=f"HTTP Error {e.code}: {e.reason}"
            )
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return ServiceHealthResult(
                service_name=service_name,
                status="FAIL",
                endpoint=url,
                response_time_ms=elapsed_ms,
                error_message=str(e)
            )

    def run_health_checks(self) -> HealthCheckReport:
        results: List[ServiceHealthResult] = []
        passed_count = 0
        failed_count = 0

        for service_name, url in self.service_urls.items():
            result = self.check_service(service_name, url)
            results.append(result)
            if result.status == "PASS":
                passed_count += 1
            else:
                failed_count += 1

        overall_status = "PASS" if failed_count == 0 else "FAIL"

        return HealthCheckReport(
            status=overall_status,
            total_checked=len(results),
            passed_count=passed_count,
            failed_count=failed_count,
            results=results
        )


def run_health_checks(service_urls: Optional[Dict[str, str]] = None, timeout: float = 5.0) -> Dict[str, Any]:
    checker = HealthChecker(service_urls=service_urls, timeout=timeout)
    return checker.run_health_checks().to_dict()


def run_health_checks_to_json(service_urls: Optional[Dict[str, str]] = None, timeout: float = 5.0, indent: int = 2) -> str:
    checker = HealthChecker(service_urls=service_urls, timeout=timeout)
    return json.dumps(checker.run_health_checks().to_dict(), indent=indent)


if __name__ == "__main__":
    urls = None
    if len(sys.argv) > 1 and sys.argv[1] == "--container":
        urls = HealthChecker.CONTAINER_SERVICES
    print(run_health_checks_to_json(service_urls=urls))
