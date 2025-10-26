"""Routes for user registration and trait retrieval."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from ..db.mongo import get_collection
from ..models.user import CognitiveTraits, UserModel
from ..services import cognitive

router = APIRouter()


class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    cognitive_traits: CognitiveTraits | None = None


def _user_collection():
    return get_collection("users")


@router.post("/register", response_model=UserModel, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreateRequest,
    collection=Depends(_user_collection),
) -> UserModel:
    existing = await collection.find_one({"_id": user.email}) or await collection.find_one(
        {"email": user.email}
    )
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    traits = cognitive.derive_traits(
        user.cognitive_traits.model_dump() if user.cognitive_traits else None
    )
    user_record = UserModel(
        id=str(user.email),
        name=user.name,
        email=user.email,
        cognitive_traits=traits,
    )
    doc = user_record.model_dump()
    doc["_id"] = doc["id"]
    await collection.insert_one(doc)
    return user_record


@router.get("/{user_id}/traits", response_model=CognitiveTraits)
async def get_user_traits(user_id: str, collection=Depends(_user_collection)) -> CognitiveTraits:
    user_doc = await collection.find_one({"_id": user_id}) or await collection.find_one(
        {"email": user_id}
    )
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    traits_doc = user_doc.get("cognitive_traits") or {}
    return CognitiveTraits(**traits_doc)
