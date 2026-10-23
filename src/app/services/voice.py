import json
import re
from functools import lru_cache

from fastapi import HTTPException, status
from groq import Groq
from pydantic import ValidationError

from src.app.api.routes import tasks as task_routes
from src.app.core.config import get_settings
from src.app.schemas.voice import (
    InstructionPayload,
    TaskCreate,
    TaskReplace,
    TaskUpdate,
)


@lru_cache
def _get_groq_client() -> Groq:
    settings = get_settings()
    return Groq(
        api_key=settings.groq_api_key,
        timeout=settings.request_timeout_seconds,
    )


def route_instruction(transcription: str) -> InstructionPayload:
    current_tasks = [task.model_dump() for task in task_routes.get_tasks()]
    system_prompt = (
        "You route voice commands to a task-list API. Respond only with one JSON object "
        'containing exactly "endpoint", "method", and "params". Never include prose. '
        'Supported operations: GET /tasks with empty params; POST /tasks with title and '
        'optional done; PUT /tasks/{id} with title and done; PATCH /tasks/{id} with '
        'one or both of title and done; DELETE /tasks/{id} with empty params. Use a '
        "concrete integer ID in the endpoint for item operations. Use only the provided "
        "task IDs when referring to existing tasks. Do not invent IDs."
    )
    user_message = (
        f"Current tasks: {json.dumps(current_tasks, ensure_ascii=False)}\n"
        f"Transcription: {transcription}"
    )

    try:
        completion = _get_groq_client().chat.completions.create(
            model=get_settings().groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The instruction service could not be reached.",
        ) from error

    content = completion.choices[0].message.content
    try:
        instruction = InstructionPayload.model_validate_json(content or "")
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The instruction service returned an invalid response.",
        ) from error

    method = instruction.method.upper()
    is_collection = instruction.endpoint == "/tasks"
    is_item = re.fullmatch(r"/tasks/\d+", instruction.endpoint) is not None
    if not (
        (is_collection and method in {"GET", "POST"})
        or (is_item and method in {"PUT", "PATCH", "DELETE"})
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The instruction service returned an unsupported task operation.",
        )

    return instruction.model_copy(update={"method": method})


def transcribe_audio(
    audio: bytes,
    filename: str,
    language: str | None = None,
) -> str:
    settings = get_settings()
    options: dict[str, str] = {"model": settings.groq_transcription_model}
    if language:
        options["language"] = language

    try:
        result = _get_groq_client().audio.transcriptions.create(
            file=(filename, audio),
            response_format="json",
            **options,
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The audio transcription service could not be reached.",
        ) from error

    transcription = result.text.strip()
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No speech could be transcribed from the audio.",
        )
    return transcription


def execute_task_instruction(instruction: InstructionPayload):
    method = instruction.method.upper()
    params = instruction.params

    if instruction.endpoint == "/tasks" and method == "GET":
        return task_routes.get_tasks()
    if instruction.endpoint == "/tasks" and method == "POST":
        return task_routes.create_task(TaskCreate.model_validate(params))

    match = re.fullmatch(r"/tasks/(\d+)", instruction.endpoint)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported task endpoint.",
        )

    task_id = int(match.group(1))
    try:
        if method == "PUT":
            return task_routes.replace_task(
                task_id,
                TaskReplace.model_validate(params),
            )
        if method == "PATCH":
            return task_routes.update_task(
                task_id,
                TaskUpdate.model_validate(params),
            )
        if method == "DELETE":
            return task_routes.delete_task(task_id)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The routed task parameters are invalid.",
        ) from error

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Unsupported task method.",
    )