"""
Papéis (roles) do sistema.

Papéis são definidos em CÓDIGO (imutáveis entre deploys).
A ATRIBUIÇÃO de papel a usuário + escopo fica no BANCO (ver models.py).

Para adicionar um papel novo: crie a chave no enum Role e mapeie em
ROLE_PERMISSIONS abaixo. Rode o seed para criar/atualizar no banco.
"""

from enum import Enum
from acl.permissions import Permission


class Role(str, Enum):
    # Operacionais
    VISUALIZADOR = "visualizador"
    OPERADOR = "operador"
    OPERADOR_SENIOR = "operador_senior"

    # Aprovação / controle
    APROVADOR = "aprovador"
    GESTOR_UNIDADE = "gestor_unidade"

    # Auditoria / compliance
    AUDITOR = "auditor"
    COMPLIANCE = "compliance"

    # Administração
    ADMIN_FUNCIONAL = "admin_funcional"
    ADMIN_USUARIOS = "admin_usuarios"
    ADMIN_TECNICO = "admin_tecnico"

    # Integrações
    SERVICE_ACCOUNT = "service_account"

    def __str__(self) -> str:
        return self.value


# Mapeamento papel -> conjunto de permissões.
# Lido pelo seed e pelos decorators. ALTERE AQUI quando mudar escopo de um papel.
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.VISUALIZADOR: {
        Permission.OPERACAO_VISUALIZAR,
    },
    Role.OPERADOR: {
        Permission.OPERACAO_VISUALIZAR,
        Permission.OPERACAO_CRIAR,
        Permission.OPERACAO_EDITAR_PROPRIA,
        Permission.OPERACAO_SUBMETER,
    },
    Role.OPERADOR_SENIOR: {
        Permission.OPERACAO_VISUALIZAR,
        Permission.OPERACAO_CRIAR,
        Permission.OPERACAO_EDITAR_PROPRIA,
        Permission.OPERACAO_EDITAR_QUALQUER,
        Permission.OPERACAO_SUBMETER,
        Permission.OPERACAO_EXPORTAR,
    },
    Role.APROVADOR: {
        Permission.OPERACAO_VISUALIZAR,
        Permission.OPERACAO_APROVAR,
        Permission.OPERACAO_REJEITAR,
    },
    Role.GESTOR_UNIDADE: {
        Permission.OPERACAO_VISUALIZAR,
        Permission.OPERACAO_EDITAR_QUALQUER,
        Permission.OPERACAO_APROVAR,
        Permission.OPERACAO_REJEITAR,
        Permission.OPERACAO_CANCELAR,
        Permission.OPERACAO_EXPORTAR,
    },
    Role.AUDITOR: {
        Permission.OPERACAO_VISUALIZAR,
        Permission.OPERACAO_EXPORTAR,
        Permission.AUDITORIA_VISUALIZAR_LOGS,
        Permission.AUDITORIA_EXPORTAR,
    },
    Role.COMPLIANCE: {
        Permission.OPERACAO_VISUALIZAR,
        Permission.AUDITORIA_VISUALIZAR_LOGS,
        Permission.COMPLIANCE_RELATORIOS,
        Permission.COMPLIANCE_DADOS_PESSOAIS,
        Permission.COMPLIANCE_ATENDER_TITULAR,
    },
    Role.ADMIN_FUNCIONAL: {
        Permission.ADMIN_PARAMETROS,
        Permission.ADMIN_TIPOS_OPERACAO,
        Permission.ADMIN_FLUXOS_APROVACAO,
    },
    Role.ADMIN_USUARIOS: {
        Permission.ADMIN_USUARIOS_VISUALIZAR,
        Permission.ADMIN_USUARIOS_GERENCIAR,
        Permission.ADMIN_PAPEIS_ATRIBUIR,
    },
    Role.ADMIN_TECNICO: {
        Permission.ADMIN_INTEGRACOES,
        Permission.ADMIN_SISTEMA,
    },
    Role.SERVICE_ACCOUNT: {
        Permission.API_LEITURA,
        Permission.API_ESCRITA,
    },
}


def permissions_for(role: Role) -> set[Permission]:
    """Retorna as permissões de um papel."""
    return ROLE_PERMISSIONS.get(role, set())
