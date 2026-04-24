"""
Seed de papéis.

Sincroniza a tabela `roles` com o enum Role definido em código.
Rodar:
    flask --app app acl-seed
ou chamar seed_roles() diretamente.
"""

from acl.roles import Role
from acl.models import RoleRef
from extensions import db


ROLE_METADATA = {
    Role.VISUALIZADOR: ("Visualizador", "Acesso somente leitura aos registros."),
    Role.OPERADOR: ("Operador", "Cadastra e edita os próprios registros."),
    Role.OPERADOR_SENIOR: ("Operador Sênior", "Edita registros da equipe; não aprova."),
    Role.APROVADOR: ("Aprovador", "Aprova ou rejeita registros submetidos."),
    Role.GESTOR_UNIDADE: ("Gestor de Unidade", "Controle total dentro da unidade."),
    Role.AUDITOR: ("Auditor", "Leitura de tudo, incluindo logs e histórico."),
    Role.COMPLIANCE: ("Compliance / DPO", "Relatórios LGPD e atendimento de titulares."),
    Role.ADMIN_FUNCIONAL: ("Admin Funcional", "Parâmetros e fluxos do sistema."),
    Role.ADMIN_USUARIOS: ("Admin de Usuários", "Gestão de usuários e atribuição de papéis."),
    Role.ADMIN_TECNICO: ("Admin Técnico", "Integrações e parâmetros técnicos."),
    Role.SERVICE_ACCOUNT: ("Service Account", "Conta para integrações via API."),
}


def seed_roles() -> None:
    """Cria/atualiza papéis no banco. Idempotente."""
    for role, (nome, descricao) in ROLE_METADATA.items():
        existing = db.session.query(RoleRef).filter_by(codigo=role.value).first()
        if existing is None:
            db.session.add(RoleRef(codigo=role.value, nome=nome, descricao=descricao))
        else:
            existing.nome = nome
            existing.descricao = descricao
    db.session.commit()
    print(f"[acl] {len(ROLE_METADATA)} papéis sincronizados.")


def register_cli(app) -> None:
    """Registra o comando `flask acl-seed`."""
    @app.cli.command("acl-seed")
    def _seed():
        seed_roles()
