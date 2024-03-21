from fastapi import APIRouter, HTTPException, status
from sqlmodel import select, or_, and_
from app.models.preset import (
    Preset,
    PresetCreate,
    PresetRead,
    PresetVisibility,
    PresetParameters,
)
from app.models.server import ServerMessage
from app.api.deps import SessionDep, UserDep
from app.api.resps import ExceptionResponse
from app.core.managers.message import MessageStorage

router = APIRouter()


@router.get(
    "", response_model=list[PresetRead], responses=ExceptionResponse.get_responses(401)
)
async def list_presets(
    session: SessionDep, user: UserDep, offset: int = 0, limit: int = 10
):
    presets = session.exec(
        select(Preset)
        .where(
            or_(
                Preset.owner_id == user.id,
                Preset.visibility == PresetVisibility.public,
                and_(
                    user.permission >= 2, Preset.visibility == PresetVisibility.unlisted
                ),
            )
        )
        .offset(offset)
        .limit(limit)
    )
    return [
        {
            **preset.model_dump(exclude={"parameters"}),
            "messages": MessageStorage.get_messages(preset.id),
            "parameters": PresetParameters.model_validate_json(preset.parameters),
        }
        for preset in presets.all()
    ]


@router.post(
    "", response_model=PresetRead, responses=ExceptionResponse.get_responses(401, 403)
)
async def create_preset(session: SessionDep, user: UserDep, preset: PresetCreate):
    if preset.visibility == PresetVisibility.public and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot create public presets",
        )
    db_preset = Preset(
        **preset.model_dump(exclude={"parameters"}),
        parameters=preset.parameters.model_dump_json(),
        owner_id=user.id
    )
    session.add(db_preset)
    session.commit()
    session.refresh(db_preset)
    MessageStorage.set_messages(db_preset.id, preset.messages)
    return {
        **db_preset.model_dump(exclude={"parameters"}),
        "messages": MessageStorage.get_messages(db_preset.id),
        "parameters": PresetParameters.model_validate_json(db_preset.parameters),
    }


@router.get(
    "/{preset_id}",
    response_model=PresetRead,
    responses=ExceptionResponse.get_responses(401, 403, 404),
)
async def read_preset(preset_id: str, session: SessionDep, user: UserDep):
    preset = session.get(Preset, preset_id)
    if preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found"
        )
    if preset.owner_id != user.id and preset.visibility == PresetVisibility.private:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You do not have access to this preset",
        )
    return {
        **preset.model_dump(exclude={"parameters"}),
        "messages": MessageStorage.get_messages(preset.id),
        "parameters": PresetParameters.model_validate_json(preset.parameters),
    }


@router.put(
    "/{preset_id}",
    response_model=PresetRead,
    responses=ExceptionResponse.get_responses(401, 403, 404),
)
async def update_preset(
    preset_id: str, session: SessionDep, user: UserDep, preset: PresetCreate
):
    db_preset = session.get(Preset, preset_id)
    if db_preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found"
        )
    if db_preset.owner_id != user.id and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot update other users' presets",
        )
    if db_preset.visibility == PresetVisibility.public and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot update public presets",
        )
    if preset.visibility == PresetVisibility.public and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot set preset visibility to public",
        )
    db_preset.sqlmodel_update(preset.model_dump(exclude={"parameters"}))
    db_preset.parameters = preset.parameters.model_dump_json()
    session.commit()
    session.refresh(db_preset)
    MessageStorage.set_messages(db_preset.id, preset.messages)
    return {
        **db_preset.model_dump(exclude={"parameters"}),
        "messages": MessageStorage.get_messages(db_preset.id),
        "parameters": PresetParameters.model_validate_json(db_preset.parameters),
    }


@router.delete(
    "/{preset_id}",
    response_model=ServerMessage,
    responses=ExceptionResponse.get_responses(401, 403, 404),
)
async def delete_preset(preset_id: str, session: SessionDep, user: UserDep):
    db_preset = session.get(Preset, preset_id)
    if db_preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found"
        )
    if db_preset.owner_id != user.id and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot delete other users' presets",
        )
    if db_preset.visibility == PresetVisibility.public and user.permission < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: You cannot delete public presets",
        )
    session.delete(db_preset)
    session.commit()
    MessageStorage.delete_messages(preset_id)
    return {"message": "Preset deleted successfully"}
