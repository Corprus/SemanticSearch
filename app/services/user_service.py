from uuid import UUID
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User, UserRole
from domain.interfaces.password_hasher import PasswordHasher
from services.exceptions import UserAlreadyExistsException, UserNotExistsException


class UserService:
    def __init__(self, session: Session, password_hasher: PasswordHasher):
        self._session = session
        self.password_hasher = password_hasher

    def create_user(self, login: str, password: str, role: UserRole) -> User:
        if self.find_user(login) is not None:
            raise UserAlreadyExistsException()
        pwd_hash = self.password_hasher.hash(password)
        user = User(
            login=login,
            password_hash=pwd_hash,
            role=role
        )
        self._session.add(user)
        self._session.flush()
        return user
    
    def delete_user(self, user_id: UUID) -> None:
        user = self.find_user_by_id(user_id)
        if user is None:
            raise UserNotExistsException()

        self._session.delete(user)
        self._session.flush()

    def find_user(self, login: str) -> User | None:
        query = select(User).where(User.login == login)
        return self._session.execute(query).scalars().first()

    def find_user_by_id(self, id: UUID) -> User | None:
        return self._session.get(User, str(id))   

    def list_users(self, role: Optional[UserRole] = None) -> Sequence[User]:
        query = select(User)
        if role is not None:
            query = query.where(User.role == role)

        return self._session.execute(query).scalars().all()