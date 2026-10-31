import unittest
from .agent import ValidationAgent, select_validations, select_validations_to_json


class TestValidationAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ValidationAgent()

    def test_low_risk_validations(self):
        result = self.agent.select_validations(
            risk_level="LOW",
            risk_score=10.0,
            affected_services=[],
            blast_radius={"total_affected_service_count": 0}
        ).to_dict()

        self.assertEqual(result["risk_level"], "LOW")
        self.assertIn("health_checks", result["recommended_validations"])
        self.assertNotIn("load_tests", result["recommended_validations"])

    def test_medium_risk_validations(self):
        blast_radius = {
            "directly_affected_services": ["task_service"],
            "indirectly_affected_services": ["gateway"],
            "total_affected_service_count": 2
        }
        result = self.agent.select_validations(
            risk_level="MEDIUM",
            risk_score=50.0,
            affected_services=["worker_service"],
            blast_radius=blast_radius
        ).to_dict()

        self.assertEqual(result["risk_level"], "MEDIUM")
        self.assertIn("health_checks", result["recommended_validations"])
        self.assertIn("api_tests", result["recommended_validations"])
        self.assertIn("dependency_validation", result["recommended_validations"])
        self.assertNotIn("load_tests", result["recommended_validations"])

    def test_high_risk_validations(self):
        blast_radius = {
            "directly_affected_services": ["task_service", "analytics"],
            "indirectly_affected_services": ["gateway"],
            "total_affected_service_count": 3
        }
        result = self.agent.select_validations(
            risk_level="HIGH",
            risk_score=85.0,
            affected_services=["worker_service"],
            blast_radius=blast_radius
        ).to_dict()

        self.assertEqual(result["risk_level"], "HIGH")
        self.assertIn("health_checks", result["recommended_validations"])
        self.assertIn("api_tests", result["recommended_validations"])
        self.assertIn("dependency_validation", result["recommended_validations"])
        self.assertIn("load_tests", result["recommended_validations"])

    def test_convenience_function(self):
        json_output = select_validations_to_json("HIGH", 75.0)
        self.assertIn('"risk_level": "HIGH"', json_output)
        self.assertIn('"recommended_validations"', json_output)
        self.assertIn('"reasoning"', json_output)


if __name__ == "__main__":
    unittest.main()
