# RoPA-Comm — Arquitetura de Módulos

## Mapa de módulos

```
ropa-comm/
│
├── app.py                      ← Controlador principal (Flask)
│   ├── importa keycloak_blueprint.py
│   ├── importa cnil_pia_importer.py
│   └── usa templates/ (Jinja2)
│
├── ropa.py                     ← Interface CLI
│   └── importa cnil_pia_importer.py
│
├── keycloak_blueprint.py       ← Mock OIDC (Blueprint Flask)
│   └── (sem dependências internas)
│
├── cnil_pia_importer.py        ← Importador CNIL PIA → LGPD
│   └── (sem dependências internas, usa sqlite3)
│
├── acl/                        ← Módulo de controle de acesso
│   ├── __init__.py             ← Exporta PermissionService, decoradores
│   ├── models.py               ← ORM SQLAlchemy (RoleRef, UserRoleAssignment)
│   ├── permissions.py          ← Enum: 22 permissões atômicas
│   ├── roles.py                ← Enum: 11 papéis + mapeamento permissões
│   ├── scopes.py               ← Enum: tipos de escopo (GLOBAL, UNIDADE…)
│   ├── service.py              ← PermissionService.has_permission()
│   ├── decorators.py           ← @require_permission, @require_any_permission
│   ├── seed.py                 ← Semente inicial dos papéis no banco
│   └── tests.py                ← Testes de sanidade do ACL
│
├── gunicorn_config.py          ← Configuração do servidor de produção
│
├── templates/                  ← Views Jinja2
│   ├── base.html               ← Layout base (sidebar, navbar, flash)
│   ├── login.html
│   ├── index.html              ← Dashboard com KPIs
│   ├── listar.html             ← Tabela de atividades
│   ├── ver.html                ← Detalhe + histórico
│   ├── form.html               ← Formulário criar/editar (multi-abas)
│   ├── validar.html            ← Relatório de conformidade
│   └── importar.html           ← Upload CNIL PIA
│
└── deploy/
    ├── install-macos.sh
    ├── ropa.app.plist.template
    └── ropa.tunnel.plist.template
```

---

## Diagrama de dependências

```
                    ┌─────────────┐
                    │   Browser   │
                    └──────┬──────┘
                           │ HTTP
                    ┌──────▼──────────────────────────────┐
                    │           app.py                    │
                    │  (Flask App — controlador central)  │
                    │                                     │
                    │  Registra Blueprint:                │
                    │  keycloak_blueprint                 │
                    │                                     │
                    │  Rotas:                             │
                    │  GET  /                             │
                    │  GET  /listar                       │
                    │  GET/POST /novo                     │
                    │  GET/POST /editar/<id>              │
                    │  GET  /ver/<id>                     │
                    │  GET  /exportar                     │
                    │  GET/POST /importar                 │
                    │  GET  /validar                      │
                    │  GET  /login                        │
                    │  GET  /auth/callback                │
                    │  GET  /logout                       │
                    └──────┬──────────────────────────────┘
                           │
           ┌───────────────┼────────────────┐
           │               │                │
    ┌──────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
    │ keycloak_   │  │   cnil_pia │  │ templates/ │
    │ blueprint   │  │ _importer  │  │  Jinja2    │
    │             │  │            │  │            │
    │ /mock-kc/   │  │ parse_cnil │  │ base.html  │
    │ authorize   │  │ _pia_json()│  │ form.html  │
    │ /token      │  │ importar() │  │ listar.html│
    │ /userinfo   │  │            │  │ ver.html   │
    │ /keys       │  └─────┬──────┘  └────────────┘
    │ /.well-known│        │
    └──────┬──────┘        │ sqlite3
           │               │
           │ sqlite3  ┌────▼────────┐
           └─────────►│  ropa.db   │
                      │  (SQLite)  │
                      └────────────┘

 acl/ (módulo independente, pendente de integração)
 ┌─────────────────────────────────────────────────┐
 │  permissions.py ──► roles.py ──► service.py     │
 │                               ──► decorators.py │
 │  models.py ──► seed.py                          │
 └─────────────────────────────────────────────────┘
```

---

## Módulo: app.py

**Responsabilidade:** Controlador central da aplicação Flask.

**Inicialização:**
1. Cria instância Flask
2. Configura OAuth via Authlib (Keycloak OIDC)
3. Registra Blueprint `keycloak_blueprint` (se `KEYCLOAK_MOCK=1`)
4. Inicializa banco SQLite (cria tabelas se não existirem)
5. Registra todas as rotas

**Rotas:**

| Método | Rota | Função |
|---|---|---|
| GET | `/` | Dashboard com KPIs (total, mês, conformidade) |
| GET | `/listar` | Tabela paginada de atividades |
| GET, POST | `/novo` | Formulário de criação |
| GET, POST | `/editar/<id>` | Formulário de edição |
| GET | `/ver/<id>` | Detalhe + histórico de alterações |
| GET | `/exportar` | Export em JSON, CSV, XLSX ou PDF |
| GET, POST | `/importar` | Upload de arquivo CNIL PIA |
| GET | `/validar` | Relatório de completude Art. 37 |
| GET | `/login` | Página de login |
| GET | `/login/keycloak` | Inicia fluxo OIDC (redirect para Keycloak) |
| GET | `/auth/callback` | Recebe código e troca por token |
| GET | `/logout` | Encerra sessão |
| POST | `/seed` | Insere 5 atividades de exemplo |

**Middleware:**
- `@login_required`: decorador que verifica `session['user']` antes de qualquer rota protegida

