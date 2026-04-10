"""Persona management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.models.persona_profile import PersonaProfile
from backend.schemas.persona import PersonaInfo, PersonaUpdate
from config.settings import get_settings

router = APIRouter(tags=["persona"])


@router.get("/personas")
async def list_personas() -> list[PersonaInfo]:
    settings = get_settings()
    profiles = PersonaProfile.list_all(settings.personas_dir)
    return [PersonaInfo(**p.model_dump()) for p in profiles]


@router.get("/personas/{persona_id}")
async def get_persona(persona_id: str) -> PersonaInfo:
    settings = get_settings()
    path = settings.personas_dir / f"{persona_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Persona not found")
    profile = PersonaProfile.load(path)
    return PersonaInfo(**profile.model_dump())


@router.put("/personas/{persona_id}")
async def update_persona(persona_id: str, update: PersonaUpdate) -> PersonaInfo:
    settings = get_settings()
    path = settings.personas_dir / f"{persona_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Persona not found")

    profile = PersonaProfile.load(path)

    # Apply updates
    update_data = update.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    profile.save(settings.personas_dir)
    return PersonaInfo(**profile.model_dump())


@router.delete("/personas/{persona_id}")
async def delete_persona(persona_id: str):
    settings = get_settings()
    path = settings.personas_dir / f"{persona_id}.json"
    if path.exists():
        path.unlink()
    return {"status": "deleted"}
