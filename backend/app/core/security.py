from datetime import datetime, timedelta, timezone
import secrets

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.config import Settings

password_hasher = PasswordHash.recommended()
# Unknown accounts still perform a password check to reduce timing differences.
DUMMY_HASH = password_hasher.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(password, hashed_password)
    except (UnknownHashError, ValueError):
        return False


def create_access_token(user_id: int, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now,
         "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
         "iss": "requestflow-api", "aud": "requestflow-web"},
        settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str, settings: Settings) -> int:
    claims = jwt.decode(
        token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm],
        issuer="requestflow-api", audience="requestflow-web",
        options={"require": ["sub", "exp", "iat", "iss", "aud"]},
    )
    subject = claims["sub"]
    if not isinstance(subject, str) or len(subject) > 10 or not subject.isascii() or not subject.isdigit():
        raise jwt.InvalidTokenError("Invalid subject")
    user_id = int(subject)
    if not 0 < user_id <= 2147483647:
        raise jwt.InvalidTokenError("Invalid subject")
    return user_id
