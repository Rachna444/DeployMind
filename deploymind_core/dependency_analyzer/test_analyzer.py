import unittest
import tempfile
import json
from pathlib import Path
from .analyzer import DependencyAnalyzer, analyze_dependencies, analyze_dependencies_to_json


class TestDependencyAnalyzer(unittest.TestCase):
    def test_real_project_analysis(self):
        analyzer = DependencyAnalyzer(root_dir=".")
        result = analyzer.analyze().to_dict()

        self.assertIn("gateway", result["services"])
        self.assertIn("task_service", result["services"])
        self.assertIn("worker_service", result["services"])

        # Check graph edges
        self.assertIn("task_service", result["graph"]["gateway"])
        self.assertIn("worker_service", result["graph"]["task_service"])

    def test_mock_project_analysis(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            app_dir = tmppath / "app"
            s1_dir = app_dir / "service_a"
            s2_dir = app_dir / "service_b"
            s1_dir.mkdir(parents=True)
            s2_dir.mkdir(parents=True)

            code_a = s1_dir / "main.py"
            code_a.write_text('import httpx\nres = httpx.get("http://service_b:8080/data")', encoding="utf-8")

            compose_file = tmppath / "docker-compose.yml"
            compose_file.write_text("""version: '3.8'
services:
  service_a:
    depends_on:
      - service_b
  service_b:
    ports:
      - "8080:8080"
""", encoding="utf-8")

            analyzer = DependencyAnalyzer(root_dir=tmpdir)
            result = analyzer.analyze().to_dict()

            self.assertIn("service_a", result["services"])
            self.assertIn("service_b", result["services"])
            self.assertIn("service_b", result["graph"]["service_a"])


if __name__ == "__main__":
    unittest.main()
