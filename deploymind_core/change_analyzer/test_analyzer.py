import unittest
from .analyzer import ChangeAnalyzer, analyze_diff, analyze_diff_to_json


class TestChangeAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ChangeAnalyzer()

    def test_determine_affected_service(self):
        self.assertEqual(ChangeAnalyzer.determine_affected_service("app/gateway/main.py"), "gateway")
        self.assertEqual(ChangeAnalyzer.determine_affected_service("app/task_service/models.py"), "task_service")
        self.assertEqual(ChangeAnalyzer.determine_affected_service("deploymind_core/change_analyzer/analyzer.py"), "change_analyzer")
        self.assertEqual(ChangeAnalyzer.determine_affected_service("monitoring/prometheus.yml"), "monitoring")
        self.assertEqual(ChangeAnalyzer.determine_affected_service("docker-compose.yml"), "root")

    def test_analyze_modified_diff(self):
        diff_text = """diff --git a/app/gateway/main.py b/app/gateway/main.py
index 1234567..89abcdef 100644
--- a/app/gateway/main.py
+++ b/app/gateway/main.py
@@ -1,5 +1,6 @@
-old line
+new line 1
+new line 2
"""
        result = self.analyzer.analyze_diff(diff_text).to_dict()
        self.assertEqual(result["summary"]["total_changed_files"], 1)
        self.assertEqual(result["summary"]["total_added_lines"], 2)
        self.assertEqual(result["summary"]["total_deleted_lines"], 1)
        self.assertEqual(result["summary"]["affected_services"], ["gateway"])

        file_change = result["changed_files"][0]
        self.assertEqual(file_change["file_path"], "app/gateway/main.py")
        self.assertEqual(file_change["affected_service"], "gateway")
        self.assertEqual(file_change["change_type"], "modified")
        self.assertEqual(file_change["added_lines"], 2)
        self.assertEqual(file_change["deleted_lines"], 1)

    def test_analyze_added_file_diff(self):
        diff_text = """diff --git a/app/worker_service/new_task.py b/app/worker_service/new_task.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/app/worker_service/new_task.py
@@ -0,0 +1,3 @@
+line 1
+line 2
+line 3
"""
        result = analyze_diff(diff_text)
        self.assertEqual(result["summary"]["total_changed_files"], 1)
        file_change = result["changed_files"][0]
        self.assertEqual(file_change["file_path"], "app/worker_service/new_task.py")
        self.assertEqual(file_change["affected_service"], "worker_service")
        self.assertEqual(file_change["change_type"], "added")
        self.assertEqual(file_change["added_lines"], 3)
        self.assertEqual(file_change["deleted_lines"], 0)

    def test_analyze_diff_to_json(self):
        diff_text = """diff --git a/app/gateway/main.py b/app/gateway/main.py
--- a/app/gateway/main.py
+++ b/app/gateway/main.py
+added line
"""
        json_output = analyze_diff_to_json(diff_text)
        self.assertIn('"affected_service": "gateway"', json_output)
        self.assertIn('"change_type": "modified"', json_output)


if __name__ == "__main__":
    unittest.main()
