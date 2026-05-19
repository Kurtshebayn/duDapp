import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.security.audit import log_failed_login, log_successful_login
from app.security.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

# Computed once at module import — used to flatten timing for nonexistent-user
# login attempts so that the response time is indistinguishable from a
# wrong-password attempt (R-5 / AD-9).
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password-for-timing-flatten", bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15 minutes")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(Usuario)
        .filter(
            (Usuario.email == body.identificador) | (Usuario.nombre == body.identificador)
        )
        .first()
    )

    # Always run bcrypt regardless of whether the user exists (R-5: timing flatten).
    # When the user does not exist we check against the dummy hash — same bcrypt cost,
    # different comparand, always fails.
    hashed = user.password_hash if user else _DUMMY_HASH
    password_ok = verify_password(body.password, hashed)

    if not user or not password_ok:
        client_ip = request.client.host if request.client else "unknown"
        log_failed_login(body.identificador, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    client_ip = request.client.host if request.client else "unknown"
    log_successful_login(user.id, client_ip)
    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "name": user.nombre,
    })
    return TokenResponse(access_token=token)
