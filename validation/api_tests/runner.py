import json
import sys
import time
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Tuple

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from .models import APITestResult, APITestSuiteReport
except ImportError:
    from models import APITestResult, APITestSuiteReport


class APITestRunner:
    """Runs end-to-end API integration tests through the API Gateway."""

    def __init__(self, gateway_url: str = "http://localhost:8000", timeout: float = 10.0):
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = timeout

    def _http_post(self, path: str, data: Optional[dict] = None) -> Tuple[int, Any]:
        url = f"{self.gateway_url}{path}"
        if HAS_HTTPX:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=data or {})
                    try:
                        res_data = resp.json()
                    except Exception:
                        res_data = resp.text
                    return resp.status_code, res_data
            except Exception as e:
                return 500, str(e)
        else:
            json_bytes = json.dumps(data or {}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=json_bytes,
                headers={"Content-Type": "application/json", "User-Agent": "DeployMind-APITestRunner"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    try:
                        res_data = json.loads(raw)
                    except Exception:
                        res_data = raw
                    return resp.status, res_data
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8")
                try:
                    res_data = json.loads(raw)
                except Exception:
                    res_data = raw
                return e.code, res_data
            except Exception as e:
                return 500, str(e)

    def _http_get(self, path: str) -> Tuple[int, Any]:
        url = f"{self.gateway_url}{path}"
        if HAS_HTTPX:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url)
                    try:
                        res_data = resp.json()
                    except Exception:
                        res_data = resp.text
                    return resp.status_code, res_data
            except Exception as e:
                return 500, str(e)
        else:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "DeployMind-APITestRunner"},
                method="GET"
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    try:
                        res_data = json.loads(raw)
                    except Exception:
                        res_data = raw
                    return resp.status, res_data
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8")
                try:
                    res_data = json.loads(raw)
                except Exception:
                    res_data = raw
                return e.code, res_data
            except Exception as e:
                return 500, str(e)

    def run_tests(self) -> APITestSuiteReport:
        tests: List[APITestResult] = []
        created_task_id = None

        # Test 1: POST /tasks (Create Task)
        try:
            payload = {"title": "Integration Test Task", "payload": {"test_run": True}}
            status_code, data = self._http_post("/tasks", payload)
            if status_code in (200, 201) and isinstance(data, dict):
                created_task_id = data.get("id") or data.get("task_id")
                if created_task_id:
                    tests.append(APITestResult("create_task", "PASS", None))
                else:
                    tests.append(APITestResult("create_task", "FAIL", f"Missing task ID in response: {data}"))
            else:
                tests.append(APITestResult("create_task", "FAIL", f"HTTP {status_code}: {data}"))
        except Exception as e:
            tests.append(APITestResult("create_task", "FAIL", str(e)))

        # Test 2: GET /tasks (Fetch Tasks)
        try:
            status_code, data = self._http_get("/tasks")
            if status_code == 200 and isinstance(data, list):
                if created_task_id:
                    found = any(t.get("id") == created_task_id or t.get("task_id") == created_task_id for t in data if isinstance(t, dict))
                    if found:
                        tests.append(APITestResult("fetch_tasks", "PASS", None))
                    else:
                        tests.append(APITestResult("fetch_tasks", "FAIL", f"Task ID '{created_task_id}' not found in task list."))
                else:
                    tests.append(APITestResult("fetch_tasks", "PASS", None))
            else:
                tests.append(APITestResult("fetch_tasks", "FAIL", f"HTTP {status_code}: {data}"))
        except Exception as e:
            tests.append(APITestResult("fetch_tasks", "FAIL", str(e)))

        # Test 3: POST /tasks/{task_id}/process (Process Task)
        process_res_data = None
        try:
            if created_task_id:
                status_code, process_res_data = self._http_post(f"/tasks/{created_task_id}/process", {})
                if status_code == 200:
                    tests.append(APITestResult("process_task", "PASS", None))
                else:
                    tests.append(APITestResult("process_task", "FAIL", f"HTTP {status_code}: {process_res_data}"))
            else:
                tests.append(APITestResult("process_task", "FAIL", "Skipped: task creation failed in previous step."))
        except Exception as e:
            tests.append(APITestResult("process_task", "FAIL", str(e)))

        # Test 4: Verify Processed Task Status is 'completed'
        try:
            if created_task_id and process_res_data:
                task_obj = process_res_data.get("task", {}) if isinstance(process_res_data, dict) else {}
                task_status = task_obj.get("status") if isinstance(task_obj, dict) else None

                if task_status == "completed":
                    tests.append(APITestResult("verify_task_completed", "PASS", None))
                else:
                    status_code, data = self._http_get("/tasks")
                    if status_code == 200 and isinstance(data, list):
                        matching = [t for t in data if isinstance(t, dict) and (t.get("id") == created_task_id or t.get("task_id") == created_task_id)]
                        if matching and matching[0].get("status") == "completed":
                            tests.append(APITestResult("verify_task_completed", "PASS", None))
                        else:
                            curr_st = matching[0].get("status") if matching else "not found"
                            tests.append(APITestResult("verify_task_completed", "FAIL", f"Expected status 'completed', got '{curr_st}'."))
                    else:
                        tests.append(APITestResult("verify_task_completed", "FAIL", f"Status was '{task_status}' in process response."))
            else:
                tests.append(APITestResult("verify_task_completed", "FAIL", "Skipped: process task step was not executed."))
        except Exception as e:
            tests.append(APITestResult("verify_task_completed", "FAIL", str(e)))

        passed_count = sum(1 for t in tests if t.status == "PASS")
        failed_count = sum(1 for t in tests if t.status == "FAIL")
        overall_status = "PASS" if failed_count == 0 else "FAIL"

        return APITestSuiteReport(
            status=overall_status,
            total_tests=len(tests),
            passed_count=passed_count,
            failed_count=failed_count,
            gateway_url=self.gateway_url,
            tests=tests
        )


def run_api_tests(gateway_url: str = "http://localhost:8000", timeout: float = 10.0) -> Dict[str, Any]:
    runner = APITestRunner(gateway_url=gateway_url, timeout=timeout)
    return runner.run_tests().to_dict()


def run_api_tests_to_json(gateway_url: str = "http://localhost:8000", timeout: float = 10.0, indent: int = 2) -> str:
    runner = APITestRunner(gateway_url=gateway_url, timeout=timeout)
    return json.dumps(runner.run_tests().to_dict(), indent=indent)


if __name__ == "__main__":
    gw_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    print(run_api_tests_to_json(gateway_url=gw_url))
