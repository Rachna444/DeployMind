# DeployMind 
### Pre-Deployment Risk Analysis for Microservices

DeployMind is a prototype designed to assess code-change risk before deployment. It analyzes changes and service dependencies, estimates blast radius, recommends validations, and produces a deployment recommendation.

## Key Features

- Code-change and dependency analysis
- Blast-radius estimation
- Risk scoring: `LOW`, `MEDIUM`, `HIGH`
- Rule-based validation recommendations
- API test, health-check, and load-test components
- Decision outcomes: `SAFE`, `CANARY`, `BLOCKED`
- Docker-based sample microservices

## Architecture

```text
Code Changes
     |
     v
Change & Dependency Analysis
     |
     v
Blast Radius → Risk Engine
     |
     v
Agent → Validations
     |
     v
Decision Engine
     |
     v
Deployment Recommendation
```

The sample application also demonstrates a Gateway → Task Service → Worker Service flow.

## Technology Stack

Python · FastAPI · Docker · Docker Compose · Pytest · Git/GitHub Actions configuration

## Quick Start

Start the sample microservices from the repository root:

```bash
docker compose up --build -d
docker compose ps
```

Open the API documentation: **http://localhost:8000/docs**

Run the pipeline sample:

```bash
python -m deploymind_core.pipeline.orchestrator
```

Run API validation tests:

```bash
python -m pytest validation/api_tests/test_runner.py -v
```

Stop the services:

```bash
docker compose down
```

## Documentation

- [Technical Documentation](technical_doc.md) — architecture, modules, execution, and implementation notes.
- [API Documentation](api_doc.md) — API usage, sample requests/responses, and observed output.
- [Product Requirements Document](prd.md) — product goals, requirements, acceptance criteria, and roadmap.

---

**Understand the change. Assess the risk. Make informed deployment decisions.**
