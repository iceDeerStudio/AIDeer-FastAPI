from app.models.task import TaskStatus, TaskFinish
from app.core.managers.task import TaskManager
from uuid import uuid4

class BaseTask:
    task_id: str

    def __init__(self) -> None:
        self.task_id = str(uuid4())

    async def run(self, *args, **kwargs):
        raise NotImplementedError
    
    async def on_status(self, status: TaskStatus):
        TaskManager.set_task(self.task_id, status)

    async def on_finish(self, task_finish: TaskFinish):
        TaskManager.set_task(self.task_id, TaskStatus.finished)

    