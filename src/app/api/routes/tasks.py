from fastapi import APIRouter, HTTPException, status

from src.app.schemas.voice import Task, TaskCreate, TaskReplace, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])
tasks: list[dict[str, object]] = []


@router.get("", response_model=list[Task])
def get_tasks() -> list[Task]:
    return [Task.model_validate(task) for task in tasks]


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    task_id = max((int(task["id"]) for task in tasks), default=0) + 1
    task = {"id": task_id, **payload.model_dump()}
    tasks.append(task)
    return Task.model_validate(task)


@router.put("/{task_id}", response_model=Task)
def replace_task(
    task_id: int,
    payload: TaskReplace,
) -> Task:
    task = _find_task(task_id)
    task.update(payload.model_dump())
    return Task.model_validate(task)


@router.patch("/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    payload: TaskUpdate,
) -> Task:
    task = _find_task(task_id)
    task.update(payload.model_dump(exclude_unset=True, exclude_none=True))
    return Task.model_validate(task)


@router.delete("/{task_id}")
def delete_task(task_id: int) -> dict[str, str]:
    task = _find_task(task_id)
    tasks.remove(task)
    return {"message": "Task deleted successfully"}


def _find_task(task_id: int) -> dict[str, object]:
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found",
    )
