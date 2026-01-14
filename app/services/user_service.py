from uuid import UUID
from app.domain.entities.user import User, UserRole
from app.domain.interfaces.password_hasher import PasswordHasher
from app.services.exceptions import UserAlreadyExistsException, UserNotExistsException


class UserService:
    def __init__(self, password_hasher: PasswordHasher):
        self.password_hasher = password_hasher

    def create_user(self, login: str, password: str, role: UserRole) -> User:
        if self.find_user(login) is not None:
            raise UserAlreadyExistsException()
        pwd_hash = self.password_hasher.hash(password)
        ...

    def delete_user(self, user_id: UUID) -> None:
        if self.find_user_by_id(user_id) is None:
            raise UserNotExistsException()
        ...

    def find_user(self, login) -> User:
        ...
    
    def find_user_by_id(self, id) -> User:
        ...        