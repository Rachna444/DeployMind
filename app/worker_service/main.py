from typing import Any, Dict
from fastapi import FastAPI, Body

app = FastAPI(title="Worker Service", description="FastAPI Worker Service")


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
