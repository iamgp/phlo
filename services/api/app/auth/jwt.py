# jwt.py - JWT authentication utilities for the FastAPI application
# Handles password hashing, user authentication, JWT token creation/validation
# and Hasura GraphQL integration for role-based access control

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# --- Password Hashing ---
# CryptContext for secure password hashing using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- User Database ---
# Demo user store with hashed passwords (in production, use proper database)
# Hardcoded users (admin and analyst)
# Passwords: admin123 and analyst123
USERS = {
    "admin": {
        "user_id": "admin_001",
        "username": "admin",
        "email": "admin@cascade.local",
        "hashed_password": "$2b$12$hVzXLFlbMnbAN2Krtk88JOUxLWN6WGNxXASvb5fpzoN/tt/GGNriy",  # admin123
        "role": "admin",
    },
    "analyst": {
        "user_id": "analyst_001",
        "username": "analyst",
        "email": "analyst@cascade.local",
        "hashed_password": "$2b$12$rVI0z2.putUx/6/qRMbhZucUMhr7bI.6ykbyqwBOWMlV1eryipJci",  # analyst123
        "role": "analyst",
    },
}


# --- Authentication Functions ---
# Core functions for password verification and user authentication
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """Authenticate a user by username and password."""
    user = USERS.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


# --- JWT Token Functions ---
# Functions for creating and validating JWT access tokens
def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({"exp": expire})

    # Add Hasura-specific claims for GraphQL integration
    if "user_id" in data:
        to_encode["https://hasura.io/jwt/claims"] = {
            "x-hasura-allowed-roles": [data.get("role", "analyst")],
            "x-hasura-default-role": data.get("role", "analyst"),
            "x-hasura-user-id": data["user_id"],
        }

    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
