import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
import httpx
import time
from prometheus_client import Counter, Histogram, make_asgi_app
from starlette.requests import Request

app = FastAPI(title="Task Service", description="FastAPI Task Service")

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# In-memory database for storing tasks
tasks_db: Dict[str, dict] = {}
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path.rstrip("/") == "/metrics":
        return await call_next(request)

    start_time = time.perf_counter()
    response = await call_next(request)

    endpoint = request.scope.get("route")
    endpoint = endpoint.path if endpoint else request.url.path

    REQUEST_COUNT.labels(
        request.method, endpoint, str(response.status_code)
    ).inc()

    REQUEST_LATENCY.labels(
        request.method, endpoint
    ).observe(time.perf_counter() - start_time)

    return response

app.mount("/metrics", make_asgi_app())


class TaskCreate(BaseModel):
    title: Optional[str] = "Untitled Task"
    payload: Optional[dict] = Field(default_factory=dict)


@app.get("/")
def read_root():
    return {"message": "Task Service is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/tasks", status_code=201)
def create_task(task_input: Optional[TaskCreate] = Body(default=None)):
    task_id = str(uuid.uuid4())
    title = task_input.title if task_input and task_input.title else "Untitled Task"
    payload = task_input.payload if task_input and task_input.payload else {}

    task_data = {
        "id": task_id,
        "task_id": task_id,
        "title": title,
        "status": "pending",
        "payload": payload,
    }
    tasks_db[task_id] = task_data
    return task_data


@app.get("/tasks")
def list_tasks():
    return list(tasks_db.values())


@app.post("/tasks/{task_id}/process")
async def process_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_db[task_id]
    worker_url = "http://worker_service:8002/process"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(worker_url, json=task, timeout=10.0)
            if response.is_success:
                task["status"] = "completed"

            try:
                worker_response = response.json()
            except Exception:
                worker_response = response.text

            return {
                "message": "Task sent for processing",
                "task": task,
                "worker_status_code": response.status_code,
                "worker_response": worker_response,
            }
        except httpx.RequestError as exc:
            return {
                "message": "Failed to connect to worker service at http://worker_service:8002/process",
                "task": task,
                "error": str(exc),
            }
