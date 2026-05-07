import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db

# auto_error=False lets us return a clean 401 instead of FastAPI's default 403
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """FastAPI dependency — resolves Bearer token to a User ORM instance."""
    from app.models.user import User  # local import avoids circular dependency

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise unauthorized

    if payload.get("type") != "access":
        raise unauthorized

    raw_id: str | None = payload.get("sub")
    if not raw_id:
        raise unauthorized

    try:
        user_uuid = uuid.UUID(raw_id)
    except ValueError:
        raise unauthorized

    user = db.get(User, user_uuid)
    if user is None:
        raise unauthorized

    return user
