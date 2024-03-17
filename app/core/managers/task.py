from app.core.connections.redis import redis_client
from app.models.task import Task, TaskStatus
from fastapi import HTTPException


class TaskManager:

    @staticmethod
    def get_task(task_id: str) -> Task:
        status_str = redis_client.hget("tasks", task_id)
        if status_str is None:
            raise HTTPException(status_code=422, detail=f"Task {task_id} not found")
        task_status = TaskStatus(status_str)
        return Task(task_id=task_id, status=task_status)

    @staticmethod
    def set_task(task_id: str, status: TaskStatus) -> None:
        redis_client.hset("tasks", task_id, status.value)
        return None

    @staticmethod
    def delete_task(task_id: str) -> None:
        redis_client.hdel("tasks", task_id)
        return None
