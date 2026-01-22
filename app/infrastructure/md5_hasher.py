# app/infrastructure/security/md5_hasher.py
import hashlib
from domain.interfaces.password_hasher import PasswordHasher

class Md5PasswordHasher(PasswordHasher):
    """
    Конкретная реализация класса хэшера (md5)
    """
    def hash(self, password: str) -> str:
        return hashlib.md5(password.encode("utf-8")).hexdigest()

    def verify(self, password: str, password_hash: str) -> bool:
        return self.hash(password) == password_hash
