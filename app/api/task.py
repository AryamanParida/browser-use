from fastapi import APIRouter,HTTPException
from app.models.models import TaskRequest
from app.services.task_service import execute_task,get_current_page
router = APIRouter()

@router.post("/execute-task")
async def execute_task_endpoint(task_request: TaskRequest):
    try:
        result = await execute_task(task_request.task, task_request.use_global_context)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current-page")
async def current_page():
    try:
        result = await get_current_page()
        return result
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
