from fastapi import BackgroundTasks, APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.deps import UserDep, SessionDep
from app.api.resps import ExceptionResponse
from app.models.task import Task, TaskType, TaskCreate, TaskStatus
from app.models.server import ServerMessage
from app.models.chat import Chat
from app.core.stream import TaskStreaming
from app.core.managers.task import TaskManager
from app.core.tasks.chat_generation import ChatGenerationTask
from app.core.tasks.title_generation import TitleGenerationTask

router = APIRouter()


@router.post(
    "",
    response_model=Task,
    responses=ExceptionResponse.get_responses(401, 402, 403, 404),
)
async def create_task(
    user: UserDep,
    session: SessionDep,
    task: TaskCreate,
    background_tasks: BackgroundTasks,
):
    if user.credits_left <= 0 and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits: Please purchase more credits",
        )

    chat = session.get(Chat, task.chat_id)
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    if chat.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You do not have access to this chat",
        )

    if task.type == TaskType.chat_generation:
        background_task = ChatGenerationTask()
    elif task.type == TaskType.title_generation:
        background_task = TitleGenerationTask()

    background_tasks.add_task(background_task.run, task.chat_id)
    return Task(task_id=background_task.task_id, status=TaskStatus.pending)


@router.get(
    "/{task_id}", response_model=Task, responses=ExceptionResponse.get_responses(404)
)
async def read_task(task_id: str):
    task = TaskManager.get_task(task_id)
    return task


@router.delete(
    "/{task_id}",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(404, 422),
)
async def delete_task(task_id: str):
    task = TaskManager.get_task(task_id)
    if task.status != TaskStatus.finished and task.status != TaskStatus.failed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot delete task {task_id} with status {task.status.value}",
        )
    TaskManager.delete_task(task_id)
    return {"message": f"Task {task_id} deleted successfully"}


@router.get(
    "/{task_id}/stream",
    response_class=StreamingResponse,
    responses=ExceptionResponse.get_responses(422),
)
async def stream_task(task_id: str):
    task = TaskManager.get_task(task_id)
    if task.status != TaskStatus.failed:
        task_streaming = TaskStreaming(task_id)
        headers = {
            "Content-Type": "text/event-stream; charset=utf-8",
            "Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        return StreamingResponse(
            task_streaming.iterator(), headers=headers, status_code=200
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Task {task_id} failed",
        )