---

## Módulo: keycloak_blueprint.py

**Responsabilidade:** Servidor Keycloak simulado para desenvolvimento.

**Ativa-se quando:** `KEYCLOAK_MOCK=1` (variável de ambiente)

**Prefixo de rota:** `/mock-kc`

**Endpoints simulados:**

| Endpoint | Equivalente real |
|---|---|
| `GET /mock-kc/<realm>/protocol/openid-connect/auth` | Keycloak authorization endpoint |
| `POST /mock-kc/<realm>/protocol/openid-connect/token` | Keycloak token endpoint |
| `GET /mock-kc/<realm>/protocol/openid-connect/userinfo` | Userinfo endpoint |
| `GET /mock-kc/<realm>/protocol/openid-connect/certs` | JWKS endpoint |
| `GET /mock-kc/<realm>/.well-known/openid-configuration` | Discovery document |

**Usuários de teste:**

| Username | Senha | Papel simulado |
|---|---|---|
| `encarregado` | `123` | Encarregado de Dados (DPO) |
| `admin` | `123` | Administrador |
| `usuario` | `123` | Usuário comum |

**Persistência:** Códigos de autorização são armazenados em `mock_kc_codes.db` (SQLite separado), compartilhado entre workers do Gunicorn.

---

## Módulo: cnil_pia_importer.py

**Responsabilidade:** Converte assessments PIA no formato CNIL (GDPR francês) para atividades LGPD.

**Mapeamento de bases legais (GDPR → LGPD):**

| Base GDPR (CNIL) | Base LGPD |
|---|---|
| Consentimento | Art. 7, I |
| Obrigação legal | Art. 7, II |
| Interesse vital | Art. 7, VIII |
| Tarefa pública | Art. 7, III |
| Interesse legítimo | Art. 7, IX |
| Contrato | Art. 7, V |

**Estratégias de importação:**
- `pular`: ignora atividades com mesmo nome
- `mesclar`: atualiza apenas campos vazios
- `sobrescrever`: substitui todos os campos

---

## Módulo: acl/

**Status:** Implementado porém **pendente de integração** em `app.py`.

**Responsabilidade:** Controle de acesso baseado em papéis (RBAC) com escopo granular.

### permissions.py — Permissões atômicas (22 total)

| Grupo | Permissões |
|---|---|
| `OPERACAO_*` | VER_PROPRIA, VER_UNIDADE, VER_TODAS, CRIAR, EDITAR_PROPRIA, EDITAR_QUALQUER, EXCLUIR_PROPRIA, EXCLUIR_QUALQUER |
| `AUDITORIA_*` | VER_HISTORICO, EXPORTAR, VALIDAR, VER_RELATORIOS |
| `ADMIN_*` | GERENCIAR_USUARIOS, GERENCIAR_PAPEIS, SEED_DADOS, IMPORTAR_DADOS, GERENCIAR_CONFIG |
| `API_*` | ACESSO_API_LEITURA, ACESSO_API_ESCRITA, ACESSO_API_ADMIN |
| Outros | IMPORTAR_PIA, ANONIMIZACAO |

### roles.py — Papéis (11 total)

| Papel | Descrição |
|---|---|
| `VISUALIZADOR` | Lê apenas atividades próprias |
| `VISUALIZADOR_UNIDADE` | Lê atividades da unidade |
| `VISUALIZADOR_GLOBAL` | Lê todas as atividades |
| `EDITOR` | Cria e edita atividades próprias |
| `EDITOR_UNIDADE` | Cria e edita atividades da unidade |
| `EDITOR_GLOBAL` | Cria e edita qualquer atividade |
| `AUDITOR` | Acesso completo de leitura e relatórios |
| `IMPORTADOR` | Pode importar dados (PIA, seed) |
| `GESTOR_USUARIOS` | Gerencia usuários e papéis |
| `ENCARREGADO` | DPO — acesso amplo exceto admin técnico |
| `ADMIN` | Acesso total |

### scopes.py — Tipos de escopo

| Escopo | Descrição |
|---|---|
| `GLOBAL` | Aplica a toda a organização |
| `UNIDADE` | Aplica a uma unidade específica |
| `TIPO_OP` | Aplica a um tipo de operação |
| `PROPRIO` | Aplica apenas aos próprios registros |

### service.py — Lógica de verificação

```python
PermissionService.has_permission(
    user_id: int,
    permission: Permission,
    scope_type: ScopeType = GLOBAL,
    scope_id: int = None
) → bool
```

### decorators.py — Proteção de rotas

```python
@require_permission(Permission.OPERACAO_VER_TODAS)
def listar():
    ...

@require_any_permission([Permission.ADMIN_GERENCIAR_USUARIOS, Permission.ENCARREGADO])
def painel_admin():
    ...
```

---

## Módulo: ropa.py (CLI)

**Responsabilidade:** Interface de linha de comando para operações sem browser.

**Comandos disponíveis:**

| Comando | Descrição |
|---|---|
| `python ropa.py novo` | Cadastro interativo de atividade |
| `python ropa.py listar` | Lista todas as atividades em tabela |
| `python ropa.py ver <id>` | Exibe detalhes de uma atividade |
| `python ropa.py editar <id>` | Edita atividade interativamente |
| `python ropa.py validar` | Relatório de completude |
| `python ropa.py seed` | Insere 5 atividades de exemplo |
| `python ropa.py exportar [json\|csv\|xlsx]` | Exporta todos os registros |
| `python ropa.py relatorio` | Gera relatório PDF |
