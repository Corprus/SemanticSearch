from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from jose import JWTError, jwt


class InvalidTokenError(Exception):
    """Token is invalid, expired, or cannot be verified."""


@dataclass(frozen=True)
class JwtConfig:
    secret_key: str
    algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60 * 24
    issuer: Optional[str] = None
    audience: Optional[str] = None


class JwtHandler:
    """
    Infrastructure component: create/verify JWT tokens.
    Does not depend on FastAPI and does not do DB lookups.
    """

    def __init__(self, config: JwtConfig) -> None:
        self._config = config

    def create_access_token(self, user_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=self._config.access_token_ttl_minutes)

        payload: Dict[str, Any] = {
            "sub": str(user_id),               # subject = user_id
            "iat": int(now.timestamp()),       # issued at
            "exp": int(exp.timestamp()),       # expires at
            "jti": str(uuid4()),               # token id (useful for future revocation)
            "type": "access",
        }

        if self._config.issuer:
            payload["iss"] = self._config.issuer
        if self._config.audience:
            payload["aud"] = self._config.audience

        token = jwt.encode(payload, self._config.secret_key, algorithm=self._config.algorithm)
        return token

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Returns decoded payload dict if token is valid.
        Raises InvalidTokenError otherwise.
        """
        try:
            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": False, 
                "verify_nbf": False,
                "require_exp": True,
                "require_sub": True,
            }

            decoded: Dict[str, Any] = jwt.decode(
                token,
                key=self._config.secret_key,
                algorithms=[self._config.algorithm],
                audience=self._config.audience,
                issuer=self._config.issuer,
                options=options,
            )

            # лёгкая семантическая проверка
            if decoded.get("type") != "access":
                raise InvalidTokenError("Not an access token")

            # sub должен быть UUID
            _ = UUID(decoded["sub"])

            return decoded

        except (JWTError, ValueError, KeyError) as e:
            raise InvalidTokenError("Invalid token") from e
