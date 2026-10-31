import json
import time
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from .models import LoadTestResult
except ImportError:
    from models import LoadTestResult


class LoadTester:
    """Performs concurrent load testing against the API Gateway's POST /tasks endpoint."""

    def __init__(
        self,
        gateway_url: str = "http://localhost:8000",
        total_requests: int = 10,
        concurrency: int = 2,
        timeout: float = 5.0
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.total_requests = max(1, total_requests)
        self.concurrency = max(1, concurrency)
        self.timeout = timeout

    def _send_request(self, idx: int) -> Tuple[bool, float, Optional[str]]:
        url = f"{self.gateway_url}/tasks"
        payload = {"title": f"Load Test Task #{idx}", "payload": {"index": idx}}
        start_time = time.time()

        if HAS_HTTPX:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload)
                    elapsed_ms = (time.time() - start_time) * 1000.0
                    success = resp.status_code in (200, 201)
                    err = None if success else f"HTTP {resp.status_code}"
                    return success, elapsed_ms, err
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000.0
                return False, elapsed_ms, str(e)
        else:
            json_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=json_bytes,
                headers={"Content-Type": "application/json", "User-Agent": "DeployMind-LoadTester"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    elapsed_ms = (time.time() - start_time) * 1000.0
                    success = resp.status in (200, 201)
                    err = None if success else f"HTTP {resp.status}"
                    return success, elapsed_ms, err
            except urllib.error.HTTPError as e:
                elapsed_ms = (time.time() - start_time) * 1000.0
                return False, elapsed_ms, f"HTTP Error {e.code}"
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000.0
                return False, elapsed_ms, str(e)

    def run_load_test(self) -> LoadTestResult:
        successful_count = 0
        failed_count = 0
        response_times: List[float] = []

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = [
                executor.submit(self._send_request, i)
                for i in range(1, self.total_requests + 1)
            ]
            for future in as_completed(futures):
                success, elapsed_ms, err = future.result()
                response_times.append(elapsed_ms)
                if success:
                    successful_count += 1
                else:
                    failed_count += 1

        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0.0
        )
        success_rate = (
            (successful_count / self.total_requests) * 100.0
            if self.total_requests > 0
            else 0.0
        )
        overall_status = "PASS" if success_rate >= 90.0 else "FAIL"

        return LoadTestResult(
            status=overall_status,
            total_requests=self.total_requests,
            successful_requests=successful_count,
            failed_requests=failed_count,
            average_response_time_ms=avg_response_time,
            success_rate=success_rate,
            concurrency=self.concurrency,
            gateway_url=self.gateway_url
        )


def run_load_test(
    gateway_url: str = "http://localhost:8000",
    total_requests: int = 10,
    concurrency: int = 2,
    timeout: float = 5.0
) -> Dict[str, Any]:
    tester = LoadTester(
        gateway_url=gateway_url,
        total_requests=total_requests,
        concurrency=concurrency,
        timeout=timeout
    )
    return tester.run_load_test().to_dict()


def run_load_test_to_json(
    gateway_url: str = "http://localhost:8000",
    total_requests: int = 10,
    concurrency: int = 2,
    timeout: float = 5.0,
    indent: int = 2
) -> str:
    tester = LoadTester(
        gateway_url=gateway_url,
        total_requests=total_requests,
        concurrency=concurrency,
        timeout=timeout
    )
    return json.dumps(tester.run_load_test().to_dict(), indent=indent)


if __name__ == "__main__":
    gw_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    num_reqs = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    conc = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    print(run_load_test_to_json(gateway_url=gw_url, total_requests=num_reqs, concurrency=conc))
