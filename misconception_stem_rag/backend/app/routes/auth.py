"""Authentication routes for registration and login."""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

from ..config import get_settings
from ..db.mongo import get_collection
from ..models.user import CognitiveTraits, UserModel
from ..services import cognitive

router = APIRouter()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserModel


def _user_collection():
    return get_collection("users")


def verify_password(plain: str, hashed: str) -> bool:
    # Simple SHA256 hash comparison for now
    return hashlib.sha256(plain.encode()).hexdigest() == hashed


def get_password_hash(password: str) -> str:
    # Simple SHA256 hash for now (replace with bcrypt when container supports it)
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    collection=Depends(_user_collection),
) -> UserModel:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    logger.info(f"🔑 Validating token: {token[:20]}..." if token else "🔑 No token provided")
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str | None = payload.get("sub")
        logger.info(f"✅ Token decoded successfully, user_id: {user_id}")
        if user_id is None:
            logger.error("❌ Token payload missing 'sub' field")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"❌ JWT decode error: {type(e).__name__}: {e}")
        raise credentials_exception

    user_doc = await collection.find_one({"_id": user_id})
    if not user_doc:
        logger.error(f"❌ User not found in database: {user_id}")
        raise credentials_exception

    logger.info(f"✅ User authenticated: {user_doc.get('email')}")
    return UserModel(**user_doc)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    collection=Depends(_user_collection),
) -> TokenResponse:
    existing = await collection.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    traits = cognitive.derive_traits(None)
    user_record = UserModel(
        id=req.email,
        name=req.name,
        email=req.email,
        password_hash=get_password_hash(req.password),
        cognitive_traits=traits,
        onboarding_completed=False,
    )
    doc = user_record.model_dump(exclude={"password_hash"})
    doc["_id"] = doc["id"]
    doc["password_hash"] = user_record.password_hash
    await collection.insert_one(doc)

    settings = get_settings()
    access_token = create_access_token(
        data={"sub": user_record.id},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    # Return user without password_hash
    safe_user = UserModel(**{k: v for k, v in doc.items() if k != "password_hash"})
    return TokenResponse(access_token=access_token, user=safe_user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    collection=Depends(_user_collection),
) -> TokenResponse:
    user_doc = await collection.find_one({"email": form_data.username})
    if not user_doc or not verify_password(form_data.password, user_doc.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    access_token = create_access_token(
        data={"sub": user_doc["_id"]},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    safe_user = UserModel(**{k: v for k, v in user_doc.items() if k != "password_hash"})
    return TokenResponse(access_token=access_token, user=safe_user)


@router.get("/me", response_model=UserModel)
async def get_me(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    return current_user
