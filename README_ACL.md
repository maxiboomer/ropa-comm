# Módulo ACL — Controle de Acesso

Controle de acesso baseado em **papéis + escopo**, com papéis definidos em código (enum) e atribuições persistidas no banco.

## Estrutura

```
acl/
├── __init__.py        # exports públicos
├── permissions.py     # enum Permission (ações atômicas)
├── roles.py           # enum Role + mapa Role -> Permissions
├── scopes.py          # tipos de escopo (global, unidade, próprio...)
├── models.py          # RoleRef e UserRoleAssignment (SQLAlchemy)
├── service.py         # PermissionService.has_permission(...)
├── decorators.py      # @require_permission para rotas Flask
├── seed.py            # sincroniza papéis do código para o banco
└── tests.py           # testes de sanidade das ACLs
```

## Como criar o branch

```bash
git checkout -b feature/acl-perfis
git add acl/
git commit -m "feat(acl): estrutura de papéis, permissões e escopo

- 11 papéis cobrindo operação, aprovação, auditoria, admin e integração
- permissões atômicas no enum Permission
- atribuição usuário x papel x escopo persistida no banco
- decorator @require_permission + PermissionService
- seed via 'flask acl-seed'
- testes de segregação de função"
```

## Integração no projeto

### 1. Ajustar o import do `db`

Em `models.py` e `service.py` o módulo importa `from extensions import db`. Ajuste para o caminho do seu projeto (ex: `from app import db`, `from app.extensions import db`, etc.).

### 2. Criar a migration

Com Flask-Migrate:

```bash
flask db migrate -m "add acl tables"
flask db upgrade
```

### 3. Popular os papéis

Em `app.py` (ou onde você cria o app Flask), registre o comando:

```python
from acl.seed import register_cli
register_cli(app)
```

E então:

```bash
flask acl-seed
```

### 4. Proteger rotas

```python
from acl.decorators import require_permission
from acl.permissions import Permission
from acl.scopes import ScopeType

@app.route("/operacoes", methods=["POST"])
@require_permission(Permission.OPERACAO_CRIAR)
def criar_operacao():
    ...

@app.route("/operacoes/<int:op_id>/aprovar", methods=["POST"])
@require_permission(
    Permission.OPERACAO_APROVAR,
    scope_resolver=lambda op_id: {
        "scope_type": ScopeType.UNIDADE,
        "scope_id": Operacao.query.get(op_id).unidade_id,
    },
)
def aprovar(op_id):
    ...
```

### 5. Disponibilizar `g.current_user`

Os decorators leem `g.current_user`. Garanta que o seu middleware de autenticação (Flask-Login, JWT, etc.) popule isso em cada request.

## Atribuindo papéis a usuários

```python
from acl.models import UserRoleAssignment, RoleRef
from acl.roles import Role
from acl.scopes import ScopeType

role = RoleRef.query.filter_by(codigo=Role.APROVADOR.value).first()
db.session.add(UserRoleAssignment(
    user_id=42,
    role_id=role.id,
    scope_type=ScopeType.UNIDADE.value,
    scope_id=3,
))
db.session.commit()
```

## Princípios de design

- **Papéis imutáveis, atribuições mutáveis.** Alterar o que um papel pode fazer é mudança de código (versionada, revisada). Quem tem cada papel é dado operacional.
- **Segregação de função.** `ADMIN_USUARIOS` não opera, `AUDITOR` não edita, `OPERADOR` não aprova. Os testes verificam isso.
- **Menor privilégio.** Usuário novo sem atribuições não vê nada. Vá adicionando.
- **Escopo é parte da checagem.** Não basta ter o papel, tem que estar no escopo certo.

## Próximos passos sugeridos

- [ ] Endpoint/tela para gestão de atribuições (só para `ADMIN_USUARIOS`)
- [ ] Log de auditoria para criação/remoção de atribuições
- [ ] Endpoint `/me/permissions` para o front esconder botões
- [ ] Cache das permissões por request (evita múltiplas queries)
