"""
Docstring for __init__
Тут будут доменные сущности
"""
from .user import User, UserRole
from .document import Document
from .query import Query, QueryResultItem, QueryResults

__all__ = ["User", "UserRole", "Document", "Query", "QueryResultItem", "QueryResults"]