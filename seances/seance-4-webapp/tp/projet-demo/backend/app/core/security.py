import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
SALT_BYTES = 16
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    # Format auto-descriptif : algorithme$coût$sel$condensat
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, hash_hex = stored.split("$")
        salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(hash_hex)
        iterations = int(iterations)  # le coût vient de la chaîne stockée, pas de la constante
    except ValueError:
        return False  # condensat malformé (ex. "x") : refus, pas d'erreur 500
    if algorithm != ALGORITHM:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, iterations)
    return hmac.compare_digest(dk, expected)


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    # Liste explicite d'algorithmes ; exp est vérifiée par jwt.decode
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    return int(payload["sub"])
