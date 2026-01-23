from domain.interfaces.password_hasher import PasswordHasher
from services.exceptions import InvalidCredentialsException
from services.user_service import UserService
from uuid import UUID
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
        user = self.user_service.find_user(login)
        if user is None:
            raise InvalidCredentialsException()

        if not self.password_hasher.verify(password, user.password_hash):
            raise InvalidCredentialsException()

        # Пока что заглушка
        return f"token:{user.id}"

    def logout(self, user_id: UUID) -> None:
        """
        Разлогинивает пользователя
        """
        return None

