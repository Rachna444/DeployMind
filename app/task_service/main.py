import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
import httpx

app = FastAPI(title="Task Service", description="FastAPI Task Service")

# In-memory database for storing tasks
tasks_db: Dict[str, dict] = {}


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
