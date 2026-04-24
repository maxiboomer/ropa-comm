"""
Permissões atômicas do sistema.

Cada permissão representa UMA ação concreta. Papéis agrupam permissões.
Nomenclatura: RECURSO_ACAO (ex: OPERACAO_APROVAR, USUARIO_EDITAR).
"""

from enum import Enum


class Permission(str, Enum):
    # --- Operações (registros) ---
    OPERACAO_VISUALIZAR = "operacao:visualizar"
    OPERACAO_CRIAR = "operacao:criar"
    OPERACAO_EDITAR_PROPRIA = "operacao:editar_propria"
    OPERACAO_EDITAR_QUALQUER = "operacao:editar_qualquer"
    OPERACAO_SUBMETER = "operacao:submeter"
    OPERACAO_APROVAR = "operacao:aprovar"
    OPERACAO_REJEITAR = "operacao:rejeitar"
    OPERACAO_CANCELAR = "operacao:cancelar"
    OPERACAO_EXPORTAR = "operacao:exportar"

    # --- Auditoria ---
    AUDITORIA_VISUALIZAR_LOGS = "auditoria:visualizar_logs"
    AUDITORIA_EXPORTAR = "auditoria:exportar"

    # --- Compliance / LGPD ---
    COMPLIANCE_RELATORIOS = "compliance:relatorios"
    COMPLIANCE_DADOS_PESSOAIS = "compliance:dados_pessoais"
    COMPLIANCE_ATENDER_TITULAR = "compliance:atender_titular"

    # --- Administração funcional ---
    ADMIN_PARAMETROS = "admin:parametros"
    ADMIN_TIPOS_OPERACAO = "admin:tipos_operacao"
    ADMIN_FLUXOS_APROVACAO = "admin:fluxos_aprovacao"

    # --- Administração de usuários / ACL ---
    ADMIN_USUARIOS_VISUALIZAR = "admin:usuarios:visualizar"
    ADMIN_USUARIOS_GERENCIAR = "admin:usuarios:gerenciar"
    ADMIN_PAPEIS_ATRIBUIR = "admin:papeis:atribuir"

    # --- Administração técnica ---
    ADMIN_INTEGRACOES = "admin:integracoes"
    ADMIN_SISTEMA = "admin:sistema"

    # --- API / integrações ---
    API_LEITURA = "api:leitura"
    API_ESCRITA = "api:escrita"

    def __str__(self) -> str:
        return self.value
