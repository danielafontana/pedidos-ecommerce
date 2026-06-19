from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from order_service.infrastructure.config import settings

security = HTTPBearer(auto_error=False)

DEV_TOKEN_PAYLOAD = {
    "sub": "dev-user",
    "scope": "orders:read orders:write payments:read payments:write",
}


def create_dev_token() -> str:
    return jwt.encode(DEV_TOKEN_PAYLOAD, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    if settings.app_env == "local" and credentials is None:
        return DEV_TOKEN_PAYLOAD
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        return jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def require_scopes(*required: str):
    def checker(payload: dict = Depends(verify_token)) -> dict:
        scopes = set(str(payload.get("scope", "")).split())
        if not all(s in scopes for s in required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return payload

    return checker
