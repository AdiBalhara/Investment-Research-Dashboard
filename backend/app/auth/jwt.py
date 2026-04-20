from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError

from app.config import get_settings

settings = get_settings()


def create_access_token(user_id: UUID, org_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with user_id and org_id claims."""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES))
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        org_id = payload.get("org_id")
        if user_id is None or org_id is None:
            return None
        return {"user_id": user_id, "org_id": org_id}
    except JWTError:
        return None
