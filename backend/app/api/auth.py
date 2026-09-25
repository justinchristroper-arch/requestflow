from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db, get_settings
from app.config import Settings
from app.core.security import DUMMY_HASH, create_access_token, verify_password
from app.models import User
from app.schemas.auth import LoginInput, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginInput, response: Response,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    user = db.scalar(select(User).where(User.email == str(payload.email)))
    valid = verify_password(payload.password.get_secret_value(), user.hashed_password if user else DUMMY_HASH)
    if not user or not valid or not user.is_active:
        raise HTTPException(401, "Invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    response.headers["Cache-Control"] = "no-store"
    return TokenResponse(
        access_token=create_access_token(user.id, settings),
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(response: Response, user: Annotated[User, Depends(get_current_active_user)]):
    response.headers["Cache-Control"] = "no-store"
    return UserResponse.model_validate(user)
