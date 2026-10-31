import unittest
from .orchestrator import DeployMindPipeline, run_pipeline, run_pipeline_to_json


class TestDeployMindPipeline(unittest.TestCase):
    def test_pipeline_dry_run_with_diff(self):
        diff_text = """diff --git a/app/worker_service/main.py b/app/worker_service/main.py
--- a/app/worker_service/main.py
+++ b/app/worker_service/main.py
+added line
"""
        pipeline = DeployMindPipeline(root_dir=".")
        report = pipeline.run_pipeline(diff_text=diff_text, execute_validations=False).to_dict()

        self.assertIn("changed_files", report)
        self.assertIn("affected_services", report)
        self.assertIn("blast_radius", report)
        self.assertIn("risk_score", report)
        self.assertIn("risk_level", report)
        self.assertIn("recommended_validations", report)
        self.assertIn("validation_results", report)
        self.assertIn("final_decision", report)
        self.assertIn("reason", report)

        self.assertEqual(report["risk_level"], "MEDIUM")
        self.assertIn("worker_service", report["affected_services"])
        self.assertEqual(report["final_decision"], "CANARY")

    def test_pipeline_to_json(self):
        diff_text = """diff --git a/app/gateway/main.py b/app/gateway/main.py
--- a/app/gateway/main.py
+++ b/app/gateway/main.py
+added line
"""
        json_output = run_pipeline_to_json(diff_text=diff_text, execute_validations=False)
        self.assertIn('"final_decision"', json_output)
        self.assertIn('"risk_level"', json_output)
        self.assertIn('"blast_radius"', json_output)


if __name__ == "__main__":
    unittest.main()
