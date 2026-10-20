from vinichannels.application.errors import PermissionDenied
from vinichannels.domain.identity.entities import Permission, User


def require(actor: User, permission: Permission) -> None:
    if not actor.can(permission):
        raise PermissionDenied("Bạn không có quyền thực hiện thao tác này")
