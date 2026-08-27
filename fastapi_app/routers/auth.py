from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from fastapi_app.dependencies import get_current_user
from fastapi_app.django_bootstrap import django  # noqa: F401
from fastapi_app.schemas import AuthResponse, LoginRequest, RegisterRequest, TokenResponse, UserPublic
from fastapi_app.security import create_access_token
from shared.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(user.id),
        user=UserPublic.model_validate(user),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    if User.objects.filter(username__iexact=payload.username).exists():
        raise HTTPException(status_code=409, detail="Username is already taken")
    if User.objects.filter(email__iexact=payload.email).exists():
        raise HTTPException(status_code=409, detail="Email is already registered")

    candidate = User(username=payload.username, email=payload.email.lower())
    try:
        validate_password(payload.password, user=candidate)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=list(exc.messages))

    try:
        user = User.objects.create_user(
            username=payload.username,
            email=payload.email.lower(),
            password=payload.password,
        )
    except IntegrityError:
        raise HTTPException(status_code=409, detail="User already exists")

    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    user = authenticate(username=payload.username, password=payload.password)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return _auth_response(user)


@router.post("/token", response_model=TokenResponse)
def token(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate(username=form.username, password=form.password)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return UserPublic.model_validate(user)
