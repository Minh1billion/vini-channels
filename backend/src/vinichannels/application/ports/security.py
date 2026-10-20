from typing import Protocol

from vinichannels.domain.shared.ids import UserId


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class SessionTokens(Protocol):
    def issue(self, user_id: UserId) -> str: ...

    def verify(self, token: str) -> UserId | None: ...


class SecretCipher(Protocol):
    def encrypt(self, text: str) -> bytes: ...

    def decrypt(self, data: bytes) -> str: ...
