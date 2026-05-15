from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import create_user, get_user_by_username
from app.schemas.auth import TokenResponse, UserCreate, UserRead


def register_user(db: Session, payload: UserCreate) -> UserRead:
    existing = get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    user = create_user(
        db,
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role.value,
    )
    return UserRead.model_validate(user)


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return user


def create_login_response(user: User) -> TokenResponse:
    token = create_access_token(subject=user.username, role=user.role.value)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


ROLE_RANK = {
    UserRole.VIEWER: 1,
    UserRole.EDITOR: 2,
    UserRole.ADMIN: 3,
}


def ensure_role(user: User, minimum_role: UserRole) -> None:
    if ROLE_RANK[user.role] < ROLE_RANK[minimum_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{minimum_role.value}' required",
        )
