from domain.interfaces.password_hasher import PasswordHasher
from common.exceptions import InvalidCredentialsException
from services.user_service import UserService
from uuid import UUID
from app.infrastructure.jwt_handler import JwtHandler
class AuthService:
    """
    Сервис авторизации уже существующих пользователей
    """

    def __init__(self, user_service: UserService, password_hasher: PasswordHasher, jwt_handler: JwtHandler):
        self.password_hasher = password_hasher
        self.user_service = user_service
        self.jwt_handler = jwt_handler
    
    def login(self, login: str, password: str) -> str:
        """
        Авторизует пользователя, возвращает токен авторизации в случае успеха
        """
        user = self.user_service.find_user(login)
        if user is None:
            raise InvalidCredentialsException()

        if not self.password_hasher.verify(password, user.password_hash):
            raise InvalidCredentialsException()

        access_token = self.jwt_handler.create_access_token(UUID(user.id))
        return access_token

    def logout(self) -> None:
        """
        Разлогинивает текущего пользователя (заглушка, будет на фронте)
        """
        return None

