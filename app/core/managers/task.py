from app.core.connections.redis import redis_client
from app.models.task import Task, TaskStatus
from fastapi import HTTPException, status


class TaskManager:

    @staticmethod
    def get_task(task_id: str) -> Task:
        status_str = redis_client.get(f"task_{task_id}")
        if status_str is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )
        task_status = TaskStatus(status_str)
        return Task(task_id=task_id, status=task_status)

    @staticmethod
    def set_task(task_id: str, status: TaskStatus) -> None:
        redis_client.set(f"task_{task_id}", status.value)
        redis_client.expire(f"task_{task_id}", 3600)
        return None

    @staticmethod
    def delete_task(task_id: str) -> None:
        redis_client.delete(f"task_{task_id}")
        return None
