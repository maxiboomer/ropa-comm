"""
Módulo ACL - Controle de acesso baseado em papéis + escopo.

Uso rápido:
    from acl.decorators import require_permission
    from acl.permissions import Permission

    @app.route("/operacoes/<id>/aprovar", methods=["POST"])
    @require_permission(Permission.OPERACAO_APROVAR, scope_from="operacao")
    def aprovar(id): ...
"""

from acl.roles import Role
from acl.permissions import Permission
from acl.scopes import ScopeType

__all__ = ["Role", "Permission", "ScopeType"]
