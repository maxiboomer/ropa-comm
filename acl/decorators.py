"""
Decorators para proteger rotas Flask.

Exemplos:

    @app.route("/operacoes", methods=["POST"])
    @require_permission(Permission.OPERACAO_CRIAR)
    def criar():
        ...

    @app.route("/operacoes/<int:op_id>/aprovar", methods=["POST"])
    @require_permission(
        Permission.OPERACAO_APROVAR,
        scope_resolver=lambda op_id: resolve_scope_from_operacao(op_id),
    )
    def aprovar(op_id):
        ...
"""

from functools import wraps
from typing import Callable, Optional
from flask import abort, g

from acl.permissions import Permission
from acl.scopes import ScopeType
from acl.service import PermissionService


def require_permission(
    permission: Permission,
    scope_resolver: Optional[Callable] = None,
):
    """
    Protege uma rota exigindo uma permissão.

    `scope_resolver` (opcional) é uma função que recebe os mesmos kwargs da rota
    e retorna um dict: {"scope_type": ScopeType, "scope_id": int, "owner_id": int}.
    Qualquer chave pode ser omitida.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if user is None:
                abort(401, description="Não autenticado")

            scope_data = {}
            if scope_resolver is not None:
                scope_data = scope_resolver(*args, **kwargs) or {}

            allowed = PermissionService.has_permission(
                user_id=user.id,
                permission=permission,
                scope_type=scope_data.get("scope_type"),
                scope_id=scope_data.get("scope_id"),
                owner_id=scope_data.get("owner_id"),
            )

            if not allowed:
                abort(403, description=f"Sem permissão: {permission}")

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: Permission):
    """Autoriza se o usuário tem QUALQUER uma das permissões (sem checagem de escopo)."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if user is None:
                abort(401)

            user_perms = PermissionService.list_permissions(user.id)
            if not any(p in user_perms for p in permissions):
                abort(403, description="Sem permissão")

            return fn(*args, **kwargs)
        return wrapper
    return decorator
