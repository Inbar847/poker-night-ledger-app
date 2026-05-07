import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


_SEARCH_MIN_LEN = 2
_SEARCH_MAX_RESULTS = 20


def search_users(db: Session, query: str, requester_id: uuid.UUID) -> list[User]:
    """
    Search users by full_name only (partial, case-insensitive).

    Rules:
    - Query must be at least 2 characters; shorter queries return an empty list
      to avoid expensive full-table scans.
    - The requesting user is excluded from results.
    - Email is never used as a search criterion and is never returned in results.
    - Results are capped at 20 rows ordered by full_name.
    - Only public-safe fields are needed — callers should map to UserSearchResult.
    """
    if len(query.strip()) < _SEARCH_MIN_LEN:
        return []

    pattern = f"%{query.strip()}%"

    return (
        db.query(User)
        .filter(
            User.id != requester_id,
            User.full_name.ilike(pattern),
        )
        .order_by(User.full_name)
        .limit(_SEARCH_MAX_RESULTS)
        .all()
    )


def get_public_profile(db: Session, user_id: uuid.UUID) -> User | None:
    """Return the User row for a public profile lookup, or None if not found."""
    return db.get(User, user_id)
