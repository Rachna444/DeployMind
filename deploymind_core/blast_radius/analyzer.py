import json
import sys
from typing import Dict, List, Set, Any, Union, Optional

try:
    from .models import BlastRadiusResult
except ImportError:
    from models import BlastRadiusResult


class BlastRadiusAnalyzer:
    """Analyzes the blast radius of changes to a service given a dependency graph."""

    @staticmethod
    def normalize_graph(dependency_graph: Dict[str, Any]) -> Dict[str, List[str]]:
        """Normalizes dependency graph input (handles raw dict or DependencyAnalyzer output dict)."""
        if "graph" in dependency_graph and isinstance(dependency_graph["graph"], dict):
            return dependency_graph["graph"]
        return dependency_graph

    def analyze(
        self,
        changed_service: Union[str, List[str]],
        dependency_graph: Dict[str, Any]
    ) -> BlastRadiusResult:
        graph = self.normalize_graph(dependency_graph)

        targets_to_analyze: Set[str] = set()
        if isinstance(changed_service, str):
            targets_to_analyze.add(changed_service)
        elif isinstance(changed_service, list):
            targets_to_analyze.update(changed_service)

        # Build reverse graph: target -> callers (who depends on target)
        reverse_graph: Dict[str, Set[str]] = {}
        for caller, targets in graph.items():
            if caller not in reverse_graph:
                reverse_graph[caller] = set()
            for target in targets:
                if target not in reverse_graph:
                    reverse_graph[target] = set()
                reverse_graph[target].add(caller)

        directly_affected: Set[str] = set()
        indirectly_affected: Set[str] = set()
        dependency_chains: List[str] = []

        for target in targets_to_analyze:
            direct_callers = reverse_graph.get(target, set())
            directly_affected.update(direct_callers)

            # Find all path chains using DFS
            self._find_chains(target, reverse_graph, [target], dependency_chains)

            # Find all reachable nodes transitively
            visited: Set[str] = set([target])
            queue = list(direct_callers)
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                if current not in direct_callers:
                    indirectly_affected.add(current)

                parents = reverse_graph.get(current, set())
                for parent in parents:
                    if parent not in visited:
                        queue.append(parent)

        indirectly_affected = indirectly_affected - directly_affected - targets_to_analyze
        total_count = len(directly_affected | indirectly_affected)

        return BlastRadiusResult(
            changed_service=changed_service,
            directly_affected_services=sorted(list(directly_affected)),
            indirectly_affected_services=sorted(list(indirectly_affected)),
            dependency_chains=sorted(list(set(dependency_chains))),
            total_affected_service_count=total_count
        )

    def _find_chains(
        self,
        current_node: str,
        reverse_graph: Dict[str, Set[str]],
        current_path: List[str],
        chains: List[str],
        visited: Optional[Set[str]] = None
    ) -> None:
        if visited is None:
            visited = set()

        parents = reverse_graph.get(current_node, set())
        if not parents:
            if len(current_path) > 1:
                reversed_chain = " -> ".join(reversed(current_path))
                chains.append(reversed_chain)
            return

        for parent in parents:
            if parent in visited or parent in current_path:
                reversed_chain = " -> ".join(reversed(current_path + [parent]))
                chains.append(reversed_chain)
                continue

            self._find_chains(
                parent,
                reverse_graph,
                current_path + [parent],
                chains,
                visited | {parent}
            )


def analyze_blast_radius(
    changed_service: Union[str, List[str]],
    dependency_graph: Dict[str, Any]
) -> Dict[str, Any]:
    analyzer = BlastRadiusAnalyzer()
    return analyzer.analyze(changed_service, dependency_graph).to_dict()


def analyze_blast_radius_to_json(
    changed_service: Union[str, List[str]],
    dependency_graph: Dict[str, Any],
    indent: int = 2
) -> str:
    analyzer = BlastRadiusAnalyzer()
    return json.dumps(analyzer.analyze(changed_service, dependency_graph).to_dict(), indent=indent)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        changed = sys.argv[1]
        graph_json = sys.argv[2]
        try:
            graph_data = json.loads(graph_json)
            print(analyze_blast_radius_to_json(changed, graph_data))
        except Exception as e:
            print(f"Error parsing graph json: {e}")
    else:
        sample_graph = {
            "gateway": ["task_service"],
            "task_service": ["worker_service"],
            "worker_service": []
        }
        print("Example Blast Radius Analysis for 'worker_service':")
        print(analyze_blast_radius_to_json("worker_service", sample_graph))
