# app/domain/interfaces/password_hasher.py
from abc import ABC, abstractmethod

class PasswordHasher(ABC):
    """
    Docstring for app.infrastructure.password_hasher
    Абстракция для созданию хэшера для паролей
    """   
    @abstractmethod
    def hash(self, password: str) -> str:
        ...

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        ...