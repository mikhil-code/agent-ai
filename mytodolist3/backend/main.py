from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Task(BaseModel):
    id: str
    text: str
    completed: bool

class TaskCreate(BaseModel):
    text: str

class TaskUpdate(BaseModel):
    completed: bool

# In-memory storage
tasks: List[Task] = []

@app.get("/tasks")
async def get_tasks():
    return tasks

@app.post("/task")
async def create_task(task: TaskCreate):
    new_task = Task(id=str(uuid.uuid4()), text=task.text, completed=False)
    tasks.append(new_task)
    return new_task

@app.put("/task/{task_id}")
async def update_task(task_id: str, task_update: TaskUpdate):
    for task in tasks:
        if task.id == task_id:
            task.completed = task_update.completed
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    for i, task in enumerate(tasks):
        if task.id == task_id:
            return tasks.pop(i)
    raise HTTPException(status_code=404, detail="Task not found")
