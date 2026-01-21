# app/services/exceptions.py

class ServiceException(Exception):
    """Базовый класс для сервисных исключений"""


class InvalidCredentialsException(ServiceException):
    """Ошибка в пароле или логине"""


class UserAlreadyExistsException(ServiceException):
    """Уже существующий пользователь"""


class UserNotExistsException(ServiceException):
    """Такого пользователя нет"""


class InsufficientBalanceException(ServiceException):
    """Недостаточно средств"""


class DocumentNotFoundException(ServiceException):
    """Документ не найден"""


class AccessDeniedException(ServiceException):
    """Нет доступа"""
