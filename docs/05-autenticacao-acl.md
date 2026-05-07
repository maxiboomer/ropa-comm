# RoPA-Comm — Autenticação e Controle de Acesso

## Visão geral

O sistema utiliza **OpenID Connect (OIDC)** para autenticação, integrado ao **Keycloak** como provedor de identidade. Para desenvolvimento, há um **mock Keycloak** embutido na própria aplicação Flask.

O controle de acesso é gerenciado pelo módulo **ACL** (Access Control List), que implementa RBAC (Role-Based Access Control) com suporte a escopos granulares.

---

## Fluxo de autenticação (Authorization Code Flow)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Fluxo Authorization Code (OIDC)                     │
└──────────────────────────────────────────────────────────────────────────┘

Usuário                  Flask App (app.py)           Keycloak / Mock KC
   │                           │                              │
   │  1. GET /listar           │                              │
   │──────────────────────────►│                              │
   │                           │ session['user'] ausente?     │
   │                           │ → redirect /login            │
   │◄──────────────────────────│                              │
   │                           │                              │
   │  2. GET /login            │                              │
   │──────────────────────────►│                              │
   │  (exibe tela de login)    │                              │
   │◄──────────────────────────│                              │
   │                           │                              │
   │  3. Clica "Entrar com     │                              │
   │     Keycloak"             │                              │
   │──────────────────────────►│                              │
   │                           │ GET /login/keycloak          │
   │                           │ Gera state + nonce           │
   │                           │ Redirect para KC /auth       │
   │◄──────────────────────────│                              │
   │                           │                              │
   │  4. Browser segue redirect│                              │
   │─────────────────────────────────────────────────────────►│
   │                           │                              │ Exibe
   │                           │                              │ tela de
   │◄─────────────────────────────────────────────────────────│ login KC
   │                           │                              │
   │  5. Insere credenciais    │                              │
   │─────────────────────────────────────────────────────────►│
   │                           │                              │ Valida
   │                           │                              │ usuário
   │                           │                              │
   │  6. Redirect para /auth/callback?code=XYZ&state=ABC      │
   │◄─────────────────────────────────────────────────────────│
   │                           │                              │
   │  7. GET /auth/callback    │                              │
   │  ?code=XYZ&state=ABC      │                              │
   │──────────────────────────►│                              │
   │                           │ POST /token (code=XYZ)       │
   │                           │─────────────────────────────►│
   │                           │                              │
   │                           │◄─────────────────────────────│
   │                           │ {access_token, id_token}     │
   │                           │                              │
   │                           │ GET /userinfo                │
   │                           │─────────────────────────────►│
   │                           │                              │
   │                           │◄─────────────────────────────│
   │                           │ {sub, name, email, roles}    │
   │                           │                              │
   │                           │ session['user'] = {          │
   │                           │   sub, name, email, roles    │
   │                           │ }                            │
   │                           │ redirect /                   │
   │◄──────────────────────────│                              │
   │                           │                              │
   │  8. GET /  (autenticado)  │                              │
   │──────────────────────────►│                              │
   │  Dashboard                │                              │
   │◄──────────────────────────│                              │
```

---

## Configuração do Keycloak

### Produção

```
Keycloak Server
└── Realm: ropa
    └── Client: ropa-web
        ├── Client Authentication: Confidential
        ├── Valid Redirect URIs: $ROPA_BASE_URL/auth/callback
        ├── Endpoints:
        │   ├── Authorization: $KEYCLOAK_URL/realms/ropa/protocol/openid-connect/auth
        │   ├── Token:         $KEYCLOAK_URL/realms/ropa/protocol/openid-connect/token
        │   ├── Userinfo:      $KEYCLOAK_URL/realms/ropa/protocol/openid-connect/userinfo
        │   └── JWKS:          $KEYCLOAK_URL/realms/ropa/protocol/openid-connect/certs
        └── Scopes: openid, profile, email
```

### Desenvolvimento (Mock)

Quando `KEYCLOAK_MOCK=1`, o Blueprint `keycloak_blueprint` é registrado na própria aplicação Flask e simula todos os endpoints do Keycloak.

```
Flask App (porta 5000)
├── /  (app principal)
└── /mock-kc/<realm>/protocol/openid-connect/
    ├── auth      → exibe formulário de login simulado
    ├── token     → troca código por JWT simulado
    ├── userinfo  → retorna dados do usuário de teste
    ├── certs     → retorna JWKS com chave local
    └── /.well-known/openid-configuration → discovery document
```

---

## Sessão do usuário

Após autenticação bem-sucedida, a sessão Flask armazena:

```python
session['user'] = {
    'sub': '12345',           # ID único do usuário no Keycloak
    'name': 'João Silva',     # Nome completo
    'email': 'joao@org.br',  # E-mail institucional
    'roles': ['editor']       # Papéis atribuídos no Keycloak
}
```

**Proteção de rotas:**
```python
@login_required  # verifica session['user'], redireciona para /login se ausente
def listar():
    user = session['user']
    ...
