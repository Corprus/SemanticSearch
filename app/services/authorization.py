from uuid import UUID
from infrastructure.auth import CurrentUser
from common.exceptions import AccessDeniedException
from common.models.user import UserRole

def resolve_target_user(current_user: CurrentUser, user_id: UUID | None = None) -> UUID:
    if user_id is None:
        return current_user.id
    if current_user.id == user_id:
        return user_id
    if current_user.role == UserRole.ADMIN:
        return user_id
    raise AccessDeniedException()

def is_admin(current_user: CurrentUser) -> bool:
    return  current_user.role == UserRole.ADMIN

def ensure_admin(current_user: CurrentUser) -> None:
    if not is_admin(current_user):
        raise AccessDeniedException()
    

