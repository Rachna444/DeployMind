import unittest
from .engine import DecisionEngine, evaluate_decision, evaluate_decision_to_json


class TestDecisionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DecisionEngine()

    def test_low_risk_all_pass_returns_safe(self):
        validations = {"health_checks": "PASSED"}
        result = self.engine.make_decision(15.0, "LOW", validations).to_dict()

        self.assertEqual(result["decision"], "SAFE")
        self.assertEqual(result["risk_level"], "LOW")
        self.assertIn("SAFE", result["reason"])

    def test_medium_risk_all_pass_returns_canary(self):
        validations = {"health_checks": "PASSED", "api_tests": "PASSED"}
        result = self.engine.make_decision(55.0, "MEDIUM", validations).to_dict()

        self.assertEqual(result["decision"], "CANARY")
        self.assertEqual(result["risk_level"], "MEDIUM")
        self.assertIn("CANARY", result["reason"])

    def test_high_risk_all_pass_returns_canary(self):
        validations = {"health_checks": "PASSED", "api_tests": "PASSED", "load_tests": "PASSED"}
        result = self.engine.make_decision(85.0, "HIGH", validations).to_dict()

        self.assertEqual(result["decision"], "CANARY")
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertIn("CANARY", result["reason"])

    def test_any_failed_validation_returns_blocked(self):
        validations = {"health_checks": "PASSED", "api_tests": "FAILED"}
        
        # Test for LOW risk with failure
        result_low = self.engine.make_decision(10.0, "LOW", validations).to_dict()
        self.assertEqual(result_low["decision"], "BLOCKED")
        self.assertIn("BLOCKED", result_low["reason"])

        # Test for MEDIUM risk with failure
        result_med = self.engine.make_decision(50.0, "MEDIUM", validations).to_dict()
        self.assertEqual(result_med["decision"], "BLOCKED")

        # Test for HIGH risk with failure
        result_high = self.engine.make_decision(80.0, "HIGH", validations).to_dict()
        self.assertEqual(result_high["decision"], "BLOCKED")

    def test_convenience_function(self):
        json_output = evaluate_decision_to_json(20.0, "LOW", {"health_checks": "PASSED"})
        self.assertIn('"decision": "SAFE"', json_output)
        self.assertIn('"reason"', json_output)


if __name__ == "__main__":
    unittest.main()
