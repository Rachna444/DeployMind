import unittest
from .engine import RiskEngine, calculate_risk_score, calculate_risk_score_to_json


class TestRiskEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RiskEngine()

    def test_low_risk_scenario(self):
        result = self.engine.calculate_risk(
            affected_service="worker_service",
            added_lines=5,
            deleted_lines=0,
            changed_files_count=1,
            change_types=["modified"],
            directly_affected_count=0,
            indirectly_affected_count=0,
        ).to_dict()

        self.assertLess(result["risk_score"], 35)
        self.assertEqual(result["risk_level"], "LOW")
        self.assertTrue(len(result["factors"]) > 0)

    def test_medium_risk_scenario(self):
        change_analysis = {
            "summary": {
                "total_changed_files": 2,
                "total_added_lines": 50,
                "total_deleted_lines": 10,
            },
            "changed_files": [
                {"file_path": "app/task_service/main.py", "affected_service": "task_service", "change_type": "modified"}
            ]
        }
        blast_radius = {
            "changed_service": "task_service",
            "directly_affected_services": ["gateway"],
            "indirectly_affected_services": [],
            "dependency_chains": ["gateway -> task_service"]
        }

        result = self.engine.calculate_risk(
            change_analysis=change_analysis,
            blast_radius=blast_radius
        ).to_dict()

        self.assertTrue(35 <= result["risk_score"] < 70)
        self.assertEqual(result["risk_level"], "MEDIUM")

    def test_high_risk_scenario(self):
        change_analysis = {
            "summary": {
                "total_changed_files": 5,
                "total_added_lines": 300,
                "total_deleted_lines": 150,
            },
            "changed_files": [
                {"file_path": "app/gateway/main.py", "affected_service": "gateway", "change_type": "modified"},
                {"file_path": "docker-compose.yml", "affected_service": "root", "change_type": "deleted"}
            ]
        }
        blast_radius = {
            "changed_service": "worker_service",
            "directly_affected_services": ["task_service", "analytics"],
            "indirectly_affected_services": ["gateway", "dashboard"],
            "dependency_chains": ["gateway -> task_service -> worker_service"]
        }

        result = self.engine.calculate_risk(
            change_analysis=change_analysis,
            blast_radius=blast_radius
        ).to_dict()

        self.assertGreaterEqual(result["risk_score"], 70)
        self.assertEqual(result["risk_level"], "HIGH")

    def test_convenience_functions(self):
        json_str = calculate_risk_score_to_json(
            affected_service="gateway",
            added_lines=10,
            changed_files_count=1
        )
        self.assertIn('"risk_level"', json_str)
        self.assertIn('"factors"', json_str)


if __name__ == "__main__":
    unittest.main()
