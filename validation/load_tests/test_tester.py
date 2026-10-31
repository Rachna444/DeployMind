import unittest
from unittest.mock import patch
from .tester import LoadTester, run_load_test, run_load_test_to_json


class TestLoadTester(unittest.TestCase):
    @patch.object(LoadTester, '_send_request')
    def test_run_load_test_success(self, mock_send):
        # Mock 10 successful requests with average ~15ms response time
        mock_send.return_value = (True, 15.0, None)

        tester = LoadTester(gateway_url="http://localhost:8000", total_requests=10, concurrency=2)
        report = tester.run_load_test().to_dict()

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["total_requests"], 10)
        self.assertEqual(report["successful_requests"], 10)
        self.assertEqual(report["failed_requests"], 0)
        self.assertEqual(report["success_rate"], 100.0)
        self.assertEqual(report["average_response_time_ms"], 15.0)

    @patch.object(LoadTester, '_send_request')
    def test_run_load_test_failures(self, mock_send):
        # Mock 5 successes and 5 failures
        mock_send.side_effect = [
            (True, 10.0, None), (False, 20.0, "HTTP 500"),
            (True, 10.0, None), (False, 20.0, "HTTP 500"),
            (True, 10.0, None), (False, 20.0, "HTTP 500"),
            (True, 10.0, None), (False, 20.0, "HTTP 500"),
            (True, 10.0, None), (False, 20.0, "HTTP 500"),
        ]

        tester = LoadTester(gateway_url="http://localhost:8000", total_requests=10, concurrency=2)
        report = tester.run_load_test().to_dict()

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["successful_requests"], 5)
        self.assertEqual(report["failed_requests"], 5)
        self.assertEqual(report["success_rate"], 50.0)

    def test_convenience_function(self):
        with patch.object(LoadTester, '_send_request', return_value=(True, 12.0, None)):
            json_output = run_load_test_to_json(total_requests=5, concurrency=2)
            self.assertIn('"success_rate": 100.0', json_output)
            self.assertIn('"total_requests": 5', json_output)


if __name__ == "__main__":
    unittest.main()
