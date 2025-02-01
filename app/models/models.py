from pydantic import BaseModel

class TaskRequest(BaseModel):
    task: str
    use_global_context: bool
