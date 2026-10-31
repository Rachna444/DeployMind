# TECHNICAL_DOC.md
# DeployMind — Pre-Deployment Risk Analysis for Microservices

## 1. Technical Overview

DeployMind is a prototype that evaluates code changes before deployment. It analyzes change metadata, examines service dependencies, estimates blast radius, calculates a risk score, recommends validations, and generates a deployment recommendation.

The repository contains a risk-analysis pipeline and a sample microservices application. Their complete automatic integration must be verified before describing the sample application as being controlled by the pipeline.

## 2. System Architecture

### Risk Analysis Pipeline

```text
Code Change
    |
    v
Change Analyzer
    |
    v
Dependency Analyzer
    |
    v
Blast Radius Analyzer
    |
    v
Risk Engine
    |
    v
Agent / Validation Recommendations
    |
    v
Validation Components
    |
    v
Decision Engine
    |
    v
Deployment Recommendation
```

### Sample Microservices

```text
Client
  |
  v
Gateway (:8000)
  |
  v
Task Service (:8001)
  |
  v
Worker Service (:8002)
```

## 3. Technology Stack

- **Language:** Python
- **API framework:** FastAPI
- **Containerization:** Docker and Docker Compose
- **Testing:** Pytest
- **Source control / CI configuration:** Git and GitHub Actions

Confirm exact dependency versions and runtime requirements from the current repository configuration.

## 4. Project Structure

```text
DeployMind/
├── app/
│   ├── gateway/
│   ├── task_service/
│   └── worker_service/
├── deploymind_core/
│   ├── change_analyzer/
│   ├── dependency_analyzer/
│   ├── blast_radius/
│   ├── risk_engine/
│   ├── agent/
│   ├── decision_engine/
│   └── pipeline/
├── validation/
│   ├── api_tests/
│   ├── load_tests/
│   └── health_checks/
├── monitoring/
├── .github/
│   └── workflows/
│       └── deploymind.yml
├── docker-compose.yml
├── README.md
├── TECHNICAL_DOC.md
├── API_DOC.md
└── PRD.md
```

## 5. Core Modules

### Change Analyzer
Identifies code changes and provides change metadata to downstream stages. Verify the Git diff source and behavior for empty or invalid input.

### Dependency Analyzer
Examines service relationships so the pipeline can reason about downstream impact.

### Blast Radius Analyzer
Estimates direct and indirect service impact. A sample pipeline result included `changed_service`, `directly_affected_services`, `indirectly_affected_services`, `dependency_chains`, and `total_affected_service_count`.

### Risk Engine
Calculates a score and risk level (`LOW`, `MEDIUM`, or `HIGH`) using configured rules. Previously inspected rules considered factors such as code churn, changed-file count, change types, service criticality, affected services, and dependency-chain depth. Confirm exact weights and thresholds in the current source code.

### Agent
Recommends validation checks using configured logic. The current implementation is described as rule-based; do not label it LLM-powered unless an actual model integration is implemented.

### Validation Components
The repository contains API testing, health-check, and load-testing modules. Their existence does not prove that every check executes against live services. Verify each runner's behavior and result provenance.

### Decision Engine
Produces a recommendation such as `SAFE`, `CANARY`, or `BLOCKED`, based on configured risk and validation rules. Exact thresholds and failure policies are implementation-dependent.

### Pipeline Orchestrator
Coordinates the pipeline stages and returns a consolidated result containing analysis, risk, validation, and decision information.

## 6. Local Execution

Start the sample services:

```bash
docker compose up --build -d
docker compose ps
```

Open the Gateway's interactive API docs:

```text
http://localhost:8000/docs
```

Run the pipeline sample:

```bash
python -m deploymind_core.pipeline.orchestrator
```

Run the Decision Engine sample:

```bash
python -m deploymind_core.decision_engine.engine
```

Run API validation tests:

```bash
python -m pytest validation/api_tests/test_runner.py -v
```

Stop the sample services:

```bash
docker compose down
```

## 7. Sample Pipeline Result

A sample orchestrator run reported `risk_score: 20`, `risk_level: LOW`, recommended `health_checks` and `api_tests`, both validation results as `PASS`, and `final_decision: SAFE`.

The same run reported an empty `changed_files` list. It therefore demonstrates that the orchestrator emitted a consolidated sample result, but it does not verify risk analysis for a real code change.

## 8. Reliability and Security Considerations

- Validate diff and service metadata before processing.
- Define behavior for missing dependency data and cyclic dependencies.
- Use timeouts and resource limits for validation commands.
- Ensure failed or missing required validations cannot silently count as passing.
- Record decision reasons and intermediate results for auditability.
- Do not use prototype recommendations as the sole production release control without review.

## 9. Verification Status

Initial functional verification has been completed for the main prototype components and the sample microservices flow.
- The pipeline orchestrator executed and produced a consolidated sample result.
- The sample microservices ran successfully with Docker Compose.
- Task creation and processing were demonstrated through the Gateway.
- The API test suite reported two passing tests in the recorded run.
- The Decision Engine produced a deployment recommendation for its sample input.
These checks demonstrate the current prototype's sample execution paths. End-to-end behavior with a real, non-empty Git diff and automated deployment integration are outside the scope of the recorded verification run.
