# API_DOC.md
# DeployMind — API Documentation

## 1. Scope

This document describes the demonstrated local API flow for the sample microservices and the observed output fields of the risk-analysis pipeline.

The exact registered HTTP routes and schemas should be confirmed in the running FastAPI OpenAPI documentation. The pipeline orchestrator is currently documented as a Python module entry point, not as a confirmed REST endpoint.

## 2. Local Services

| Service | Base URL | Purpose |
|---|---|---|
| Gateway | `http://localhost:8000` | API entry point |
| Task Service | `http://localhost:8001` | Task management |
| Worker Service | `http://localhost:8002` | Task processing |

**Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

## 3. Demonstrated Task Flow

### 3.1 Create a Task

Use the task-creation route shown in Swagger UI and submit a body like:

```json
{
  "title": "DeployMind Demo Task",
  "payload": {
    "demo": true
  }
}
```

**Observed:** A successful request returned `201 Created`, a generated task ID, and a pending task.

Example response shape (illustrative; verify exact property names in Swagger):

```json
{
  "id": "<generated-task-id>",
  "title": "DeployMind Demo Task",
  "payload": {
    "demo": true
  },
  "status": "pending"
}
```

### 3.2 Process a Task

The demonstrated route pattern is:

```http
POST /tasks/{task_id}/process
```

Replace `{task_id}` with the ID returned by task creation.

**Observed:** A successful processing request returned `200 OK` and indicated that the task had been processed.

### 3.3 List Tasks

The sample application includes task-listing functionality. Use the exact route and schema registered in Swagger rather than relying on an assumed path.

## 4. Pipeline Module

Run the pipeline sample locally:

```bash
python -m deploymind_core.pipeline.orchestrator
```

This is a local Python command, not a confirmed HTTP endpoint.

A sample result included:

| Field | Meaning |
|---|---|
| `changed_files` | Detected changed files |
| `affected_services` | Services considered affected |
| `blast_radius` | Direct and indirect impact details |
| `risk_score` | Numeric risk score |
| `risk_level` | `LOW`, `MEDIUM`, or `HIGH` |
| `recommended_validations` | Recommended validation names |
| `validation_results` | Reported validation outcomes |
| `final_decision` | `SAFE`, `CANARY`, or `BLOCKED` |
| `reason` | Human-readable decision explanation |
| `summary` | Aggregate result information |

These fields are based on an observed sample; confirm the current `models.py` definitions before treating them as a stable interface.

### Example Result Excerpt

```json
{
  "changed_files": [],
  "affected_services": [],
  "risk_score": 20,
  "risk_level": "LOW",
  "recommended_validations": [
    "health_checks",
    "api_tests"
  ],
  "validation_results": {
    "health_checks": "PASS",
    "api_tests": "PASS"
  },
  "final_decision": "SAFE"
}
```

This sample contained no changed files, so it does not demonstrate evaluation of a real code change.

## 5. Status Codes

The following were observed or are common for the demonstrated FastAPI flow; exact behavior depends on the endpoint implementation.

| Code | Meaning |
|---|---|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created |
| `404 Not Found` | Resource not found, if implemented |
| `422 Unprocessable Entity` | FastAPI request validation error may be returned |
| `500 Internal Server Error` | Unexpected server-side error |

## 6. Verify the API

```bash
docker compose up --build -d
docker compose ps
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs), create a task, copy its ID, and submit the processing request.

When finished:

```bash
docker compose down
```

## 7. Contract and Security Notes

- Treat Swagger/OpenAPI as the source of truth for current endpoint schemas.
- Handle non-2xx responses.
- Do not assume authentication, rate limiting, or production access controls exist unless confirmed in code.
- The sample task flow and risk pipeline are separate capabilities unless explicit integration is implemented and tested.
