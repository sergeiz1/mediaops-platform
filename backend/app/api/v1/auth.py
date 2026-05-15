from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.auth_deps import get_current_user
from app.core.database import get_db
from app.schemas.auth import TokenResponse, UserCreate, UserRead
from app.services.auth_service import authenticate_user, create_login_response, register_user

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserRead)
def register_endpoint(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    return register_user(db, payload)


@router.post("/login", response_model=TokenResponse)
def login_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(db, form_data.username, form_data.password)
    return create_login_response(user)


@router.get("/me", response_model=UserRead)
def me_endpoint(current_user=Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
