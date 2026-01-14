from app.domain.interfaces.password_hasher import PasswordHasher
from app.services.exceptions import InvalidCredentialsException
from app.services.user_service import UserService

class AuthService:
    """
    Сервис авторизации уже существующих пользователей
    """

    def __init__(self, user_service: UserService, password_hasher: PasswordHasher):
        self.password_hasher = password_hasher
        self.user_service = user_service
        
    def login(self, login: str, password: str) -> str:
        """
        Авторизует пользователя, возвращает токен авторизации в случае успеха
        """
        if not self.password_hasher.verify(password, pwd_hash):
            raise InvalidCredentialsException()
        ...

    def logout(self, login: str) -> None:
        """
        Разлогинивает пользователя пользователя
        """
        ...

