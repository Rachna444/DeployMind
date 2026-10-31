from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class FileChange:
    file_path: str
    affected_service: str
    change_type: str  # "added", "deleted", "modified", "renamed"
    added_lines: int
    deleted_lines: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeAnalysisResult:
    summary: Dict[str, Any]
    changed_files: List[FileChange]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "changed_files": [f.to_dict() for f in self.changed_files]
        }
