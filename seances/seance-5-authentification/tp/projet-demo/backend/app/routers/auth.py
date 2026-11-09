from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthServiceDep, CurrentUser
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import TokenRead, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, service: AuthServiceDep) -> User:
    return service.register(
        email=payload.email, password=payload.password, display_name=payload.display_name
    )


# Formulaire OAuth2 : le champ username porte l'email
@router.post("/login", response_model=TokenRead)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], service: AuthServiceDep) -> TokenRead:
    user = service.authenticate(email=form.username, password=form.password)
    if user is None:
        # Même message pour un email inconnu et un mauvais mot de passe
        raise HTTPException(
            status_code=401,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenRead(
        access_token=create_access_token(user.id),
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> User:
    return current_user
