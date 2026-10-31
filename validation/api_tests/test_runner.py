import unittest
from unittest.mock import patch
from .runner import APITestRunner, run_api_tests, run_api_tests_to_json


class TestAPITestRunner(unittest.TestCase):
    @patch.object(APITestRunner, '_http_get')
    @patch.object(APITestRunner, '_http_post')
    def test_run_tests_success_flow(self, mock_post, mock_get):
        mock_post.side_effect = [
            # 1. POST /tasks
            (201, {"id": "test-uuid-123", "title": "Integration Test Task", "status": "pending"}),
            # 2. POST /tasks/test-uuid-123/process
            (200, {
                "message": "Task sent for processing",
                "task": {"id": "test-uuid-123", "title": "Integration Test Task", "status": "completed"}
            })
        ]
        mock_get.side_effect = [
            # 1. GET /tasks
            (200, [{"id": "test-uuid-123", "title": "Integration Test Task", "status": "pending"}])
        ]

        runner = APITestRunner(gateway_url="http://localhost:8000")
        report = runner.run_tests().to_dict()

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["total_tests"], 4)
        self.assertEqual(report["passed_count"], 4)
        self.assertEqual(report["failed_count"], 0)

        test_names = [t["test_name"] for t in report["tests"]]
        self.assertEqual(test_names, ["create_task", "fetch_tasks", "process_task", "verify_task_completed"])

    @patch.object(APITestRunner, '_http_get')
    @patch.object(APITestRunner, '_http_post')
    def test_run_tests_failure_flow(self, mock_post, mock_get):
        mock_post.side_effect = [
            # 1. POST /tasks fails
            (503, "Task Service Unavailable")
        ]

        runner = APITestRunner(gateway_url="http://localhost:8000")
        report = runner.run_tests().to_dict()

        self.assertEqual(report["status"], "FAIL")
        self.assertGreater(report["failed_count"], 0)
        self.assertEqual(report["tests"][0]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
