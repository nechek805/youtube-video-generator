from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.exceptions import EmailAlreadyRegistered, EmailNotConfirmed, EmailNotFound, PasswordNotValid
from src.core.database import get_db
from src.core.limiter import limiter
from src.auth.dependencies import get_current_user
from src.auth.service import AuthService
from src.user.schemas import UserLogin, UserCreate, UserRead
from src.logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
@limiter.limit("5/minute")
async def register(
    request: Request,
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuthService(db)
    try:
        await service.register_user(user)
    except EmailAlreadyRegistered:
        logger.warning("Registration attempt with already registered email: %s", user.email)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
    logger.info("New user registered: %s", user.email)
    return {"message": "Registered successfully. Now you need confirm your email and login."}


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    user: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = AuthService(db)
    try:
        session = await service.login_user(user)
    except EmailNotFound:
        logger.warning("Login failed — email not found: %s", user.email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    except PasswordNotValid:
        logger.warning("Login failed — wrong password for: %s", user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password not valid")
    except EmailNotConfirmed:
        logger.warning("Login failed — email not confirmed for: %s", user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not confirmed.")
    response.set_cookie(
        key="session_token",
        value=session.session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    logger.info("User logged in: %s", user.email)
    return {"message": "Logged in"}


@router.post("/logout")
async def logout(
    response: Response,
    session_token: str | None = Cookie(default=None),
    current_user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    service = AuthService(db)
    success = await service.logout_user(session_token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    response.delete_cookie("session_token")
    logger.info("User logged out: %s", current_user.email)
    return {"message": "Logout successfully"}


@router.get("/confirm-email")
@limiter.limit("10/minute")
async def confirm_email(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    success = await service.confirm_email(token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    logger.info("Email confirmed via token")
    return {"message": "Confirmed successfully"}
