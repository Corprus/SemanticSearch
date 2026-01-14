# app/services/exceptions.py

class ServiceException(Exception):
    """Базовый класс для сервисных исключений"""

class InvalidCredentialsException(ServiceException):
    """
    Ошибка в пароле
    """
    ...

class UserAlreadyExistsException(ServiceException):
    """
    Уже существующий пользователь
    """
    ...

class UserNotExistsException(ServiceException):
    """
    Такого пользователя нет
    """
    ...