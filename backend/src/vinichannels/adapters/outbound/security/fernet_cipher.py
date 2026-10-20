import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from vinichannels.application.errors import SecretUnreadable


class FernetSecretCipher:
    def __init__(self, secret_key: str) -> None:
        digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(digest))

    def encrypt(self, text: str) -> bytes:
        return self._fernet.encrypt(text.encode("utf-8"))

    def decrypt(self, data: bytes) -> str:
        try:
            return self._fernet.decrypt(data).decode("utf-8")
        except InvalidToken as error:
            raise SecretUnreadable(
                "Không giải mã được khóa đã lưu, hãy kiểm tra VINI_SECRET_KEY hoặc nhập lại"
            ) from error