```

---

## Módulo ACL — Controle de acesso granular

### Arquitetura do módulo

```
┌─────────────────────────────────────────────────────────────┐
│  acl/                                                        │
│                                                              │
│  permissions.py                                              │
│  └── class Permission(Enum)                                  │
│      22 permissões atômicas                                  │
│                    │                                         │
│                    ▼                                         │
│  roles.py                                                    │
│  ├── class Role(Enum)  — 11 papéis                          │
│  └── ROLE_PERMISSIONS = {Role → [Permission, ...]}          │
│                    │                                         │
│                    ▼                                         │
│  scopes.py                                                   │
│  └── class ScopeType(Enum)                                   │
│      GLOBAL | UNIDADE | TIPO_OP | PROPRIO                   │
│                    │                                         │
│                    ▼                                         │
│  models.py                                                   │
│  ├── RoleRef (ORM — tabela roles)                            │
│  └── UserRoleAssignment (ORM — tabela user_role_assignments) │
│                    │                                         │
│                    ▼                                         │
│  service.py                                                  │
│  └── PermissionService                                       │
│      ├── has_permission(user_id, perm, scope, scope_id)     │
│      └── list_permissions(user_id)                           │
│                    │                                         │
│                    ▼                                         │
│  decorators.py                                               │
│  ├── @require_permission(Permission.X)                       │
│  └── @require_any_permission([Permission.X, Permission.Y])  │
│                    │                                         │
│                    ▼                                         │
│  seed.py                                                     │
│  └── sync_roles_to_db()  (flask acl-seed)                   │
└─────────────────────────────────────────────────────────────┘
```

---

### Permissões atômicas (22)

#### Grupo OPERACAO

| Permissão | Descrição |
|---|---|
| `OPERACAO_VER_PROPRIA` | Ver apenas atividades que o próprio usuário criou |
| `OPERACAO_VER_UNIDADE` | Ver atividades da sua unidade |
| `OPERACAO_VER_TODAS` | Ver todas as atividades |
| `OPERACAO_CRIAR` | Criar novas atividades |
| `OPERACAO_EDITAR_PROPRIA` | Editar atividades próprias |
| `OPERACAO_EDITAR_QUALQUER` | Editar qualquer atividade |
| `OPERACAO_EXCLUIR_PROPRIA` | Excluir atividades próprias |
| `OPERACAO_EXCLUIR_QUALQUER` | Excluir qualquer atividade |

#### Grupo AUDITORIA

| Permissão | Descrição |
|---|---|
| `AUDITORIA_VER_HISTORICO` | Ver histórico de alterações |
| `AUDITORIA_EXPORTAR` | Exportar dados |
| `AUDITORIA_VALIDAR` | Executar validação de conformidade |
| `AUDITORIA_VER_RELATORIOS` | Ver relatórios consolidados |

#### Grupo ADMIN

| Permissão | Descrição |
|---|---|
| `ADMIN_GERENCIAR_USUARIOS` | Gerenciar usuários |
| `ADMIN_GERENCIAR_PAPEIS` | Gerenciar papéis e permissões |
| `ADMIN_SEED_DADOS` | Inserir dados de exemplo |
| `ADMIN_IMPORTAR_DADOS` | Importar dados externos |
| `ADMIN_GERENCIAR_CONFIG` | Gerenciar configurações do sistema |

#### Grupo API

| Permissão | Descrição |
|---|---|
| `API_ACESSO_LEITURA` | Acesso à API de leitura |
| `API_ACESSO_ESCRITA` | Acesso à API de escrita |
| `API_ACESSO_ADMIN` | Acesso administrativo à API |

#### Outros

| Permissão | Descrição |
|---|---|
| `IMPORTAR_PIA` | Importar arquivos CNIL PIA |
| `ANONIMIZACAO` | Operações de anonimização |

---

### Matriz de papéis × permissões

| Papel | VER | CRIAR | EDITAR | EXCLUIR | AUDITORIA | ADMIN |
|---|---|---|---|---|---|---|
| VISUALIZADOR | Próprias | ✗ | ✗ | ✗ | ✗ | ✗ |
| VISUALIZADOR_UNIDADE | Unidade | ✗ | ✗ | ✗ | ✗ | ✗ |
| VISUALIZADOR_GLOBAL | Todas | ✗ | ✗ | ✗ | ✗ | ✗ |
| EDITOR | Próprias | ✓ | Próprias | Próprias | ✗ | ✗ |
| EDITOR_UNIDADE | Unidade | ✓ | Unidade | Próprias | ✗ | ✗ |
| EDITOR_GLOBAL | Todas | ✓ | Qualquer | Próprias | ✗ | ✗ |
| AUDITOR | Todas | ✗ | ✗ | ✗ | Completa | ✗ |
| IMPORTADOR | Próprias | ✓ | ✗ | ✗ | Exportar | Importar |
| GESTOR_USUARIOS | Todas | ✗ | ✗ | ✗ | Relatórios | Usuários/Papéis |
| ENCARREGADO | Todas | ✓ | Qualquer | Próprias | Completa | Parcial |
| ADMIN | Todas | ✓ | Qualquer | Qualquer | Completa | Completa |

---

### Lógica de verificação de escopo

```
has_permission(user_id=5, permission=OPERACAO_VER_UNIDADE, scope_type=UNIDADE, scope_id=3)

1. Busca todas as atribuições ativas de user_id=5
   (WHERE user_id=5 AND (expires_at IS NULL OR expires_at > now()))

2. Para cada atribuição, resolve as permissões do papel

3. Verifica se OPERACAO_VER_UNIDADE está na lista de permissões

4. Se scope_type=UNIDADE, verifica se scope_id=3 corresponde
   à unidade da atribuição

5. Retorna True se qualquer atribuição satisfaz os critérios
```

---

### Atribuição de papéis com escopo

```python
# Usuário 5 como EDITOR na Unidade 3 (sem expiração)
UserRoleAssignment(
    user_id=5,
    role_id=roles['EDITOR'].id,
    scope_type='UNIDADE',
    scope_id=3,
    created_by=1,
    expires_at=None
)

# Usuário 7 como AUDITOR global por 30 dias
UserRoleAssignment(
    user_id=7,
    role_id=roles['AUDITOR'].id,
    scope_type='GLOBAL',
    scope_id=None,
    created_by=1,
    expires_at=datetime.now() + timedelta(days=30)
)
```
