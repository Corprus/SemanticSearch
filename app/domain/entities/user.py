# app/domain/entities/user.py
from decimal import Decimal
from enum import Enum
from uuid import UUID
from dataclasses import dataclass

"""
Перечисление возможных ролей пользователя
"""
class UserRole(str, Enum):    
    USER = "user"
    ADMIN = "admin"


"""
Класс пользователя
"""
@dataclass(frozen=True)
class User:
    id: UUID
    password_hash: str
    email: str
    name: str
    role: UserRole
    balance: Decimal