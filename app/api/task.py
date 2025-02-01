from fastapi import APIRouter
from app.models.models import TaskRequest
from app.services.task_service import execute_task

router = APIRouter()

@router.post("/execute-task")
async def execute_task_endpoint(task_request: TaskRequest):
    result = await execute_task(task_request.task, task_request.use_global_context)
    return result

@router.get("/current-page")
async def current_page():
    try:
        result = await execute_task("", False)
        return result
    except Exception as e:
        return {"message": str(e)}
