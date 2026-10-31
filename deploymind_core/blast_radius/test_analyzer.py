import unittest
from .analyzer import BlastRadiusAnalyzer, analyze_blast_radius, analyze_blast_radius_to_json


class TestBlastRadiusAnalyzer(unittest.TestCase):
    def setUp(self):
        self.sample_graph = {
            "gateway": ["task_service"],
            "task_service": ["worker_service", "database"],
            "analytics": ["worker_service"],
            "worker_service": [],
            "database": []
        }

    def test_worker_service_change(self):
        result = analyze_blast_radius("worker_service", self.sample_graph)
        self.assertEqual(result["changed_service"], "worker_service")
        self.assertEqual(sorted(result["directly_affected_services"]), ["analytics", "task_service"])
        self.assertEqual(result["indirectly_affected_services"], ["gateway"])
        self.assertEqual(result["total_affected_service_count"], 3)
        self.assertIn("gateway -> task_service -> worker_service", result["dependency_chains"])
        self.assertIn("analytics -> worker_service", result["dependency_chains"])

    def test_task_service_change(self):
        result = analyze_blast_radius("task_service", self.sample_graph)
        self.assertEqual(result["directly_affected_services"], ["gateway"])
        self.assertEqual(result["indirectly_affected_services"], [])
        self.assertEqual(result["total_affected_service_count"], 1)
        self.assertIn("gateway -> task_service", result["dependency_chains"])

    def test_gateway_change(self):
        result = analyze_blast_radius("gateway", self.sample_graph)
        self.assertEqual(result["directly_affected_services"], [])
        self.assertEqual(result["indirectly_affected_services"], [])
        self.assertEqual(result["total_affected_service_count"], 0)
        self.assertEqual(result["dependency_chains"], [])

    def test_with_dependency_analyzer_output_format(self):
        dep_output = {
            "services": ["gateway", "task_service", "worker_service"],
            "graph": {
                "gateway": ["task_service"],
                "task_service": ["worker_service"],
                "worker_service": []
            }
        }
        result = analyze_blast_radius("worker_service", dep_output)
        self.assertEqual(result["directly_affected_services"], ["task_service"])
        self.assertEqual(result["indirectly_affected_services"], ["gateway"])
        self.assertEqual(result["total_affected_service_count"], 2)


if __name__ == "__main__":
    unittest.main()
