# RoPA-Comm — Topologia e Deployment

## Diagrama de topologia (produção macOS)

```
Internet
   │
   │  HTTPS (*.trycloudflare.com)
   ▼
┌─────────────────────┐
│  Cloudflare Tunnel  │  cloudflared daemon
│  (túnel público)    │  ropa.tunnel.plist.template
└────────┬────────────┘
         │ HTTP local
         ▼
┌─────────────────────────────────────────────────────────┐
│  macOS (servidor local)                                  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Gunicorn (processo Python)                      │   │
│  │  Bind: 127.0.0.1:8000                            │   │
│  │  Workers: min(4, CPU×2+1)                        │   │
│  │  Timeout: 120s  /  Preload: true                 │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │  Flask App (app.py)                      │   │   │
│  │  │  - Rotas CRUD (/novo, /editar, /ver)     │   │   │
│  │  │  - Exportação (/exportar)                │   │   │
│  │  │  - Importação (/importar)                │   │   │
│  │  │  - Autenticação (/login, /callback)      │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │ sqlite3                                 │
│  ┌──────────────▼───────────────────────────────────┐   │
│  │  ropa.db (SQLite — arquivo único)                │   │
│  │  /var/ropa/ropa.db  (ou $ROPA_DB_PATH)           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  LaunchAgent: ropa.app.plist                             │
│  (auto-restart, log: /var/ropa/logs/)                    │
└─────────────────────────────────────────────────────────┘
         │
         │  OIDC (HTTPS)
         ▼
┌─────────────────────┐
│  Keycloak Server    │  Realm: ropa / Client: ropa-web
│  (servidor externo) │  Endpoints: /auth, /token, /userinfo
└─────────────────────┘
```

---

## Diagrama de topologia (Docker)

```
┌─────────────────────────────────────────┐
│  Host (qualquer SO)                     │
│                                         │
│  docker run -p 8000:8000 ropa-comm      │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  Container Python 3.12-slim      │   │
│  │                                  │   │
│  │  CMD: gunicorn app:app           │   │
│  │       --bind 0.0.0.0:8000        │   │
│  │       --workers 2                │   │
│  │                                  │   │
│  │  VOLUME: /app/data/ropa.db       │   │
│  │  EXPOSE: 8000                    │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## Diagrama de topologia (Heroku)

```
Internet
   │
   ▼
┌─────────────────────────────────┐
│  Heroku Platform                │
│                                 │
│  Procfile:                      │
│  web: gunicorn app:app          │
│       --bind 0.0.0.0:$PORT      │
│                                 │
│  Dyno (ephemeral container)     │
│  ⚠ SQLite em dyno = dados       │
│    perdidos a cada restart      │
└─────────────────────────────────┘
```

> **Nota:** Heroku usa sistema de arquivos efêmero. Para produção Heroku, o banco de dados deve ser migrado para PostgreSQL.

---

## Diagrama de topologia (desenvolvimento local)

```
┌─────────────────────────────────────────────────────────┐
│  Máquina do Desenvolvedor                                │
│                                                          │
│  ./start_dev.sh                                          │
│  KEYCLOAK_MOCK=1 python app.py                          │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Flask Dev Server (localhost:5000)             │     │
│  │                                                │     │
│  │  ┌──────────────────────────────────────────┐ │     │
│  │  │  Flask App (app.py)                      │ │     │
│  │  └──────────────────────────────────────────┘ │     │
│  │                                                │     │
│  │  ┌──────────────────────────────────────────┐ │     │
│  │  │  Mock Keycloak (Blueprint Flask)         │ │     │
│  │  │  Rota: /mock-kc/*                        │ │     │
│  │  │  Usuários: encarregado/123, admin/123    │ │     │
│  │  │  Códigos: mock_kc_codes.db (SQLite)      │ │     │
│  │  └──────────────────────────────────────────┘ │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  Banco: ./ropa.db (arquivo local)                        │
└─────────────────────────────────────────────────────────┘
```

---

## Fluxo de requisição HTTP (produção)

```
Browser do Usuário
       │
       │  1. GET /listar  (com cookie de sessão)
       ▼
Cloudflare Tunnel / Proxy
       │
       │  2. Forward para 127.0.0.1:8000
       ▼
Gunicorn Worker (processo Python)
       │
       │  3. Seleciona worker livre
       ▼
Flask App — before_request middleware
       │
       │  4. Verifica session['user'] (Flask session cookie)
       │     Se ausente → redirect para /login
       ▼
Flask Route Handler (/listar)
       │
       │  5. Consulta SQLite (SELECT atividades WHERE ativo=1)
       ▼
Jinja2 Template (templates/listar.html)
       │
       │  6. Renderiza HTML com dados
       ▼
HTTP Response → Browser
```

---

## Portas e endpoints

| Ambiente | Porta | Observação |
|---|---|---|
| Dev (Flask) | 5000 | `python app.py` |
| Prod (Gunicorn) | 8000 | bind 127.0.0.1:8000 |
| Docker | 8000 | mapeável via -p |
| Mock Keycloak | 5000 | `/mock-kc/*` (mesmo processo) |

---

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `FLASK_SECRET_KEY` | — | Chave de assinatura das sessões (obrigatório) |
| `KEYCLOAK_URL` | — | URL base do servidor Keycloak |
| `KEYCLOAK_REALM` | `ropa` | Nome do realm |
| `KEYCLOAK_CLIENT_ID` | `ropa-web` | ID do cliente OIDC |
| `KEYCLOAK_CLIENT_SECRET` | — | Segredo do cliente OIDC |
| `KEYCLOAK_MOCK` | `0` | `1` = ativa mock interno de Keycloak |
| `ROPA_DB_PATH` | `./ropa.db` | Caminho para o banco de dados SQLite |
| `ROPA_DATA_DIR` | `.` | Diretório para exports, logs |
| `ROPA_BASE_URL` | `http://127.0.0.1:8000` | URL base para redirect OAuth |
