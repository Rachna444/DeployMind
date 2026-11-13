from typing import Any, Dict
from fastapi import FastAPI, Body
import time
from prometheus_client import Counter, Histogram, make_asgi_app
from starlette.requests import Request

app = FastAPI(title="Worker Service", description="FastAPI Worker Service")
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



@app.get("/")
def read_root():
    return {"message": "Worker Service is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/process")
def process_task(task: Dict[str, Any] = Body(default_factory=dict)):
    task["status"] = "completed"
    return task
