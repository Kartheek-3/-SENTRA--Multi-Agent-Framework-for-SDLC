from fastapi import FastAPI, APIRouter
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

app = FastAPI(title="TaskPulse API")
router = APIRouter()
Base = declarative_base()

class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}

@router.get("/api/v1/tasks")
def list_tasks():
    return [{"id": 1, "title": "Initial Task"}]

@router.post("/api/v1/tasks")
def create_task(title: str):
    return {"id": 2, "title": title}

app.include_router(router)
