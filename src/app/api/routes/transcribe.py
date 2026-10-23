from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from src.app.schemas.voice import InstructionPayload, InstructionRequest, TranscribeFlowResponse
from src.app.services.voice import execute_task_instruction, route_instruction, transcribe_audio

router = APIRouter(tags=["transcribe"])


@router.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/transcribe", response_model=TranscribeFlowResponse)
async def transcribe_and_run_flow(request: Request) -> TranscribeFlowResponse:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        audio_file = form.get("file")
        if not isinstance(audio_file, UploadFile):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A file field containing audio is required.",
            )

        audio = await audio_file.read()
        if not audio:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The uploaded audio file is empty.",
            )
        transcription = transcribe_audio(
            audio,
            audio_file.filename or "audio.webm",
            str(form.get("language") or "") or None,
        )
    elif content_type.startswith("application/json"):
        try:
            payload = InstructionRequest.model_validate(await request.json())
        except (ValueError, ValidationError) as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A valid transcription field is required.",
            ) from error
        transcription = payload.transcription
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Use multipart/form-data with an audio file or JSON with a transcription.",
        )

    instruction: InstructionPayload = route_instruction(transcription)
    result = execute_task_instruction(instruction)
    return TranscribeFlowResponse(
        transcription=transcription,
        instruction=instruction,
        result=result,
    )
