from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.auth.jwt import verify_token
from app.auth.models import User

security = HTTPBearer()


class CurrentUser:
    """Represents the authenticated user with their org context."""

    def __init__(self, user_id: UUID, org_id: UUID, email: str):
        self.user_id = user_id
        self.org_id = org_id
        self.email = email


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    FastAPI dependency that extracts and validates the JWT token
    from the Authorization header and returns the authenticated user.
    """
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = UUID(payload["user_id"])
    org_id = UUID(payload["org_id"])

    # Verify user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return CurrentUser(user_id=user.id, org_id=user.org_id, email=user.email)
