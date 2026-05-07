# RoPA-Comm — Banco de Dados e Armazenamento

## Visão geral do armazenamento

O sistema utiliza **SQLite 3** como único banco de dados, armazenado em um arquivo único (`ropa.db`). Não há dependência de servidor de banco de dados externo.

```
┌──────────────────────────────────────────────────────────┐
│  ropa.db  (SQLite — arquivo único)                       │
│                                                          │
│  Tabelas de dados RoPA:                                  │
│  ├── atividades       (registros de tratamento)         │
│  └── historico        (auditoria de alterações)         │
│                                                          │
│  Tabelas do módulo ACL:                                  │
│  ├── roles            (papéis disponíveis)              │
│  └── user_role_assignments  (atribuições usuário→papel) │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  mock_kc_codes.db  (SQLite separado — dev only)          │
│  └── authorization_codes  (códigos temporários OIDC)    │
└──────────────────────────────────────────────────────────┘
```

---

## Esquema completo

### Tabela: `atividades`

Tabela principal do sistema. Cada linha representa uma atividade de tratamento de dados pessoais conforme Art. 37 LGPD.

```sql
CREATE TABLE atividades (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_atividade        TEXT NOT NULL,
    finalidade            TEXT,        -- Art. 37, II — por que os dados são tratados
    base_legal            TEXT,        -- Art. 7 LGPD — fundamento legal do tratamento
    categorias_titulares  TEXT,        -- Art. 37, III — quem são os titulares
    categorias_dados      TEXT,        -- Art. 37, IV — quais dados são tratados
    dados_sensiveis       INTEGER DEFAULT 0,  -- Boolean: 1 = contém dados sensíveis (Art. 11)
    destinatarios         TEXT,        -- Art. 37, V — com quem os dados são compartilhados
    transferencia_inter   TEXT,        -- Art. 37, VII — transferência internacional?
    prazo_retencao        TEXT,        -- Art. 37, VI — por quanto tempo são mantidos
    medidas_seguranca     TEXT,        -- Art. 46 — controles técnicos e organizacionais
    unidade_controladora  TEXT,        -- Qual unidade é responsável
    sistema_sei           TEXT,        -- Referência no sistema SEI (governo brasileiro)
    observacoes           TEXT,
    criado_em             TEXT DEFAULT (datetime('now','localtime')),
    atualizado_em         TEXT DEFAULT (datetime('now','localtime')),
    ativo                 INTEGER DEFAULT 1  -- Soft delete: 0 = excluída logicamente
);
```

**Campos obrigatórios para conformidade Art. 37 (com peso na pontuação):**

| Campo | Peso | Base legal |
|---|---|---|
| `nome_atividade` | 15% | Identificação |
| `finalidade` | 15% | Art. 37, II |
| `base_legal` | 15% | Art. 37, II |
| `categorias_titulares` | 10% | Art. 37, III |
| `categorias_dados` | 10% | Art. 37, IV |
| `destinatarios` | 10% | Art. 37, V |
| `prazo_retencao` | 10% | Art. 37, VI |
| `medidas_seguranca` | 10% | Art. 46 |
| `unidade_controladora` | 5% | Gestão organizacional |

**Pontuação de completude:**
- 0–100 pontos (soma dos pesos dos campos preenchidos)
- Verde: ≥ 80 pontos
- Amarelo: 50–79 pontos
- Vermelho: < 50 pontos

---

### Tabela: `historico`

Trilha de auditoria de todas as alterações campo a campo.

```sql
CREATE TABLE historico (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    atividade_id   INTEGER,   -- FK para atividades.id
    campo          TEXT,      -- Nome do campo alterado
    valor_antigo   TEXT,      -- Valor anterior
    valor_novo     TEXT,      -- Valor novo
    alterado_em    TEXT DEFAULT (datetime('now','localtime'))
);
```

**Exemplo de registro:**

| id | atividade_id | campo | valor_antigo | valor_novo | alterado_em |
|---|---|---|---|---|---|
| 1 | 5 | base_legal | `Art. 7, IX` | `Art. 7, II` | 2024-03-15 14:32:00 |
| 2 | 5 | prazo_retencao | `` | `5 anos` | 2024-03-15 14:32:00 |

---

### Tabela: `roles` (módulo ACL)

Papéis disponíveis no sistema, populados pelo comando `flask acl-seed`.

```sql
CREATE TABLE roles (
    id        INTEGER PRIMARY KEY,
    codigo    STRING(50) UNIQUE,  -- Identificador do papel (ex: 'ADMIN', 'AUDITOR')
    nome      STRING(100),        -- Nome legível
    descricao STRING(255)         -- Descrição do papel
);
```

