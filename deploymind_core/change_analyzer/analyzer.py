import json
import re
import sys
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from .models import FileChange, ChangeAnalysisResult
except ImportError:
    from models import FileChange, ChangeAnalysisResult


class ChangeAnalyzer:
    """Analyzes Git diffs to identify changed files, affected services, change types, and line metrics."""

    @staticmethod
    def determine_affected_service(file_path: str) -> str:
        """Determines affected service based on file path."""
        path = file_path.strip().replace('\\', '/')
        parts = [p for p in path.split('/') if p and p != '.']
        
        if not parts:
            return "root"
        
        if parts[0] == "app" and len(parts) > 1:
            return parts[1]
        elif parts[0] == "deploymind_core" and len(parts) > 1:
            return parts[1]
        elif len(parts) > 1:
            return parts[0]
        
        return "root"

    def analyze_diff(self, diff_text: str) -> ChangeAnalysisResult:
        """Parses git diff output and returns structured analysis result."""
        if not diff_text or not diff_text.strip():
            return ChangeAnalysisResult(
                summary={
                    "total_changed_files": 0,
                    "total_added_lines": 0,
                    "total_deleted_lines": 0,
                    "affected_services": []
                },
                changed_files=[]
            )

        # Split diff into chunks per file (each starting with "diff --git")
        file_chunks = re.split(r'(^diff --git )', diff_text, flags=re.MULTILINE)
        
        diff_blocks = []
        for i in range(1, len(file_chunks), 2):
            block = file_chunks[i] + (file_chunks[i+1] if i+1 < len(file_chunks) else "")
            diff_blocks.append(block)

        if not diff_blocks and diff_text.strip():
            diff_blocks = [diff_text]

        file_changes: List[FileChange] = []
        total_additions = 0
        total_deletions = 0
        affected_services_set = set()

        for block in diff_blocks:
            lines = block.strip().splitlines()
            if not lines:
                continue

            file_path = None
            change_type = "modified"
            added_count = 0
            deleted_count = 0

            # Find file path and change type from block header
            header = lines[0]
            git_diff_match = re.search(r'diff --git a/(.*?)\s+b/(.*)', header)
            if git_diff_match:
                file_path = git_diff_match.group(2)

            for line in lines:
                if line.startswith("new file mode"):
                    change_type = "added"
                elif line.startswith("deleted file mode"):
                    change_type = "deleted"
                elif line.startswith("similarity index") or line.startswith("rename to"):
                    change_type = "renamed"
                elif line.startswith("--- /dev/null"):
                    change_type = "added"
                elif line.startswith("+++ /dev/null"):
                    change_type = "deleted"
                elif line.startswith("+++ b/"):
                    if not file_path:
                        file_path = line[6:]
                elif line.startswith("--- a/"):
                    if not file_path and change_type == "deleted":
                        file_path = line[6:]

            if not file_path and git_diff_match:
                file_path = git_diff_match.group(1)

            if not file_path:
                continue

            # Count line changes
            for line in lines:
                if line.startswith("+") and not line.startswith("+++"):
                    added_count += 1
                elif line.startswith("-") and not line.startswith("---"):
                    deleted_count += 1

            service = self.determine_affected_service(file_path)
            affected_services_set.add(service)
            total_additions += added_count
            total_deletions += deleted_count

            file_changes.append(
                FileChange(
                    file_path=file_path,
                    affected_service=service,
                    change_type=change_type,
                    added_lines=added_count,
                    deleted_lines=deleted_count
                )
            )

        summary = {
            "total_changed_files": len(file_changes),
            "total_added_lines": total_additions,
            "total_deleted_lines": total_deletions,
            "affected_services": sorted(list(affected_services_set))
        }

        return ChangeAnalysisResult(summary=summary, changed_files=file_changes)

    def analyze_repo_git_diff(self, repo_path: str = ".", target: Optional[str] = None) -> ChangeAnalysisResult:
        """Executes `git diff` on target repo and analyzes output."""
        cmd = ["git", "diff"]
        if target:
            cmd.append(target)

        try:
            res = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=True)
            diff_text = res.stdout
        except Exception:
            diff_text = ""

        return self.analyze_diff(diff_text)


def analyze_diff(diff_text: str) -> Dict[str, Any]:
    """Convenience function to analyze diff text and return structured dictionary."""
    analyzer = ChangeAnalyzer()
    return analyzer.analyze_diff(diff_text).to_dict()


def analyze_diff_to_json(diff_text: str, indent: int = 2) -> str:
    """Convenience function to analyze diff text and return JSON string."""
    analyzer = ChangeAnalyzer()
    return json.dumps(analyzer.analyze_diff(diff_text).to_dict(), indent=indent)


if __name__ == "__main__":
    analyzer = ChangeAnalyzer()
    if len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        diff_input = sys.stdin.read()
        print(json.dumps(analyzer.analyze_diff(diff_input).to_dict(), indent=2))
    else:
        # Analyze current repository git diff by default
        result = analyzer.analyze_repo_git_diff()
        print(json.dumps(result.to_dict(), indent=2))
