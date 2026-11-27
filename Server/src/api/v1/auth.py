from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.config import Settings
from src.core.security import create_access_token, decode_access_token
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from src.services.auth import (
    DuplicateEmailError,
    InvalidCredentialsError,
    RefreshSession,
    create_refresh_session,
    get_current_user,
    login_user,
    register_user,
    revoke_refresh_session,
    rotate_refresh_session,
)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_auth = HTTPBearer(auto_error=False)
REFRESH_COOKIE_NAME = "manualist_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _session_response(
    response: Response, session: RefreshSession, settings: Settings, secret_key: str
) -> LoginResponse:
    access_token = create_access_token(
        session.user_id, secret_key, settings.access_token_ttl_minutes
    )
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=session.token,
        expires=session.expires_at,
        path=REFRESH_COOKIE_PATH,
        secure=settings.app_env == "production",
        httponly=True,
        samesite="lax",
    )
    return LoginResponse(access_token=access_token)


def _error(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": {},
                "request_id": request.state.request_id,
            }
        },
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterResponse,
    responses={
        409: {"description": "Email already registered"},
        503: {"description": "Database not configured"},
    },
)
async def register(
    payload: RegisterRequest, request: Request
) -> RegisterResponse | JSONResponse:
    engine = cast(AsyncEngine | None, request.app.state.db_engine)
    if engine is None:
        return _error(request, 503, "DATABASE_UNAVAILABLE", "Database not configured")

    try:
        return await register_user(engine, payload.email, payload.password)
    except DuplicateEmailError:
        return _error(
            request, 409, "EMAIL_ALREADY_REGISTERED", "Email already registered"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"description": "Invalid email or password"}},
)
async def login(
    payload: LoginRequest, request: Request, response: Response
) -> LoginResponse | JSONResponse:
    engine = cast(AsyncEngine | None, request.app.state.db_engine)
    settings = cast(Settings, request.app.state.settings)
    secret_key = settings.secret_key
    if engine is None or secret_key is None:
        return _error(request, 503, "AUTH_UNAVAILABLE", "Login is unavailable")

    dummy_hash = cast(str, request.app.state.dummy_password_hash)
    try:
        user_id = await login_user(engine, payload.email, payload.password, dummy_hash)
    except InvalidCredentialsError:
        return _error(request, 401, "INVALID_CREDENTIALS", "Invalid email or password")

    session = await create_refresh_session(
        engine, user_id, settings.refresh_token_ttl_days
    )
    return _session_response(response, session, settings, secret_key.get_secret_value())


@router.post(
    "/refresh",
    response_model=LoginResponse,
    responses={
        401: {"description": "Missing or invalid refresh token"},
        503: {"description": "Authentication unavailable"},
    },
)
async def refresh(request: Request, response: Response) -> LoginResponse | JSONResponse:
    engine = cast(AsyncEngine | None, request.app.state.db_engine)
    settings = cast(Settings, request.app.state.settings)
    secret_key = settings.secret_key
    if engine is None or secret_key is None:
        return _error(request, 503, "AUTH_UNAVAILABLE", "Authentication is unavailable")

    token = request.cookies.get(REFRESH_COOKIE_NAME)
    try:
        if not token:
            raise InvalidCredentialsError
        session = await rotate_refresh_session(engine, token)
    except InvalidCredentialsError:
        return _error(
            request, 401, "INVALID_REFRESH_TOKEN", "Missing or invalid refresh token"
        )

    return _session_response(response, session, settings, secret_key.get_secret_value())


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={503: {"description": "Authentication unavailable"}},
)
async def logout(request: Request) -> Response:
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if token:
        engine = cast(AsyncEngine | None, request.app.state.db_engine)
        if engine is None:
            return _error(request, 503, "AUTH_UNAVAILABLE", "Logout is unavailable")
        await revoke_refresh_session(engine, token)

    settings = cast(Settings, request.app.state.settings)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        secure=settings.app_env == "production",
        httponly=True,
        samesite="lax",
    )
    return response


@router.get(
    "/me",
    response_model=RegisterResponse,
    responses={
        401: {"description": "Missing or invalid access token"},
        503: {"description": "Authentication unavailable"},
    },
)
async def me(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_auth)],
) -> RegisterResponse | JSONResponse:
    engine = cast(AsyncEngine | None, request.app.state.db_engine)
    settings = cast(Settings, request.app.state.settings)
    secret_key = settings.secret_key
    if engine is None or secret_key is None:
        return _error(request, 503, "AUTH_UNAVAILABLE", "Authentication is unavailable")

    try:
        if credentials is None:
            raise InvalidCredentialsError

        user_id = decode_access_token(
            credentials.credentials, secret_key.get_secret_value()
        )
        return await get_current_user(engine, user_id)
    except (InvalidTokenError, InvalidCredentialsError, ValueError):
        response = _error(
            request, 401, "INVALID_TOKEN", "Missing or invalid access token"
        )
        response.headers["WWW-Authenticate"] = "Bearer"
        return response
