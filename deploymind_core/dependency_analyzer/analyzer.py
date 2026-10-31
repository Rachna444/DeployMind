import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

try:
    from .models import ServiceDependency, DependencyGraphResult
except ImportError:
    from models import ServiceDependency, DependencyGraphResult


class DependencyAnalyzer:
    """Analyzes codebase and configuration files to discover service-to-service dependencies."""

    def __init__(self, root_dir: str = "."):
        self.root_path = Path(root_dir).resolve()

    def discover_services(self) -> Dict[str, str]:
        """Discovers service names mapped to their directory paths."""
        services = {}
        app_dir = self.root_path / "app"
        if app_dir.is_dir():
            for item in app_dir.iterdir():
                if item.is_dir() and not item.name.startswith(('.', '_')):
                    services[item.name] = str(item.relative_to(self.root_path)).replace('\\', '/')
        return services

    def analyze_docker_compose(self, services: Set[str]) -> List[ServiceDependency]:
        """Parses docker-compose file for service definitions and depends_on relations."""
        dependencies = []
        compose_file = None
        for name in ["docker-compose.yml", "docker-compose.yaml"]:
            path = self.root_path / name
            if path.is_file():
                compose_file = path
                break

        if not compose_file:
            return dependencies

        rel_source = str(compose_file.relative_to(self.root_path)).replace('\\', '/')
        try:
            content = compose_file.read_text(encoding="utf-8")
        except Exception:
            return dependencies

        current_service = None
        in_services_section = False
        in_depends_on = False

        lines = content.splitlines()
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Check top-level sections (0-indentation)
            if re.match(r'^[a-zA-Z0-9_\-]+:\s*$', line):
                in_services_section = line.startswith("services:")
                current_service = None
                in_depends_on = False
                continue

            if in_services_section:
                # Detect service block (2-indentation under services:)
                service_match = re.match(r'^\s{2}([a-zA-Z0-9_\-]+):\s*$', line)
                if service_match:
                    current_service = service_match.group(1)
                    services.add(current_service)
                    in_depends_on = False
                    continue

                if current_service:
                    if re.match(r'^\s{4}depends_on:\s*$', line):
                        in_depends_on = True
                        continue

                    if re.match(r'^\s{4}[a-zA-Z0-9_\-]+:\s*', line) and not stripped.startswith("-"):
                        in_depends_on = False

                    if in_depends_on:
                        dep_match = re.match(r'^\s{6}-\s*([a-zA-Z0-9_\-]+)', line)
                        if dep_match:
                            target = dep_match.group(1)
                            services.add(target)
                            dependencies.append(
                                ServiceDependency(
                                    caller=current_service,
                                    target=target,
                                    type="docker_depends_on",
                                    source_file=rel_source
                                )
                            )

        return dependencies

    def analyze_code_dependencies(self, known_services: Set[str]) -> List[ServiceDependency]:
        """Scans codebase (.py files) for HTTP calls and service references."""
        dependencies = []
        app_dir = self.root_path / "app"
        search_dirs = [app_dir] if app_dir.is_dir() else [self.root_path]

        port_map = {}
        for s in known_services:
            if "gateway" in s:
                port_map["8000"] = s
            elif "task" in s:
                port_map["8001"] = s
            elif "worker" in s:
                port_map["8002"] = s

        url_pattern = re.compile(r'https?://([a-zA-Z0-9_\-]+)(?::(\d+))?(/[^\s"\'\`\)]*)?')

        for s_dir in search_dirs:
            for py_file in s_dir.rglob("*.py"):
                if "__pycache__" in py_file.parts:
                    continue

                rel_path = str(py_file.relative_to(self.root_path)).replace('\\', '/')
                parts = rel_path.split('/')
                caller_service = None
                if parts[0] == "app" and len(parts) > 1:
                    caller_service = parts[1]

                if not caller_service:
                    continue

                try:
                    code_text = py_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                matches = url_pattern.findall(code_text)
                for host, port, endpoint in matches:
                    target_service = None
                    if host in known_services or any(s in host for s in known_services):
                        target_service = host
                    elif port in port_map:
                        target_service = port_map[port]
                    elif host in ["localhost", "127.0.0.1"] and port in port_map:
                        target_service = port_map[port]

                    if target_service and target_service != caller_service:
                        full_url = f"http://{host}" + (f":{port}" if port else "") + (endpoint if endpoint else "")
                        dependencies.append(
                            ServiceDependency(
                                caller=caller_service,
                                target=target_service,
                                type="http_call",
                                details=full_url,
                                source_file=rel_path
                            )
                        )

        return dependencies

    def analyze(self) -> DependencyGraphResult:
        discovered_services_map = self.discover_services()
        all_services: Set[str] = set(discovered_services_map.keys())

        docker_deps = self.analyze_docker_compose(all_services)
        code_deps = self.analyze_code_dependencies(all_services)

        all_deps = docker_deps + code_deps

        unique_deps = []
        seen = set()
        for dep in all_deps:
            key = (dep.caller, dep.target, dep.type, dep.details, dep.source_file)
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)

        graph: Dict[str, List[str]] = {s: [] for s in all_services}
        for dep in unique_deps:
            if dep.caller not in graph:
                graph[dep.caller] = []
            if dep.target not in graph[dep.caller]:
                graph[dep.caller].append(dep.target)
            if dep.target not in graph:
                graph[dep.target] = []

        return DependencyGraphResult(
            services=sorted(list(all_services)),
            dependencies=unique_deps,
            graph=graph
        )


def analyze_dependencies(root_dir: str = ".") -> Dict[str, Any]:
    analyzer = DependencyAnalyzer(root_dir=root_dir)
    return analyzer.analyze().to_dict()


def analyze_dependencies_to_json(root_dir: str = ".", indent: int = 2) -> str:
    analyzer = DependencyAnalyzer(root_dir=root_dir)
    return json.dumps(analyzer.analyze().to_dict(), indent=indent)


if __name__ == "__main__":
    root_path = sys.argv[1] if len(sys.argv) > 1 else "."
    print(analyze_dependencies_to_json(root_path))
