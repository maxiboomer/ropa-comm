"""
Testes de exemplo para o módulo ACL.

Rode com: pytest acl/tests.py
"""

from acl.roles import Role, permissions_for, ROLE_PERMISSIONS
from acl.permissions import Permission


def test_todos_papeis_tem_permissoes():
    """Nenhum papel pode ficar sem permissão (provavelmente um bug)."""
    for role in Role:
        assert len(permissions_for(role)) > 0, f"Papel {role} sem permissões"


def test_operador_nao_aprova():
    """Segregação de funções: operador não deve aprovar."""
    assert Permission.OPERACAO_APROVAR not in permissions_for(Role.OPERADOR)


def test_admin_usuarios_nao_opera():
    """Admin de usuários não deve ter acesso operacional."""
    perms = permissions_for(Role.ADMIN_USUARIOS)
    assert Permission.OPERACAO_CRIAR not in perms
    assert Permission.OPERACAO_APROVAR not in perms


def test_auditor_nao_edita():
    """Auditor é read-only."""
    perms = permissions_for(Role.AUDITOR)
    assert Permission.OPERACAO_EDITAR_QUALQUER not in perms
    assert Permission.OPERACAO_CRIAR not in perms
    assert Permission.AUDITORIA_VISUALIZAR_LOGS in perms


def test_todas_permissoes_mapeadas():
    """Sanidade: toda permissão do enum deveria ser usada por algum papel."""
    usadas = set()
    for perms in ROLE_PERMISSIONS.values():
        usadas |= perms
    nao_usadas = set(Permission) - usadas
    assert not nao_usadas, f"Permissões órfãs: {nao_usadas}"
