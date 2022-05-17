from datetime import datetime, timedelta
import time
from typing import Optional
from jose import JWTError, jwt
from pydantic import SecretStr

from opservatory.auth.exceptions import UnableToValidateToken
from opservatory.auth.models import User


def create_access_token(
    data: dict, secret_key: SecretStr, algorithm: str, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key.get_secret_value(), algorithm=algorithm)

    return encoded_jwt


def decode_payload(token: str, secret_key: SecretStr, algorithm: str) -> dict:
    try:
        payload = jwt.decode(token, secret_key.get_secret_value(), algorithms=[algorithm])
        return payload
    except JWTError:
        raise UnableToValidateToken()


def user_from_token(token: str, secret_key: SecretStr, algorithm: str) -> str:
    payload = decode_payload(token, secret_key, algorithm)
    print(payload)
    user = payload["user"].get("credentials", {}).get("username")
    if not user:
        UnableToValidateToken()
    return user


def verify_token(token: str, secret_key: SecretStr, algorithm: str, expiration: timedelta) -> bool:
    if token is None:
        return False

    try:
        token_data = decode_payload(token, secret_key, algorithm)

        if token_data["exp"] < int(time.time()) + expiration.total_seconds():
            return True

        return False

    except Exception:
        return False
