from typing import Optional
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import httpx

app = FastAPI(title="API Gateway", description="FastAPI API Gateway")

TASK_SERVICE_URL = "http://task_service:8001"


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
