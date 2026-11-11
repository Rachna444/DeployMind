from typing import Optional
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import httpx
import time
from prometheus_client import Counter, Histogram, make_asgi_app
from starlette.requests import Request

app = FastAPI(title="API Gateway", description="FastAPI API Gateway")

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

TASK_SERVICE_URL = "http://task_service:8001"
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


class TaskRequest(BaseModel):
    title: Optional[str] = None
    payload: Optional[dict] = None


@app.get("/")
def read_root():
    return {"message": "API Gateway is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/tasks")
async def create_task(task: TaskRequest):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(f"{TASK_SERVICE_URL}/tasks", json=task.model_dump(), timeout=10.0)
            return Response(
                content=res.content,
                status_code=res.status_code,
                media_type=res.headers.get("content-type", "application/json"),
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Task Service unavailable: {str(exc)}")


@app.get("/tasks")
async def list_tasks():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{TASK_SERVICE_URL}/tasks", timeout=10.0)
            return Response(
                content=res.content,
                status_code=res.status_code,
                media_type=res.headers.get("content-type", "application/json"),
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Task Service unavailable: {str(exc)}")


@app.post("/tasks/{task_id}/process")
async def process_task(task_id: str):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(f"{TASK_SERVICE_URL}/tasks/{task_id}/process", timeout=10.0)
            return Response(
                content=res.content,
                status_code=res.status_code,
                media_type=res.headers.get("content-type", "application/json"),
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Task Service unavailable: {str(exc)}")
