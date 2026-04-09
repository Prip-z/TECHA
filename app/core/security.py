import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 120000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${password_hash}"


def verify_password(password: str, encoded_password: str) -> bool:
    try:
        scheme, iterations_raw, salt, expected_hash = encoded_password.split("$", 3)
    except ValueError:
        return False

    if scheme != PASSWORD_SCHEME:
        return False

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations_raw),
    ).hex()
    return hmac.compare_digest(password_hash, expected_hash)


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def create_access_token(subject: str, role: str) -> str:
    payload = {
        "sub": subject,
        "role": role,
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()),
        "jti": secrets.token_hex(8),
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(
        settings.auth_secret.encode("utf-8"),
        payload_json,
        hashlib.sha256,
    ).digest()
    return f"{_b64_encode(payload_json)}.{_b64_encode(signature)}"


def decode_access_token(token: str) -> dict[str, str | int]:
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        ) from exc

    payload_bytes = _b64_decode(payload_part)
    expected_signature = hmac.new(
        settings.auth_secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    provided_signature = _b64_decode(signature_part)

    if not hmac.compare_digest(expected_signature, provided_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
        )

    payload = json.loads(payload_bytes.decode("utf-8"))
    exp = int(payload["exp"])
    if datetime.now(timezone.utc).timestamp() >= exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    return payload
