"""
Serviço de checagem de permissões.

Toda verificação passa por aqui. Não dispersar lógica de ACL pelos controllers.
"""

from typing import Optional
from datetime import datetime

from acl.permissions import Permission
from acl.roles import Role, permissions_for
from acl.scopes import ScopeType
from acl.models import UserRoleAssignment, RoleRef
from extensions import db


class PermissionService:

    @staticmethod
    def get_user_assignments(user_id: int) -> list[UserRoleAssignment]:
        """Retorna atribuições ativas (não expiradas) do usuário."""
        now = datetime.utcnow()
        return (
            db.session.query(UserRoleAssignment)
            .filter(UserRoleAssignment.user_id == user_id)
            .filter(
                (UserRoleAssignment.expires_at.is_(None))
                | (UserRoleAssignment.expires_at > now)
            )
            .all()
        )

    @staticmethod
    def has_permission(
        user_id: int,
        permission: Permission,
        scope_type: Optional[ScopeType] = None,
        scope_id: Optional[int] = None,
        owner_id: Optional[int] = None,
    ) -> bool:
        """
        Verifica se o usuário tem determinada permissão no escopo dado.

        Regras:
          - Atribuição GLOBAL cobre qualquer escopo.
          - Atribuição com escopo específico só vale se (scope_type, scope_id) baterem.
          - Escopo PROPRIO exige owner_id == user_id.
        """
        assignments = PermissionService.get_user_assignments(user_id)

        for assignment in assignments:
            role = _role_from_code(assignment.role.codigo)
            if role is None:
                continue

            if permission not in permissions_for(role):
                continue

            # GLOBAL cobre tudo
            if assignment.scope_type == ScopeType.GLOBAL.value:
                return True

            # Escopo PROPRIO: só se o dono do recurso for o próprio usuário
            if assignment.scope_type == ScopeType.PROPRIO.value:
                if owner_id is not None and owner_id == user_id:
                    return True
                continue

            # Escopo específico (unidade, tipo de operação, etc.)
            if (
                scope_type is not None
                and assignment.scope_type == scope_type.value
                and assignment.scope_id == scope_id
            ):
                return True

        return False

    @staticmethod
    def list_permissions(user_id: int) -> set[Permission]:
        """Útil para front-end: todas as permissões do usuário (sem escopo)."""
        perms: set[Permission] = set()
        for assignment in PermissionService.get_user_assignments(user_id):
            role = _role_from_code(assignment.role.codigo)
            if role is not None:
                perms |= permissions_for(role)
        return perms


def _role_from_code(codigo: str) -> Optional[Role]:
    try:
        return Role(codigo)
    except ValueError:
        return None
