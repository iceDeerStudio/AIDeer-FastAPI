from fastapi import BackgroundTasks, APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.deps import UserDep
from app.models.task import Task, TaskCreate, TaskStatus
from app.core.stream import TaskStreaming
from app.core.managers.task import TaskManager
from app.core.clients.dashscope import ChatGeneration
from uuid import uuid4

router = APIRouter()


@router.post("", response_model=Task)
async def create_task(
    user: UserDep,
    task: TaskCreate,
    background_tasks: BackgroundTasks,
):
    if user.credits_left <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits: Please purchase more credits",
        )
    uuid = str(uuid4())
    TaskManager.set_task(uuid, TaskStatus.pending)
    textgen = ChatGeneration(user_id=user.id, task_id=uuid, chat_id=task.chat_id)
    background_tasks.add_task(textgen.start)
    return Task(task_id=uuid, status=TaskStatus.pending)


@router.get("/{task_id}", response_model=Task)
async def read_task(task_id: str):
    task = TaskManager.get_task(task_id)
    return task


@router.delete("/{task_id}", response_model=Task)
async def delete_task(task_id: str):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{task_id}/stream", response_class=StreamingResponse)
async def stream_task(task_id: str):
    task = TaskManager.get_task(task_id)
    if task.status != TaskStatus.failed:
        task_streaming = TaskStreaming(task_id)
        await task_streaming.start()
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        return StreamingResponse(
            task_streaming.iterator(), headers=headers, status_code=200
        )
    else:
        raise HTTPException(status_code=422, detail=f"Task {task_id} failed")
