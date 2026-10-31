import unittest
from unittest.mock import patch, MagicMock
from .checker import HealthChecker, run_health_checks, run_health_checks_to_json


class TestHealthChecker(unittest.TestCase):
    @patch.object(HealthChecker, 'check_service')
    def test_run_health_checks_all_pass(self, mock_check):
        from .models import ServiceHealthResult
        mock_check.side_effect = [
            ServiceHealthResult("gateway", "PASS", "http://localhost:8000/health", 10.5),
            ServiceHealthResult("task_service", "PASS", "http://localhost:8001/health", 8.2),
            ServiceHealthResult("worker_service", "PASS", "http://localhost:8002/health", 5.1),
        ]

        checker = HealthChecker()
        report = checker.run_health_checks().to_dict()

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["total_checked"], 3)
        self.assertEqual(report["passed_count"], 3)
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual(len(report["results"]), 3)

    @patch.object(HealthChecker, 'check_service')
    def test_run_health_checks_with_failure(self, mock_check):
        from .models import ServiceHealthResult
        mock_check.side_effect = [
            ServiceHealthResult("gateway", "PASS", "http://localhost:8000/health", 10.5),
            ServiceHealthResult("task_service", "FAIL", "http://localhost:8001/health", 500.0, "Connection Refused"),
            ServiceHealthResult("worker_service", "PASS", "http://localhost:8002/health", 5.1),
        ]

        checker = HealthChecker()
        report = checker.run_health_checks().to_dict()

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["passed_count"], 2)
        self.assertEqual(report["failed_count"], 1)

    def test_health_check_defaults(self):
        checker = HealthChecker()
        self.assertIn("gateway", checker.service_urls)
        self.assertIn("task_service", checker.service_urls)
        self.assertIn("worker_service", checker.service_urls)


if __name__ == "__main__":
    unittest.main()