**Papéis predefinidos (seed):**

| codigo | nome |
|---|---|
| `VISUALIZADOR` | Visualizador |
| `VISUALIZADOR_UNIDADE` | Visualizador da Unidade |
| `VISUALIZADOR_GLOBAL` | Visualizador Global |
| `EDITOR` | Editor |
| `EDITOR_UNIDADE` | Editor da Unidade |
| `EDITOR_GLOBAL` | Editor Global |
| `AUDITOR` | Auditor |
| `IMPORTADOR` | Importador de Dados |
| `GESTOR_USUARIOS` | Gestor de Usuários |
| `ENCARREGADO` | Encarregado de Dados (DPO) |
| `ADMIN` | Administrador |

---

### Tabela: `user_role_assignments` (módulo ACL)

Atribuições de papéis a usuários, com suporte a escopo e validade.

```sql
CREATE TABLE user_role_assignments (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER,          -- ID do usuário (vem do Keycloak)
    role_id     INTEGER,          -- FK para roles.id
    scope_type  STRING(20),       -- GLOBAL | UNIDADE | TIPO_OP | PROPRIO
    scope_id    INTEGER,          -- NULL para escopo GLOBAL; ID da unidade/tipo para os demais
    created_at  DATETIME,
    created_by  INTEGER,          -- user_id de quem criou a atribuição
    expires_at  DATETIME          -- NULL = sem expiração
);
```

---

## Diagrama de relacionamentos (ER)

```
┌──────────────────────────────┐
│        atividades            │
│                              │
│  id         (PK)             │
│  nome_atividade              │
│  finalidade                  │
│  base_legal                  │
│  categorias_titulares        │
│  categorias_dados            │
│  dados_sensiveis             │
│  destinatarios               │
│  transferencia_inter         │
│  prazo_retencao              │
│  medidas_seguranca           │
│  unidade_controladora        │
│  sistema_sei                 │
│  observacoes                 │
│  criado_em                   │
│  atualizado_em               │
│  ativo                       │
└──────┬───────────────────────┘
       │ 1
       │
       │ N
┌──────▼───────────────────────┐
│         historico            │
│                              │
│  id           (PK)           │
│  atividade_id (FK)           │
│  campo                       │
│  valor_antigo                │
│  valor_novo                  │
│  alterado_em                 │
└──────────────────────────────┘

┌──────────────────────────────┐
│           roles              │
│                              │
│  id        (PK)              │
│  codigo    (UNIQUE)          │
│  nome                        │
│  descricao                   │
└──────┬───────────────────────┘
       │ 1
       │
       │ N
┌──────▼───────────────────────┐
│    user_role_assignments     │
│                              │
│  id         (PK)             │
│  user_id                     │
│  role_id    (FK)             │
│  scope_type                  │
│  scope_id                    │
│  created_at                  │
│  created_by                  │
│  expires_at                  │
└──────────────────────────────┘
```

---

## Arquivos de armazenamento

| Arquivo | Localização | Criado por | Conteúdo |
|---|---|---|---|
| `ropa.db` | `$ROPA_DB_PATH` ou `./ropa.db` | `app.py` na inicialização | Dados RoPA + ACL |
| `mock_kc_codes.db` | diretório atual | `keycloak_blueprint.py` | Códigos OIDC temporários |
| `exports/` | `$ROPA_DATA_DIR/exports/` | Rotas de exportação | JSON, CSV, XLSX, PDF |
| `logs/` | `$ROPA_DATA_DIR/logs/` | Gunicorn | `gunicorn-access.log`, `gunicorn-error.log` |

---

## Ciclo de vida dos dados

### Criação de atividade
```
POST /novo → app.py → INSERT INTO atividades → SELECT last_insert_rowid()
```

### Edição de atividade
```
POST /editar/<id>
  → app.py compara campo a campo com registro atual
  → Para cada campo alterado: INSERT INTO historico
  → UPDATE atividades SET campo=novo, atualizado_em=now()
```

### Exclusão (soft delete)
```
POST /excluir/<id> → UPDATE atividades SET ativo=0
```
O registro permanece no banco e no histórico, mas não aparece nas listagens.

### Exportação
```
GET /exportar?formato=xlsx
  → SELECT * FROM atividades WHERE ativo=1
  → Gera arquivo em memória
  → Salva em $ROPA_DATA_DIR/exports/
  → Retorna como download
```
