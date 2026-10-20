from datetime import UTC, datetime, timedelta

import jwt

from vinichannels.domain.shared.ids import UserId

_ALGORITHM = "HS256"


class JwtSessionTokens:
    def __init__(self, secret: str, ttl: timedelta) -> None:
        self._secret = secret
        self._ttl = ttl

    def issue(self, user_id: UserId) -> str:
        now = datetime.now(UTC)
        payload = {"sub": user_id, "iat": now, "exp": now + self._ttl}
        return jwt.encode(payload, self._secret, algorithm=_ALGORITHM)

    def verify(self, token: str) -> UserId | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[_ALGORITHM])
        except jwt.PyJWTError:
            return None
        subject = payload.get("sub")
        return UserId(subject) if isinstance(subject, str) else None
